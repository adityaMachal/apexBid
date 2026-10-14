"""
schemas/ledger_schema.py
Defines the $jsonSchema validator and indexes for the 'bid_ledger' collection.
This is the append-only audit trail that stores every single bid ever placed.
"""

from pymongo.errors import CollectionInvalid


LEDGER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["auction_id", "bidder_id", "amount", "timestamp"],
        "properties": {
            "auction_id": {
                "bsonType": "objectId",
                "description": "Must reference an auction _id"
            },
            "bidder_id": {
                "bsonType": "objectId",
                "description": "Must reference a user _id"
            },
            "amount": {
                "bsonType": "double",
                "minimum": 0.0,
                "description": "Bid amount must be a positive double"
            },
            "timestamp": {
                "bsonType": "date",
                "description": "Time the bid was placed"
            }
        }
    }
}


def setup_ledger(db):
    """Creates the 'bid_ledger' collection with schema validation and lookup indexes."""

    print("\n--- Creating 'bid_ledger' collection with Schema Validation ---")

    try:
        db.create_collection("bid_ledger", validator=LEDGER_VALIDATOR)
        print("Created 'bid_ledger' collection with strict schema validation!")
    except CollectionInvalid:
        db.command("collMod", "bid_ledger", validator=LEDGER_VALIDATOR)
        print("'bid_ledger' already exists. Updated schema validation rules!")

    # Indexes for bid_ledger
    print("Creating indexes on 'bid_ledger'...")
    # Fast chronological lookup for all bids on a specific auction
    db.bid_ledger.create_index([("auction_id", 1), ("timestamp", -1)])
    # Fast lookup for all bids placed by a specific user
    db.bid_ledger.create_index([("bidder_id", 1)])
    print("Created indexes on 'bid_ledger'.")
