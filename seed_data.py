import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient

# 1. Load connection string
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["apexbid_db"]

print("Connected to database. Starting Phase 2: Seeding Data...")

# 2. Reset existing data for a clean run
db.bid_ledger.delete_many({})
db.auctions.delete_many({})
db.users.delete_many({})
print("Cleared previous test data.")


users_data = [
    {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "mobile": "9876543210",
        "balance": 1500.00
    },
    {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "mobile": "9123456780",
        "balance": 800.00
    },
    {
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "mobile": "9988776655",
        "balance": 350.00
    }
]
user_insert_result = db.users.insert_many(users_data)
# Save their generated _ids to link them as sellers/bidders
alice_id = user_insert_result.inserted_ids[0]
bob_id = user_insert_result.inserted_ids[1]
charlie_id = user_insert_result.inserted_ids[2]
print(f"Successfully inserted {len(user_insert_result.inserted_ids)} users!")