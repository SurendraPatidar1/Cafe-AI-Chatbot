
import json
import random
import re
import uuid
import torch

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


# -------------------- MODEL SETUP --------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

with open("intents.json", "r", encoding="utf-8") as file:
    intents = json.load(file)["intents"]

try:
    data = torch.load(
        "data.pth",
        map_location=device,
        weights_only=False
    )
except TypeError:
    data = torch.load("data.pth", map_location=device)

all_words = data["all_words"]
tags = data["tags"]

model = NeuralNet(
    data["input_size"],
    data["hidden_size"],
    data["output_size"]
).to(device)

model.load_state_dict(data["model_state"])
model.eval()

intent_responses = {item["tag"]: item["responses"] for item in intents}


# -------------------- CAFE MENU --------------------

MENU = {
    "espresso": {
        "price": 80,
        "aliases": ["espresso"]
    },
    "cappuccino": {
        "price": 120,
        "aliases": ["cappuccino", "cappuccinos"]
    },
    "cold coffee": {
        "price": 140,
        "aliases": ["cold coffee", "cold coffees"]
    },
    "masala tea": {
        "price": 40,
        "aliases": ["masala tea", "tea"]
    },
    "hot chocolate": {
        "price": 130,
        "aliases": ["hot chocolate"]
    },
    "veg sandwich": {
        "price": 100,
        "aliases": ["veg sandwich", "sandwich", "sandwiches"]
    },
    "grilled sandwich": {
        "price": 150,
        "aliases": ["grilled sandwich"]
    },
    "veg burger": {
        "price": 120,
        "aliases": ["veg burger", "burger", "burgers"]
    },
    "french fries": {
        "price": 90,
        "aliases": ["french fries", "fries"]
    },
    "brownie": {
        "price": 100,
        "aliases": ["chocolate brownie", "brownie", "brownies"]
    }
}

cart = {}

NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5
}


# -------------------- INTENT CLASSIFICATION --------------------

def predict_intent(sentence):
    tokens = tokenize(sentence)
    vector = bag_of_words(tokens, all_words)

    X = torch.from_numpy(vector).float().reshape(1, -1).to(device)

    with torch.no_grad():
        output = model(X)
        probabilities = torch.softmax(output, dim=1)
        confidence, predicted = torch.max(probabilities, dim=1)

    return tags[predicted.item()], confidence.item()


# -------------------- MENU AND CART --------------------

def show_menu():
    print("\n" + "=" * 45)
    print("             WELCOME TO CAFE AI")
    print("=" * 45)
    print(f"{'No.':<5}{'Item':<27}{'Price':>10}")
    print("-" * 45)

    for number, (name, item) in enumerate(MENU.items(), start=1):
        print(f"{number:<5}{name.title():<27}Rs. {item['price']:>4}")

    print("=" * 45)
    print("Enter an item number or type its name.")


def get_total():
    return sum(
        MENU[name]["price"] * quantity
        for name, quantity in cart.items()
    )


def show_cart():
    print("\n" + "=" * 40)
    print("                YOUR CART")
    print("=" * 40)

    if not cart:
        print("Your cart is empty.")
        print("=" * 40)
        return

    for name, quantity in cart.items():
        price = MENU[name]["price"]
        subtotal = price * quantity
        print(
            f"{name.title()} x {quantity} = Rs. {subtotal}"
        )

    print("-" * 40)
    print(f"TOTAL: Rs. {get_total()}")
    print("=" * 40)


# -------------------- ITEM AND QUANTITY EXTRACTION --------------------

def find_item_matches(text):
    """Find menu items and their positions in the user's message."""
    aliases = []

    for name, item in MENU.items():
        for alias in item["aliases"]:
            aliases.append((alias, name))

    # Match longer names first to avoid overlapping matches.
    aliases.sort(key=lambda entry: len(entry[0]), reverse=True)

    matches = []
    occupied = []

    for alias, name in aliases:
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"

        for match in re.finditer(pattern, text):
            start, end = match.span()

            if any(start < old_end and end > old_start
                   for old_start, old_end in occupied):
                continue

            matches.append({
                "name": name,
                "start": start,
                "end": end
            })
            occupied.append((start, end))

    return sorted(matches, key=lambda item: item["start"])


def extract_quantity(text, item_match):
    """Read quantity immediately before or after an item name."""
    before = text[:item_match["start"]].strip()
    after = text[item_match["end"]:].strip()

    number_pattern = r"(?:\d+|one|two|three|four|five|a|an)"

    before_match = re.search(
        r"(?<!\w)(" + number_pattern + r")\s*$",
        before
    )

    if before_match:
        value = before_match.group(1)
        quantity = (
            int(value) if value.isdigit()
            else NUMBER_WORDS[value]
        )
        return quantity

    after_match = re.match(
        r"^(?:x\s*)?(\d+|one|two|three|four|five)\b",
        after
    )

    if after_match:
        value = after_match.group(1)
        return int(value) if value.isdigit() else NUMBER_WORDS[value]

    return 1


