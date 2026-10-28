from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
ORDERS_FILE = BASE_DIR / "orders.json"

# Edit the menu/prices here. Prices are in INR.
MENU = {
    "espresso": {"price": 80, "aliases": ["espresso", "espressos"]},
    "cappuccino": {"price": 120, "aliases": ["cappuccino", "cappuccinos", "capuccino"]},
    "cold coffee": {"price": 140, "aliases": ["cold coffee", "cold coffees", "iced coffee"]},
    "masala tea": {"price": 40, "aliases": ["masala tea", "tea", "chai", "masala chai"]},
    "hot chocolate": {"price": 130, "aliases": ["hot chocolate", "hot cocoa"]},
    "veg sandwich": {"price": 100, "aliases": ["veg sandwich", "vegetable sandwich", "sandwich", "sandwiches"]},
    "grilled sandwich": {"price": 150, "aliases": ["grilled sandwich", "grilled sandwiches"]},
    "veg burger": {"price": 120, "aliases": ["veg burger", "vegetarian burger", "burger", "burgers"]},
    "french fries": {"price": 90, "aliases": ["french fries", "fries"]},
    "brownie": {"price": 100, "aliases": ["brownie", "brownies", "chocolate brownie"]},
}

# Example coupon codes. Set discount to 0 to disable a coupon.
COUPONS = {"CAFE10": 0.10, "WELCOME5": 0.05}
TAX_RATE = 0.05
MAX_ITEM_QUANTITY = 50

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
YES = {"yes", "y", "yeah", "yep", "haan", "ha", "ji"}
NO = {"no", "n", "nope", "nahi", "nah"}
cart: dict[str, int] = {}
active_coupon: Optional[str] = None
order_type: Optional[str] = None
customer_name: Optional[str] = None


def money(amount: float) -> str:
    return f"₹{amount:,.2f}"


def load_orders() -> list[dict]:
    if not ORDERS_FILE.exists():
        return []
    try:
        data = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        print("Note: order history could not be read; starting with an empty history.")
        return []


def save_order(order: dict) -> None:
    orders = load_orders()
    orders.append(order)
    ORDERS_FILE.write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding="utf-8")


def show_menu(query: str = "") -> None:
    print("\n" + "=" * 58)
    print("                         CAFE AI MENU")
    print("=" * 58)
    print(f"{'ITEM':<28}{'PRICE':>12}  {'AVAILABILITY':>16}")
    print("-" * 58)
    q = query.casefold().strip()
    shown = 0
    for name, item in MENU.items():
        if q and q not in name.casefold() and not any(q in a.casefold() for a in item["aliases"]):
            continue
        print(f"{name.title():<28}{money(item['price']):>12}  {'Available':>16}")
        shown += 1
    if not shown:
        print("No menu items matched that search.")
    print("=" * 58)
    print("Tip: '2 cappuccinos', 'add fries', 'search coffee', or 'help'.")


def find_item_matches(text: str) -> list[dict]:
    aliases = []
    for canonical, item in MENU.items():
        for alias in item["aliases"]:
            aliases.append((alias.casefold(), canonical))
    aliases.sort(key=lambda pair: len(pair[0]), reverse=True)

    found = []
    occupied: list[tuple[int, int]] = []
    lowered = text.casefold()
    for alias, canonical in aliases:
        pattern = re.compile(r"(?<!\w)" + re.escape(alias) + r"(?!\w)")
        for match in pattern.finditer(lowered):
            start, end = match.span()
            if any(start < old_end and end > old_start for old_start, old_end in occupied):
                continue
            found.append({"name": canonical, "start": start, "end": end})
            occupied.append((start, end))
    return sorted(found, key=lambda item: item["start"])


def quantity_for_match(text: str, match: dict) -> int:
    before = text[:match["start"]].casefold().rstrip()
    after = text[match["end"]:].casefold().lstrip()
    words = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
    number = rf"(?:\d+|{words})"

    # Quantity immediately before the item: "2 cappuccinos", "two cappuccinos".
    m = re.search(rf"(?<!\w)({number})\s*$", before)
    if m:
        token = m.group(1)
        return int(token) if token.isdigit() else NUMBER_WORDS[token]

    # Quantity immediately after item: "cappuccino x 2", "fries 2".
    m = re.match(rf"^(?:x\s*)?({number})(?!\w)", after)
    if m:
        token = m.group(1)
        return int(token) if token.isdigit() else NUMBER_WORDS[token]
    return 1


