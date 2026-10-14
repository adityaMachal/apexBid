"""
seed_data.py (Phase 2 Runner)
Populates the database with 10 mock users and 18 diverse auction listings.
Safe to re-run: clears previous test data before inserting.
"""

from db_connection import db
from data.mock_users import get_mock_users
from data.mock_auctions import get_mock_auctions


print("=== Phase 2: Seeding Data ===")

# 1. Clear previous test data (delete_many preserves schemas & indexes, unlike drop())
db.bid_ledger.delete_many({})
db.auctions.delete_many({})
db.users.delete_many({})
print("Cleared previous test data.")

# 2. Insert mock users
users = get_mock_users()
user_result = db.users.insert_many(users)
user_ids = user_result.inserted_ids
print(f"Inserted {len(user_ids)} users.")

# 3. Insert mock auctions (pass user_ids so auctions can reference sellers/bidders)
auctions = get_mock_auctions(user_ids)
auction_result = db.auctions.insert_many(auctions)
print(f"Inserted {len(auction_result.inserted_ids)} auctions across 4 categories.")

# 4. Summary
print("\n=== Phase 2 Complete: Database populated with rich test dataset! ===")
print(f"  Users:    {len(user_ids)}")
print(f"  Auctions: {len(auction_result.inserted_ids)}")
print(f"  Categories: Electronics, Collectibles, Gaming, Watches")
print(f"  Anti-snipe test items: 2 (ending in <2 minutes)")
print(f"  Ended auctions: 3 (for analytics pipeline)")