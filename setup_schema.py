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