def extract_requested_items(text: str) -> list[tuple[str, int]]:
    matches = find_item_matches(text)
    return [(m["name"], quantity_for_match(text, m)) for m in matches]


def subtotal() -> float:
    return sum(MENU[name]["price"] * qty for name, qty in cart.items())


def totals() -> dict[str, float]:
    sub = subtotal()
    discount_rate = COUPONS.get(active_coupon or "", 0)
    discount = round(sub * discount_rate, 2)
    taxable = max(0.0, sub - discount)
    tax = round(taxable * TAX_RATE, 2)
    return {"subtotal": sub, "discount": discount, "tax": tax, "total": round(taxable + tax, 2)}


def show_cart() -> None:
    print("\n" + "=" * 58)
    print("                         YOUR CART")
    print("=" * 58)
    if not cart:
        print("Your cart is empty. Try 'add a cappuccino'.")
        print("=" * 58)
        return
    print(f"{'ITEM':<26}{'QTY':>6}{'PRICE':>12}{'TOTAL':>14}")
    print("-" * 58)
    for name, qty in cart.items():
        price = MENU[name]["price"]
        print(f"{name.title():<26}{qty:>6}{money(price):>12}{money(price * qty):>14}")
    t = totals()
    print("-" * 58)
    print(f"{'Subtotal':>43} {money(t['subtotal']):>14}")
    if t["discount"]:
        print(f"{('Coupon ' + str(active_coupon)):>43} -{money(t['discount']):>13}")
    print(f"{'Tax (5%)':>43} {money(t['tax']):>14}")
    print(f"{'GRAND TOTAL':>43} {money(t['total']):>14}")
    if order_type:
        print(f"Order type: {order_type.title()}")
    print("=" * 58)


def add_items(text: str) -> None:
    requested = extract_requested_items(text)
    if not requested:
        print("Cafe AI: I couldn't identify a menu item. Try 'menu' to see options.")
        return
    for name, qty in requested:
        if qty < 1 or qty > MAX_ITEM_QUANTITY:
            print(f"Cafe AI: Quantity for {name.title()} must be between 1 and {MAX_ITEM_QUANTITY}; skipped.")
            continue
        cart[name] = cart.get(name, 0) + qty
        print(f"Cafe AI: Added {qty} × {name.title()}.")
    show_cart()


def remove_items(text: str) -> None:
    requested = extract_requested_items(text)
    if not requested:
        print("Cafe AI: Which item should I remove? Example: 'remove 1 brownie'.")
        return
    for name, qty in requested:
        if name not in cart:
            print(f"Cafe AI: {name.title()} isn't in your cart.")
        elif qty >= cart[name]:
            del cart[name]
            print(f"Cafe AI: Removed {name.title()} from your cart.")
        else:
            cart[name] -= qty
            print(f"Cafe AI: Removed {qty} × {name.title()}.")
    show_cart()


def set_quantity(text: str) -> None:
    matches = extract_requested_items(text)
    if not matches:
        print("Cafe AI: Tell me the item and quantity, e.g. 'set cappuccino to 3'.")
        return
    for name, qty in matches:
        if qty < 1 or qty > MAX_ITEM_QUANTITY:
            print(f"Cafe AI: Quantity must be between 1 and {MAX_ITEM_QUANTITY}.")
        else:
            cart[name] = qty
            print(f"Cafe AI: Set {name.title()} quantity to {qty}.")
    show_cart()


def apply_coupon(text: str) -> None:
    global active_coupon
    code_match = re.search(r"\b([A-Za-z0-9_-]+)\b", re.sub(r"(?i)\b(apply|coupon|code|use)\b", " ", text))
    code = code_match.group(1).upper() if code_match else ""
    if code in COUPONS:
        active_coupon = code
        print(f"Cafe AI: Coupon {code} applied ({COUPONS[code] * 100:.0f}% off).")
        show_cart()
    else:
        print("Cafe AI: That coupon isn't valid. Try CAFE10 or WELCOME5.")


