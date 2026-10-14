"""
db_connection.py
Shared MongoDB Atlas connection module.
All scripts import `db` from here instead of duplicating connection logic.
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found. Check your .env file!")

client = MongoClient(MONGO_URI)
db = client["apexbid_db"]
