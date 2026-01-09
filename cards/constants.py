PACKAGES = {
    "basic": {
        "label": "Basic",
        "price": 299,
        "card_quantity": 3,
        "edits_included": 2,
        "analytics": "none",
    },
    "pro": {
        "label": "Pro",
        "price": 499,
        "card_quantity": 5,
        "edits_included": 5,
        "analytics": "basic",
    },
    "premium": {
        "label": "Premium",
        "price": 799,
        "card_quantity": 10,
        "edits_included": None,
        "analytics": "advanced",
    },
}

HOSTING_PRICE_YEARLY = 36
HOSTING_INCLUDED_YEARS = 1

PACKAGE_CHOICES = [(key, value["label"]) for key, value in PACKAGES.items()]

CUSTOMER_STATUS_CHOICES = [
    ("active", "Active"),
    ("suspended", "Suspended"),
]

PROFILE_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("live", "Live"),
    ("suspended", "Suspended"),
]

ORDER_STATUS_CHOICES = [
    ("paid", "Paid"),
    ("encoded", "Encoded"),
    ("shipped", "Shipped"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

PAYMENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("success", "Success"),
    ("failed", "Failed"),
    ("refunded", "Refunded"),
]

TEMPLATE_PRESETS = {
    "business": {
        "label": "Business",
        "sections": ["hero", "contact", "bio", "links"],
    },
    "portfolio": {
        "label": "Portfolio",
        "sections": ["hero", "bio", "links"],
    },
    "music": {
        "label": "Music",
        "sections": ["hero", "bio", "links"],
    },
    "restaurant": {
        "label": "Restaurant",
        "sections": ["hero", "bio", "links"],
    },
}

TEMPLATE_CHOICES = [(key, value["label"]) for key, value in TEMPLATE_PRESETS.items()]
