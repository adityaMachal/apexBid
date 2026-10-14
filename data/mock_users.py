"""
data/mock_users.py
Contains 10 realistic mock users with varied wallet balances.
"""


def get_mock_users():
    """Returns a list of 10 user documents ready for insert_many()."""

    return [
        {"name": "Alice Johnson",    "email": "alice@example.com",   "mobile": "9876543210", "balance": 2500.00},
        {"name": "Bob Smith",        "email": "bob@example.com",     "mobile": "9123456780", "balance": 1800.00},
        {"name": "Charlie Brown",    "email": "charlie@example.com", "mobile": "9988776655", "balance": 450.00},
        {"name": "Diana Prince",     "email": "diana@example.com",   "mobile": "9811223344", "balance": 5200.00},
        {"name": "Ethan Hunt",       "email": "ethan@example.com",   "mobile": "9722334455", "balance": 3100.00},
        {"name": "Fiona Gallagher",  "email": "fiona@example.com",   "mobile": "9633445566", "balance": 750.00},
        {"name": "George Clark",     "email": "george@example.com",  "mobile": "9544556677", "balance": 1200.00},
        {"name": "Hannah Abbott",    "email": "hannah@example.com",  "mobile": "9455667788", "balance": 950.00},
        {"name": "Ian Malcolm",      "email": "ian@example.com",     "mobile": "9366778899", "balance": 4100.00},
        {"name": "Julia Roberts",    "email": "julia@example.com",   "mobile": "9277889900", "balance": 1600.00},
    ]
