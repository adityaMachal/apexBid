import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid    

load_dotenv()

MONGO_URI=os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found. check .env")

print("connecting to Atlas server...")
client = MongoClient(MONGO_URI)

db = client["apexbid_db"]

print("connection successfull!!")

print("\n--- 1. Creating users Collection with schema validation. ---")

user_validator = {
    "$jsonSchema":{
        "bsonType": "object",
        "required": ["name","email","mobile","balance"],
        "properties" : {
            "name" : {
                "bsonType" : "string",
                "description" : "User's full name (must be a string)"
            },
            "email" : {
                "bsonType" : "string",
                "pattern" : "^.+@.+$",          # Regex check must have @ symbol
                "description" : "Must be a valid email string"
            },
            "mobile" : {
                "bsonType" : "string",
                "pattern" : "^[1-9]{10}$",      #enforce exactly 10 numeric digits
                "description" : "Phone number String"
            },
            "balance" : {
                "bsonType" : "double",
                "minimum" : 0.0,                #enforces balance cannot be negative
                "description" : "Wallet balance (must be a float/double >= 0)"
            }
        }
    }
}

try:
    db.create_collection("users",validator=user_validator)
    print("Created 'users' Collection with strict schema validation!")
except CollectionInvalid:
    db.command("collMod","users",validator=user_validator)
    print("'users' already exists. Updated schema validation rules!")

db.users.create_index("email",unique=True)
print("created unique index on 'email'.")

print("\n--- 2. Creating 'auctions' collection with Schema Validation ---")

auction_validator = {
    "$jsonSchema" : {
        "bsonType" : "object",
        "required" : [
            "title",
            "category",
            "seller_id",
            "starting_price",
            "current_bid",
            "status",
            "ends_at"
        ],
        "properties" : {
            "title" : {
                "bsonType" : "string",
                "description" : "Item title (must be string)"
            },
            "category" : {
                "bsonType" : "string",
                "description" : "Category for analytics (e.g., Electronics, Art)"
            },
            "seller_id" : {
                "bsonType" : "objectId",
                "description" : "Must reference a valid user's id"
            },
            "staring_price" : {
                "bsonType" : "double",
                "minimum" : 0.0,
                "description" : "Base price must be a non-negative double"
            },
            "current_bid" : {
                "bsonType" : "double",
                "minimum" : 0.0,
                "description" : "current highest bid"
            },
            "Highest_bidder_id":{
                "bsonType" : ["objectId", "null"],
                "description" : "References user _id or null if no bids yet"
            },
            "status" : {
                "enum" : ["active", "ended", "settled"],
                "description" : "Can only be 'active', 'ended', or 'settled'"
            },
            "ends_at" : {
                "bsonType" : "date",
                "description" : "Auction expiration timestamp"
            },
            # The subset pattern: Strictly capped in 5 recent bids!
            "recent_bids" : {
                "bsonType" : "array",
                "maxItems" : 5,
                "description": "Subset pattern: latest 5 bids embedded for fast reads",
                "items" : {
                    "bsonType" : "object",
                    "required" : ["bidder_id","amount","timestamp"],
                    "properties" : {
                        "bidder_id" : {"bsonType" : "objectId"},
                        "amount" : {"bsonType" : "double"},
                        "time_stamp" : {"bsonType" : "date"}
                    }
                }
            }
        }
    }
}
try:
    db.create_collection("auctions", validator=auction_validator)
    print("Created 'auctions' collection with strict schema validation!")
except CollectionInvalid:
    db.command("collMod", "auctions", validator=auction_validator)
    print("'auctions' already exists. Updated schema validation rules!")
    
    # Indexes for auctions
print("Creating indexes on 'auctions'...")
    # 1. Compound index: Follows ESR rule (Equality on status, Sort on ends_at)
db.auctions.create_index([("status", 1), ("ends_at", 1)])
print("Created compound index: [('status', 1), ('ends_at', 1)].")
    
    # 2. Text index: Powers full-text keyword search on titles
db.auctions.create_index([("title", "text")])
print("Created text index on 'title'.")
