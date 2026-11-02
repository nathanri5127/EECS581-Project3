import re

# Ordered: the first category whose keyword matches wins.
# Put more specific categories above general ones.
CATEGORY_RULES = [
    ("Rent", [
        "rent", "apartment", "apartments", "property management",
        "landlord", "leasing"
    ]),
    ("Utilities", [
        "evergy", "electric", "water", "gas service", "kansas gas",
        "sewer", "trash", "waste management", "internet", "comcast",
        "xfinity", "spectrum", "at&t", "verizon", "t-mobile", "wireless"
    ]),
    ("Subscriptions", [
        "netflix", "spotify", "hulu", "disney+", "youtube premium",
        "apple.com/bill", "amazon prime", "hbo", "max.com", "paramount",
        "adobe", "chatgpt", "patreon"
    ]),
    ("Groceries", [
        "grocery", "dillons", "hy-vee", "hyvee", "aldi", "walmart",
        "target", "costco", "sam's club", "trader joe", "whole foods",
        "kroger", "price chopper"
    ]),
    ("Gas", [
        "quiktrip", "qt ", "shell", "exxon", "mobil", "chevron", "bp ",
        "phillips 66", "casey's", "caseys", "conoco", "sinclair", "fuel"
    ]),
    ("Dining", [
        "restaurant", "chipotle", "starbucks", "taco bell", "mcdonald",
        "jimmy john", "subway", "wendy", "chick-fil-a", "panera",
        "domino", "pizza", "doordash", "grubhub", "uber eats",
        "coffee", "cafe", "burger"
    ]),
    ("Transportation", [
        "uber", "lyft", "parking", "bus", "transit", "toll",
        "auto repair", "oil change", "car wash"
    ]),
    ("Shopping", [
        "amazon", "ebay", "best buy", "etsy", "kohl", "old navy",
        "nike", "marketplace"
    ]),
    ("Health", [
        "pharmacy", "cvs", "walgreens", "clinic", "hospital",
        "dental", "doctor", "medical"
    ]),
    ("Transfers", [
        "venmo", "zelle", "paypal", "cash app", "transfer"
    ]),
]

INCOME_KEYWORDS = [
    "payroll", "direct deposit", "salary", "paycheck", "deposit"
]


def _matches(text, keyword):
    # Word-boundary match so "gas" doesn't match "vegas".
    # Allows a trailing "s" or "'s" so "jimmy john" matches "Jimmy Johns".
    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(keyword.strip())
        + r"(?:'?s)?(?![a-z0-9])"
    )
    return re.search(pattern, text) is not None


def auto_categorize(description, amount):
    text = str(description).lower()

    if amount > 0:
        for keyword in INCOME_KEYWORDS:
            if _matches(text, keyword):
                return "Income"

    for category, keywords in CATEGORY_RULES:
        for keyword in keywords:
            if _matches(text, keyword):
                return category

    # Unmatched money coming in is still income.
    if amount > 0:
        return "Income"

    return "Uncategorized"
