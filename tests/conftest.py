"""
tests/conftest.py
Shared Pytest fixtures for ApexBid test suites.
Handles database connections, test user retrieval, and state resets.
"""

from datetime import datetime, timedelta, timezone
import pytest
from db_connection import db


@pytest.fixture(scope="session")
def database():
    """Provides shared MongoDB database client instance."""
    return db


@pytest.fixture(scope="session")
def users(database):
    """Provides pre-seeded reference users mapped by name."""
    alice = database.users.find_one({"email": "alice@example.com"})
    bob = database.users.find_one({"email": "bob@example.com"})
    charlie = database.users.find_one({"email": "charlie@example.com"})
    diana = database.users.find_one({"email": "diana@example.com"})
    ethan = database.users.find_one({"email": "ethan@example.com"})

    assert all([alice, bob, charlie, diana, ethan]), "Seed data missing! Run 'python seed_data.py' first."

    return {
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "diana": diana,
        "ethan": ethan
    }


@pytest.fixture
def clean_keyboard_auction(database, users):
    """
    Sets up an active auction item with known baseline state:
    Current bid: $120.00 by Bob. Seller: Alice. Ends in 2 days.
    """
    now = datetime.now(timezone.utc)
    auction = database.auctions.find_one({"title": "1984 IBM Model M Mechanical Keyboard"})
    assert auction, "Keyboard auction fixture missing!"

    # Reset to baseline
    database.auctions.update_one(
        {"_id": auction["_id"]},
        {
            "$set": {
                "starting_price": 50.00,
                "current_bid": 120.00,
                "highest_bidder_id": users["bob"]["_id"],
                "seller_id": users["alice"]["_id"],
                "status": "active",
                "ends_at": now + timedelta(days=2),
                "extension_count": 0,
                "recent_bids": [
                    {"bidder_id": users["bob"]["_id"], "amount": 120.00, "timestamp": now - timedelta(hours=2)}
                ]
            }
        }
    )

    return database.auctions.find_one({"_id": auction["_id"]})


@pytest.fixture
def anti_snipe_auction(database, users):
    """
    Sets up an auction expiring in 90 seconds (inside the 2-minute soft-close window).
    Seller: Diana. Current bid: $1400.00 by Bob.
    """
    now = datetime.now(timezone.utc)
    auction = database.auctions.find_one({"title": "RTX 4090 Founders Edition GPU"})
    assert auction, "RTX 4090 auction fixture missing!"

    database.auctions.update_one(
        {"_id": auction["_id"]},
        {
            "$set": {
                "starting_price": 1000.00,
                "current_bid": 1400.00,
                "highest_bidder_id": users["bob"]["_id"],
                "seller_id": users["diana"]["_id"],
                "status": "active",
                "ends_at": now + timedelta(seconds=90),
                "extension_count": 0
            }
        }
    )

    return database.auctions.find_one({"_id": auction["_id"]})
