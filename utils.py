from datetime import date, datetime

CURRENCIES = ["$", "৳", "€", "£"]
CURRENCY_CODES = {"$": "USD", "৳": "BDT", "€": "EUR", "£": "GBP"}  # used inside charts

_currency = "৳"


def set_currency(symbol):
    global _currency
    _currency = symbol if symbol in CURRENCIES else "৳"


def get_currency():
    return _currency


def currency_code():
    return CURRENCY_CODES.get(_currency, _currency)


def fmt(amount):
    return f"{_currency}{amount:,.2f}"


def parse_amount(text):
    try:
        value = float(str(text).replace(",", "").strip())
    except ValueError:
        raise ValueError("Amount must be a number.")
    if not (0 < value < 1e12):
        raise ValueError("Amount must be greater than zero.")
    return round(value, 2)


def parse_date(text):
    try:
        return datetime.strptime(str(text).strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format (e.g. 2026-11-10).")


def today_str():
    return date.today().isoformat()
