"""
schemas/auction_schema.py
Defines the $jsonSchema validator and indexes for the 'auctions' collection.
Implements the Subset Pattern: recent_bids array is capped at 5 items.
"""

from pymongo.errors import CollectionInvalid


AUCTION_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "title",
            "category",
            "seller_id",
            "starting_price",
            "current_bid",
            "status",
            "ends_at"
        ],
        "properties": {
            "title": {
                "bsonType": "string",
                "description": "Item title (must be string)"
            },
            "category": {
                "bsonType": "string",
                "description": "Category for analytics (e.g., Electronics, Art)"
            },
            "seller_id": {
                "bsonType": "objectId",
                "description": "Must reference a valid user's _id"
            },
            "starting_price": {
                "bsonType": "double",
                "minimum": 0.0,
                "description": "Base price must be a non-negative double"
            },
            "current_bid": {
                "bsonType": "double",
                "minimum": 0.0,
                "description": "Current highest bid"
            },
            "highest_bidder_id": {
                "bsonType": ["objectId", "null"],
                "description": "References user _id or null if no bids yet"
            },
            "status": {
                "enum": ["active", "ended", "settled"],
                "description": "Can only be 'active', 'ended', or 'settled'"
            },
            "ends_at": {
                "bsonType": "date",
                "description": "Auction expiration timestamp"
            },
            # The Subset Pattern: Strictly capped at 5 recent bids!
            "recent_bids": {
                "bsonType": "array",
                "maxItems": 5,
                "description": "Subset pattern: latest 5 bids embedded for fast reads",
                "items": {
                    "bsonType": "object",
                    "required": ["bidder_id", "amount", "timestamp"],
                    "properties": {
                        "bidder_id": {"bsonType": "objectId"},
                        "amount": {"bsonType": "double"},
                        "timestamp": {"bsonType": "date"}
                    }
                }
            }
        }
    }
}


def setup_auctions(db):
    """Creates the 'auctions' collection with schema validation and performance indexes."""

    print("\n--- Creating 'auctions' collection with Schema Validation ---")

    try:
        db.create_collection("auctions", validator=AUCTION_VALIDATOR)
        print("Created 'auctions' collection with strict schema validation!")
    except CollectionInvalid:
        db.command("collMod", "auctions", validator=AUCTION_VALIDATOR)
        print("'auctions' already exists. Updated schema validation rules!")

    # 1. Compound index: Follows ESR rule (Equality on status, Sort on ends_at)
    print("Creating indexes on 'auctions'...")
    db.auctions.create_index([("status", 1), ("ends_at", 1)])
    print("Created compound index: [('status', 1), ('ends_at', 1)].")

    # 2. Text index: Powers full-text keyword search on titles
    db.auctions.create_index([("title", "text")])
    print("Created text index on 'title'.")
