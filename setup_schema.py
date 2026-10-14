"""
setup_schema.py (Phase 1 Runner)
Initializes all 3 collections with strict $jsonSchema validation and indexes.
Run this ONCE to set up the database structure.
"""

from db_connection import db
from schemas.user_schema import setup_users
from schemas.auction_schema import setup_auctions
from schemas.ledger_schema import setup_ledger


print("=== Phase 1: Database Schema Setup ===")
print("Connected to database:", db.name)

# Create collections with validation and indexes
setup_users(db)
setup_auctions(db)
setup_ledger(db)

print("\n=== Phase 1 Complete: All 3 collections, schemas, and indexes configured! ===")