def choose_order_type() -> Optional[str]:
    print("\nChoose order type: dine-in / takeaway / delivery")
    while True:
        choice = input("You: ").strip().casefold()
        if choice in {"dine-in", "dine in", "dinein", "1"}:
            return "dine-in"
        if choice in {"takeaway", "take away", "pickup", "pick-up", "2"}:
            return "takeaway"
        if choice in {"delivery", "deliver", "3"}:
            return "delivery"
        if choice in {"cancel", "back"}:
            return None
        print("Please enter dine-in, takeaway, delivery, or cancel.")


def checkout() -> None:
    global active_coupon, order_type, customer_name
    if not cart:
        print("Cafe AI: Your cart is empty. Add an item before checkout.")
        return
    show_cart()
    answer = input("Place this order? (yes/no): ").strip().casefold()
    if answer not in YES:
        print("Cafe AI: Checkout cancelled; your cart is unchanged.")
        return

    selected_type = choose_order_type()
    if not selected_type:
        print("Cafe AI: Checkout cancelled; your cart is unchanged.")
        return
    name = input("Your name: ").strip()
    if not name:
        print("Cafe AI: Please enter a name so the order can be labelled.")
        return

    t = totals()
    order_id = "CAFE-" + uuid.uuid4().hex[:8].upper()
    order = {
        "order_id": order_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "customer": name,
        "order_type": selected_type,
        "items": [{"name": n, "quantity": q, "unit_price": MENU[n]["price"],
                   "line_total": MENU[n]["price"] * q} for n, q in cart.items()],
        "coupon": active_coupon,
        **t,
        "status": "placed",
    }
    try:
        save_order(order)
    except OSError as exc:
        print(f"Cafe AI: Could not save the order ({exc}). No order was confirmed.")
        return

    print("\n" + "*" * 58)
    print("                    ORDER PLACED SUCCESSFULLY")
    print("*" * 58)
    print(f"Order ID   : {order_id}")
    print(f"Customer   : {name}")
    print(f"Order type : {selected_type.title()}")
    print(f"Time       : {order['created_at']}")
    for item in order["items"]:
        print(f"  {item['name'].title()} × {item['quantity']}  {money(item['line_total'])}")
    print("-" * 58)
    print(f"Subtotal   : {money(t['subtotal'])}")
    if t["discount"]:
        print(f"Discount   : -{money(t['discount'])} ({active_coupon})")
    print(f"Tax        : {money(t['tax'])}")
    print(f"TOTAL      : {money(t['total'])}")
    print("Thank you for choosing Cafe AI!")
    print("*" * 58)
    cart.clear()
    active_coupon = None
    order_type = selected_type
    customer_name = name


def show_order_history() -> None:
    orders = load_orders()
    if not orders:
        print("Cafe AI: No saved orders yet.")
        return
    print("\nRECENT ORDERS")
    for order in orders[-10:][::-1]:
        print(f"{order.get('order_id', 'Unknown')} | {order.get('customer', 'Guest')} | "
              f"{order.get('order_type', '-')} | {money(float(order.get('total', 0)))} | "
              f"{order.get('status', 'placed')} | {order.get('created_at', '')}")


def show_help() -> None:
    print("""
CAFE AI — COMMAND GUIDE
  menu / show menu                 Show all menu items
  search coffee                    Search the menu
  add 2 cappuccinos and a brownie  Add items (you can also just type item names)
  cart / bill                      View cart and totals
  remove 1 brownie                 Remove a quantity or an entire item
  set cappuccino to 3              Set an item's exact cart quantity
  coupon CAFE10                    Apply a coupon (CAFE10 or WELCOME5)
  checkout                         Confirm and save an order
  history                          Show recent saved orders
  clear cart                       Empty the cart after confirmation
  help                             Show this guide
  quit                             Exit
Tax is currently configured at 5% in cafe_ai.py. Update TAX_RATE to change it.
""".strip())


