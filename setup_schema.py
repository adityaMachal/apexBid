import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI=os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found. check .env")

print("connecting to Atlas server...")
client = MongoClient(MONGO_URI)

db = client["apexbid_db"]

print("connection successfull!!")

