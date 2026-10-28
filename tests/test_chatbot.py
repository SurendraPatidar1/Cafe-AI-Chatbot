
import pytest
import chat as chatbot


@pytest.fixture(autouse=True)
def reset_chatbot_state():
    """Reset shared chatbot state before and after each test."""
    chatbot.cart.clear()
    chatbot.active_coupon = None
    chatbot.order_type = None

    yield

    chatbot.cart.clear()
    chatbot.active_coupon = None
    chatbot.order_type = None


# -------------------------
# MENU TESTS
# -------------------------

def test_menu_is_not_empty():
    assert chatbot.MENU


def test_menu_prices_are_positive():
    assert all(
        isinstance(item["price"], (int, float))
        and item["price"] > 0
        for item in chatbot.MENU.values()
    )


def test_known_menu_prices():
    assert chatbot.MENU["espresso"]["price"] == 80
    assert chatbot.MENU["cappuccino"]["price"] == 120
    assert chatbot.MENU["brownie"]["price"] == 100


def test_show_menu(capsys):
    chatbot.show_menu()
    output = capsys.readouterr().out

    assert "CAFE AI MENU" in output
    assert "espresso".title() in output


def test_menu_search(capsys):
    chatbot.show_menu("cappuccino")
    output = capsys.readouterr().out.lower()

    assert "cappuccino" in output
    assert "espresso" not in output


# -------------------------
# ITEM MATCHING TESTS
# -------------------------

def test_find_item_matches_for_known_item():
    matches = chatbot.find_item_matches("cappuccino")

    assert matches
    assert matches[0]["name"] == "cappuccino"


def test_find_item_matches_for_unknown_text():
    matches = chatbot.find_item_matches("zzqv blargh xyz")

    assert matches == []


# -------------------------
# QUANTITY PARSING TESTS
# -------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("2 cappuccinos", [("cappuccino", 2)]),
        ("3 brownies", [("brownie", 3)]),
        ("two cappuccinos", [("cappuccino", 2)]),
        ("cappuccino x 2", [("cappuccino", 2)]),
        ("cappuccino", [("cappuccino", 1)]),
    ],
)
def test_extract_requested_items(text, expected):
    assert chatbot.extract_requested_items(text) == expected


def test_extract_multiple_items():
    result = chatbot.extract_requested_items(
        "2 cappuccinos and 3 brownies"
    )

    assert ("cappuccino", 2) in result
    assert ("brownie", 3) in result


def test_quantity_for_match():
    text = "3 brownies"
    match = chatbot.find_item_matches(text)[0]

    assert chatbot.quantity_for_match(text, match) == 3


# -------------------------
# CART AND BILL TESTS
# -------------------------

def test_empty_cart_subtotal_is_zero():
    assert chatbot.subtotal() == 0


def test_empty_cart_total_is_zero():
    assert chatbot.totals()["total"] == 0


def test_add_items_to_cart():
    chatbot.add_items("2 cappuccinos")

    assert chatbot.cart["cappuccino"] == 2


def test_add_same_item_twice():
    chatbot.add_items("2 cappuccinos")
    chatbot.add_items("1 cappuccino")

    assert chatbot.cart["cappuccino"] == 3


def test_add_unknown_item_does_not_change_cart():
    chatbot.add_items("zzqv blargh xyz")

    assert chatbot.cart == {}


def test_subtotal_for_multiple_items():
    chatbot.cart["espresso"] = 2
    chatbot.cart["brownie"] = 1

    assert chatbot.subtotal() == 260


def test_totals_include_tax():
    chatbot.cart["espresso"] = 1

    result = chatbot.totals()

    assert result["subtotal"] == 80
    assert result["discount"] == 0
    assert result["tax"] == pytest.approx(
        80 * chatbot.TAX_RATE
    )
    assert result["total"] == pytest.approx(
        80 * (1 + chatbot.TAX_RATE)
    )


# -------------------------
# REMOVE AND UPDATE TESTS
# -------------------------

def test_remove_part_of_cart_quantity():
    chatbot.cart["cappuccino"] = 3

    chatbot.remove_items("remove 1 cappuccino")

    assert chatbot.cart["cappuccino"] == 2


def test_remove_all_of_an_item():
    chatbot.cart["brownie"] = 2

    chatbot.remove_items("remove 2 brownies")

    assert "brownie" not in chatbot.cart


def test_set_item_quantity():
    chatbot.set_quantity("set 3 cappuccino")

    assert chatbot.cart["cappuccino"] == 3


def test_reject_quantity_above_limit():
    chatbot.add_items(
        f"{chatbot.MAX_ITEM_QUANTITY + 1} cappuccinos"
    )

    assert chatbot.cart == {}


# -------------------------
# COUPON TESTS
# -------------------------

def test_valid_coupon_changes_discount():
    if not chatbot.COUPONS:
        pytest.skip("No coupons are configured.")

    coupon = next(iter(chatbot.COUPONS))

    chatbot.cart["espresso"] = 2
    chatbot.apply_coupon(f"coupon {coupon}")

    assert chatbot.active_coupon == coupon
    assert chatbot.totals()["discount"] == pytest.approx(
        160 * chatbot.COUPONS[coupon]
    )


def test_invalid_coupon_does_not_apply():
    chatbot.cart["espresso"] = 1

    chatbot.apply_coupon("coupon INVALID_CODE")

    assert chatbot.active_coupon is None
    assert chatbot.totals()["discount"] == 0


# -------------------------
# CLEAR CART TESTS
# -------------------------

def test_clear_cart_when_confirmed(monkeypatch):
    chatbot.cart["espresso"] = 2
    chatbot.active_coupon = "CAFE10"

    monkeypatch.setattr("builtins.input", lambda _: "yes")

    chatbot.clear_cart()

    assert chatbot.cart == {}
    assert chatbot.active_coupon is None


def test_clear_cart_when_cancelled(monkeypatch):
    chatbot.cart["espresso"] = 2

    monkeypatch.setattr("builtins.input", lambda _: "no")

    chatbot.clear_cart()

    assert chatbot.cart == {"espresso": 2}


# -------------------------
# CHATBOT MESSAGE TESTS
# -------------------------

def test_quit_returns_false():
    assert chatbot.handle_message("quit") is False


def test_exit_returns_false():
    assert chatbot.handle_message("exit") is False


def test_empty_message_keeps_chat_running():
    assert chatbot.handle_message("") is True


def test_greeting_response(capsys):
    result = chatbot.handle_message("namaste")
    output = capsys.readouterr().out.lower()

    assert result is True
    assert "hello" in output


def test_delivery_order_type(capsys):
    chatbot.handle_message("delivery")

    assert chatbot.order_type == "delivery"


def test_menu_command(capsys):
    result = chatbot.handle_message("menu")
    output = capsys.readouterr().out

    assert result is True
    assert "CAFE AI MENU" in output