def try_existing_intent_model(text: str) -> Optional[tuple[str, float, list[str]]]:
    """Load the user's existing model if its files exist; fail safely otherwise."""
    try:
        import torch
        from model import NeuralNet
        from nltk_utils import bag_of_words, tokenize
        intents_path = BASE_DIR / "intents.json"
        data_path = BASE_DIR / "data.pth"
        if not intents_path.exists() or not data_path.exists():
            return None
        intents = json.loads(intents_path.read_text(encoding="utf-8"))["intents"]
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            data = torch.load(data_path, map_location=device, weights_only=False)
        except TypeError:
            data = torch.load(data_path, map_location=device)
        model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"]).to(device)
        model.load_state_dict(data["model_state"])
        model.eval()
        vector = bag_of_words(tokenize(text), data["all_words"])
        x = torch.from_numpy(vector).float().reshape(1, -1).to(device)
        with torch.no_grad():
            probs = torch.softmax(model(x), dim=1)
            confidence, predicted = torch.max(probs, dim=1)
        tag = data["tags"][predicted.item()]
        response_map = {i["tag"]: i.get("responses", []) for i in intents}
        return tag, float(confidence.item()), response_map.get(tag, [])
    except Exception:
        return None


def clear_cart() -> None:
    global active_coupon
    if not cart:
        print("Cafe AI: Your cart is already empty.")
        return
    answer = input("Clear the entire cart? (yes/no): ").strip().casefold()
    if answer in YES:
        cart.clear()
        active_coupon = None
        print("Cafe AI: Cart cleared.")
    else:
        print("Cafe AI: Cart kept unchanged.")


def handle_message(raw: str) -> bool:
    global order_type
    text = raw.strip()
    low = text.casefold().strip()
    if not text:
        return True
    if low in {"quit", "exit", "bye", "goodbye"}:
        print("Cafe AI: Thanks for visiting. Have a great day!")
        return False
    if low in {"help", "commands"}:
        show_help(); return True
    if low in {"menu", "show menu", "show me the menu", "view menu", "menu please"}:
        show_menu(); return True
    if low.startswith(("search ", "find ")):
        show_menu(re.sub(r"^(search|find)\s+", "", text, flags=re.I)); return True
    if low in {"cart", "show cart", "view cart", "my bill", "my total", "bill"}:
        show_cart(); return True
    if low in {"history", "order history", "recent orders"}:
        show_order_history(); return True
    if low in {"checkout", "place order", "confirm order", "proceed to checkout"}:
        checkout(); return True
    if low in {"clear cart", "cancel cart", "cancel my order"}:
        clear_cart(); return True
    if re.search(r"\b(set|update|change)\b", low) and re.search(r"\b(to|quantity)\b", low):
        set_quantity(text); return True
    if re.search(r"\b(remove|delete|take out)\b", low):
        remove_items(text); return True
    if re.search(r"\b(coupon|promo|discount)\b", low):
        apply_coupon(text); return True
    if low in {"dine-in", "dine in", "takeaway", "take away", "delivery"}:
        order_type = low
        print(f"Cafe AI: Preferred order type set to {order_type}.")
        return True

    requested = extract_requested_items(text)
    if requested:
        add_items(text)
        return True

    result = try_existing_intent_model(text)
    if result:
        tag, confidence, responses = result
        if confidence >= 0.75 and responses:
            print("Cafe AI:", responses[0])
            return True

    if any(word in low for word in ["hello", "hi", "hey", "namaste", "namaskar"]):
        print("Cafe AI: Hello! Welcome to Cafe AI. You can say 'show menu' or tell me what you'd like.")
    elif any(word in low for word in ["thank", "thanks", "shukriya", "dhanyawad"]):
        print("Cafe AI: You're welcome! Let me know if you'd like anything else.")
    elif any(word in low for word in ["recommend", "suggest", "best", "kya lu", "kya loon"]):
        print("Cafe AI: Popular picks are cappuccino, cold coffee, veg sandwich and brownie.")
    elif any(word in low for word in ["price", "cost", "kitne", "rate"]):
        print("Cafe AI: You can check prices with 'menu' or search for an item, e.g. 'search coffee'.")
    else:
        print("Cafe AI: I didn't quite understand. Try 'help', 'menu', 'add 2 cappuccinos', or 'checkout'.")
    return True


def main() -> None:
    print("\n☕ Welcome to Cafe AI!")
    print("Order in simple English or Hinglish. Type 'help' for commands and 'quit' to exit.")
    show_menu()
    running = True
    while running:
        try:
            message = input("\nYou: ")
            running = handle_message(message)
        except (KeyboardInterrupt, EOFError):
            print("\nCafe AI: Session ended. Thanks for visiting!")
            break


if __name__ == "__main__":
    main()
