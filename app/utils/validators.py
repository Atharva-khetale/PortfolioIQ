import re

TICKER_PATTERN = re.compile(r"^[A-Z0-9\.\-\^]{1,15}$")


def is_valid_ticker(ticker: str) -> bool:
    return bool(TICKER_PATTERN.match(ticker.strip().upper()))


def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+\.[^\s]+$", url.strip()))


def is_valid_quantity(qty) -> bool:
    try:
        return float(qty) > 0
    except (TypeError, ValueError):
        return False


def is_valid_price(price) -> bool:
    try:
        return float(price) >= 0
    except (TypeError, ValueError):
        return False
