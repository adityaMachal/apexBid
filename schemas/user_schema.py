"""
schemas/user_schema.py
Defines the $jsonSchema validator and indexes for the 'users' collection.
"""

from pymongo.errors import CollectionInvalid


# Schema enforces: name (string), email (valid format), mobile (10 digits), balance (>= 0)
USER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "mobile", "balance"],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "User's full name (must be a string)"
            },
            "email": {
                "bsonType": "string",
                "pattern": "^.+@.+$",          # Regex check: must have '@' symbol
                "description": "Must be a valid email string"
            },
            "mobile": {
                "bsonType": "string",
                "pattern": "^[0-9]{10}$",       # Enforce exactly 10 numeric digits
                "description": "Phone number string"
            },
            "balance": {
                "bsonType": "double",
                "minimum": 0.0,                 # Enforces balance cannot be negative
                "description": "Wallet balance (must be a float/double >= 0)"
            }
        }
    }
}


def setup_users(db):
    """Creates the 'users' collection with strict schema validation and unique indexes."""

    print("\n--- Creating 'users' collection with Schema Validation ---")

    try:
        db.create_collection("users", validator=USER_VALIDATOR)
        print("Created 'users' collection with strict schema validation!")
    except CollectionInvalid:
        db.command("collMod", "users", validator=USER_VALIDATOR)
        print("'users' already exists. Updated schema validation rules!")

    # Unique index: No two users can share the same email
    db.users.create_index("email", unique=True)
    print("Created unique index on 'email'.")