def add_items(text):
    matches = find_item_matches(text)

    if not matches:
        print("Bot: I couldn't identify an item. Please check the menu.")
        show_menu()
        return

    # First validate all quantities before changing the cart.
    requested = []

    for match in matches:
        quantity = extract_quantity(text, match)

        if not 1 <= quantity <= 50:
            print("Bot: Quantity must be between 1 and 50 per item.")
            return

        requested.append((match["name"], quantity))

    for name, quantity in requested:
        cart[name] = cart.get(name, 0) + quantity
        print(f"Bot: Added {quantity} x {name.title()}.")

    show_cart()


def remove_item(text):
    matches = find_item_matches(text)

    if not matches:
        print("Bot: Which item would you like to remove?")
        return

    for match in matches:
        name = match["name"]

        if name not in cart:
            print(f"Bot: {name.title()} is not in your cart.")
            continue

        quantity = extract_quantity(text, match)

        if quantity >= cart[name]:
            del cart[name]
            print(f"Bot: Removed {name.title()} from your cart.")
        else:
            cart[name] -= quantity
            print(f"Bot: Removed {quantity} x {name.title()}.")

    show_cart()


# -------------------- CHECKOUT --------------------

def checkout():
    if not cart:
        print("Bot: Your cart is empty. Please order something first.")
        return

    show_cart()

    answer = input(
        "Bot: Confirm your order? (yes/no): "
    ).strip().lower()

    if answer not in ("yes", "y"):
        print("Bot: Checkout cancelled. Your cart is unchanged.")
        return

    customer = input("Bot: Enter your name: ").strip()

    if not customer:
        customer = "Cafe Customer"

    order_id = "CAFE-" + uuid.uuid4().hex[:8].upper()
    total = get_total()

    print("\n" + "*" * 42)
    print("               ORDER PLACED!")
    print("*" * 42)
    print(f"Order ID : {order_id}")
    print(f"Customer : {customer}")
    print("-" * 42)

    for name, quantity in cart.items():
        subtotal = MENU[name]["price"] * quantity
        print(f"{name.title()} x {quantity} = Rs. {subtotal}")

    print("-" * 42)
    print(f"TOTAL AMOUNT: Rs. {total}")
    print("Thank you for visiting Cafe AI!")
    print("*" * 42)

    cart.clear()


# -------------------- CHATBOT ACTIONS --------------------

def handle_intent(tag, text):
    if tag == "greeting":
        print("Bot:", random.choice(
            intent_responses.get(
                tag,
                ["Welcome to Cafe AI!"]
            )
        ))

    elif tag == "show_menu":
        show_menu()

    elif tag == "add_to_cart":
        add_items(text)

    elif tag == "view_cart":
        show_cart()

    elif tag == "remove_from_cart":
        remove_item(text)

    elif tag == "checkout":
        checkout()

    elif tag == "cancel_order":
        if not cart:
            print("Bot: Your cart is already empty.")
            return

        answer = input(
            "Bot: Clear your entire cart? (yes/no): "
        ).strip().lower()

        if answer in ("yes", "y"):
            cart.clear()
            print("Bot: Your cart has been cleared.")
        else:
            print("Bot: Your cart has been kept.")

    elif tag in ("thanks", "goodbye"):
        print("Bot:", random.choice(
            intent_responses.get(tag, ["Thanks for visiting Cafe AI!"])
        ))

    else:
        print("Bot: Sorry, I didn't understand. Try 'menu' or an item name.")


def main():
    print("\nBot: Hello! Welcome to Cafe AI.")
    print("Bot: Type 'quit' to exit.")
    show_menu()

    while True:
        text = input("\nYou: ").strip()
        lower_text = text.lower()

        if not text:
            continue

        if lower_text in ("quit", "exit"):
            print("Bot: Thanks for visiting Cafe AI!")
            break

        # Explicit commands take priority over model predictions.
        if lower_text in ("menu", "show menu", "show me the menu",
                          "menu please", "view menu"):
            show_menu()
            continue

        if lower_text in ("cart", "show cart", "view cart",
                          "show my cart", "my bill", "my total"):
            show_cart()
            continue

        if lower_text in ("checkout", "place order", "confirm order",
                          "place my order", "proceed to checkout"):
            checkout()
            continue

        if lower_text in ("cancel", "cancel cart", "clear cart",
                          "cancel my order"):
            handle_intent("cancel_order", lower_text)
            continue

        # Number selection: 1 = Espresso, 2 = Cappuccino, etc.
        if lower_text.isdigit():
            number = int(lower_text)
            names = list(MENU.keys())

            if 1 <= number <= len(names):
                add_items(names[number - 1])
            else:
                print("Bot: Invalid menu number. Type 'menu'.")
            continue

        # Detect explicit removal requests before adding items.
        if re.search(r"\b(remove|delete|take out)\b", lower_text):
            remove_item(lower_text)
            continue

        # Menu item names are handled directly, even if the
        # neural network predicts the wrong intent.
        if find_item_matches(lower_text):
            add_items(lower_text)
            continue

        # Use the trained model for other natural-language requests.
        tag, confidence = predict_intent(text)

        print(f"[Intent: {tag} | Confidence: {confidence:.2f}]")

        if confidence < 0.75:
            print(
                "Bot: Sorry, I didn't understand. "
                "Try 'show menu', an item name, or 'checkout'."
            )
            continue

        handle_intent(tag, lower_text)


if __name__ == "__main__":
    main()
