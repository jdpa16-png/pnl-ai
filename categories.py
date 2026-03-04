"""
Define your expense and income categories here,
and the asset accounts/wallets you use.

Customize these lists to match your Google Sheets setup.
"""

# ─── EXPENSE CATEGORIES ───────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    # Housing
    "Rent",
    "Mortgage",
    "Utilities (electricity, water, gas)",
    "Internet and mobile",
    "Home and cleaning",

    # Food
    "Groceries",
    "Restaurants and bars",
    "Delivery (Glovo, Uber Eats)",

    # Transport
    "Public transport",
    "Gas / Fuel",
    "Taxi / Cabify / Uber",
    "Parking",

    # Health
    "Pharmacy",
    "Doctor / Health insurance",
    "Gym",

    # Leisure and culture
    "Leisure and entertainment",
    "Streaming (Netflix, Spotify)",
    "Travel and holidays",
    "Clothing and fashion",

    # Finance
    "Savings / Investment",
    "Insurance",
    "Taxes and fees",
    "Bank charges",

    # Social
    "Gifts",
    "Transfers to people",

    # Other
    "Subscriptions",
    "Education and training",
    "Pets",
    "Uncategorized",
]

# ─── INCOME CATEGORIES ────────────────────────────────────────────────────────
INCOME_CATEGORIES = [
    "Salary / Payroll",
    "Freelance / Invoice",
    "Transfer received",
    "Refund",
    "Insurance reimbursement",
    "Extraordinary income",
]

# ─── ASSET ACCOUNTS ───────────────────────────────────────────────────────────
# These are the "wallets" money moves in and out of in your system
ASSET_ACCOUNTS = [
    "Actual",       # Your main account
    "Revolut",
    "Cash",
    "Savings",
    # Add your accounts here
]

# ─── ALL CATEGORIES ───────────────────────────────────────────────────────────
CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES


# ─── KEYWORD HINTS FOR FAST PRE-CLASSIFICATION ────────────────────────────────
# Helps the AI and reduces API calls for obvious cases.
# Format: "lowercase_text_in_description" -> "Category"
KEYWORD_HINTS = {
    # Supermarkets
    "carrefour": "Groceries",
    "mercadona": "Groceries",
    "lidl": "Groceries",
    "aldi": "Groceries",
    "dia ": "Groceries",
    "eroski": "Groceries",
    "alcampo": "Groceries",
    "hipercor": "Groceries",
    "el corte ingles": "Groceries",

    # Delivery
    "glovo": "Delivery (Glovo, Uber Eats)",
    "uber eats": "Delivery (Glovo, Uber Eats)",
    "just eat": "Delivery (Glovo, Uber Eats)",
    "deliveroo": "Delivery (Glovo, Uber Eats)",

    # Transport
    "cabify": "Taxi / Cabify / Uber",
    "uber": "Taxi / Cabify / Uber",
    "bolt": "Taxi / Cabify / Uber",
    "renfe": "Public transport",
    "metro": "Public transport",
    "emt ": "Public transport",
    "tmc ": "Public transport",

    # Streaming
    "netflix": "Streaming (Netflix, Spotify)",
    "spotify": "Streaming (Netflix, Spotify)",
    "hbo": "Streaming (Netflix, Spotify)",
    "disney": "Streaming (Netflix, Spotify)",
    "amazon prime": "Streaming (Netflix, Spotify)",
    "apple.com/bill": "Subscriptions",

    # Bizum / transfers
    "bizum payment to": "Transfers to people",
    "bizum received from": "Transfer received",

    # Salary
    "nomina": "Salary / Payroll",
    "nómina": "Salary / Payroll",
    "salario": "Salary / Payroll",

    # Pharmacy
    "farmacia": "Pharmacy",
    "pharmacy": "Pharmacy",

    # Gas / Fuel
    "repsol": "Gas / Fuel",
    "bp ": "Gas / Fuel",
    "cepsa": "Gas / Fuel",
    "galp": "Gas / Fuel",
}
