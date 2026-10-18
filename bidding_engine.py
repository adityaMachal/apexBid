"""
bidding_engine.py
Phase 3: The Atomic Bidding Engine & Edge-Case Guard Suite.

Handles bid placement with:
- Wallet balance verification
- Anti-shill bidding (sellers cannot bid on own items)
- Self-outbidding prevention
- Minimum bid increment enforcement
- Dynamic anti-sniping soft-close (extends deadline if bid in final 2 minutes)
- Atomic single-document concurrency guard (find_one_and_update)
- The Subset Pattern ($slice: 5)
- Append-only audit logging to bid_ledger
"""

from datetime import datetime, timedelta, timezone
from pymongo import ReturnDocument
from db_connection import db


def place_bid(auction_id, bidder_id, bid_amount, min_increment=5.00, max_extensions=5):
    """
    Places a bid on an active auction with comprehensive edge-case protection.

    Returns:
        (success: bool, message: str, metadata: dict)
    """
    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------
    # EDGE CASE 1: Verify Bidder Exists
    # -------------------------------------------------------------
    bidder = db.users.find_one({"_id": bidder_id})
    if not bidder:
        return False, "User not found.", {}

    # -------------------------------------------------------------
    # EDGE CASE 2: Insufficient Wallet Balance
    # -------------------------------------------------------------
    if bidder["balance"] < bid_amount:
        return (
            False,
            f"Insufficient funds! Wallet balance is ${bidder['balance']:.2f}, but bid is ${bid_amount:.2f}.",
            {"error_code": "INSUFFICIENT_FUNDS", "balance": bidder["balance"]}
        )

    # -------------------------------------------------------------
    # EDGE CASE 3: Verify Auction Exists & Fetch State
    # -------------------------------------------------------------
    auction = db.auctions.find_one({"_id": auction_id})
    if not auction:
        return False, "Auction not found.", {}

    # -------------------------------------------------------------
    # EDGE CASE 4: Auction Not Active
    # -------------------------------------------------------------
    if auction.get("status") != "active":
        return (
            False,
            f"Auction is not active! Current status is '{auction.get('status')}'.",
            {"error_code": "AUCTION_NOT_ACTIVE"}
        )

    # -------------------------------------------------------------
    # EDGE CASE 5: Auction Already Expired
    # -------------------------------------------------------------
    auction_ends_at = auction["ends_at"]
    if auction_ends_at.tzinfo is None:
        auction_ends_at = auction_ends_at.replace(tzinfo=timezone.utc)

    if auction_ends_at <= now:
        return (
            False,
            "Auction has already ended!",
            {"error_code": "AUCTION_EXPIRED"}
        )

    # -------------------------------------------------------------
    # EDGE CASE 6: Shill Bidding (Seller Bidding on Own Item)
    # -------------------------------------------------------------
    if auction["seller_id"] == bidder_id:
        return (
            False,
            "Shill bidding violation: Sellers cannot bid on their own listings!",
            {"error_code": "SHILL_BIDDING_DISALLOWED"}
        )

    # -------------------------------------------------------------
    # EDGE CASE 7: Outbidding Yourself
    # -------------------------------------------------------------
    if auction.get("highest_bidder_id") == bidder_id:
        return (
            False,
            "You are already the highest bidder on this item!",
            {"error_code": "ALREADY_HIGHEST_BIDDER"}
        )

    # -------------------------------------------------------------
    # EDGE CASE 8: Minimum Increment & Starting Price Rules
    # -------------------------------------------------------------
    has_prior_bids = auction.get("highest_bidder_id") is not None
    current_bid = auction["current_bid"]

    if not has_prior_bids:
        # First bid: must be >= starting price
        if bid_amount < auction["starting_price"]:
            return (
                False,
                f"First bid must be at least the starting price of ${auction['starting_price']:.2f}.",
                {"error_code": "BELOW_STARTING_PRICE"}
            )
    else:
        # Subsequent bid: must satisfy minimum increment (e.g. +$5.00)
        required_min = current_bid + min_increment
        if bid_amount < required_min:
            return (
                False,
                f"Bid increment too low! Current bid is ${current_bid:.2f}. Minimum next bid is ${required_min:.2f} (+${min_increment:.2f}).",
                {"error_code": "MIN_INCREMENT_NOT_MET", "required_min": required_min}
            )

    # -------------------------------------------------------------
    # EDGE CASE 9: Anti-Sniping Soft-Close (Final 2-Min Window)
    # -------------------------------------------------------------
    time_left_seconds = (auction_ends_at - now).total_seconds()
    extension_count = auction.get("extension_count", 0)

    extended = False
    new_ends_at = auction["ends_at"]

    # If within 120 seconds (2 mins) and under max allowed extensions
    if 0 < time_left_seconds <= 120 and extension_count < max_extensions:
        new_ends_at = auction_ends_at + timedelta(seconds=180)  # +3 minutes
        extended = True

    # -------------------------------------------------------------
    # STEP 10: Atomic Concurrency Guard (find_one_and_update)
    # -------------------------------------------------------------
    filter_doc = {
        "_id": auction_id,
        "status": "active",
        "ends_at": {"$gt": now},
    }

    if has_prior_bids:
        filter_doc["current_bid"] = {"$lt": bid_amount}
    else:
        filter_doc["current_bid"] = {"$lte": bid_amount}

    update_doc = {
        "$set": {
            "current_bid": bid_amount,
            "highest_bidder_id": bidder_id,
            "ends_at": new_ends_at,
            "updated_at": now
        },
        "$inc": {
            "bid_count": 1,
            "extension_count": 1 if extended else 0
        },
        # The Subset Pattern: Strictly keep only the top 5 newest bids
        "$push": {
            "recent_bids": {
                "$each": [{
                    "bidder_id": bidder_id,
                    "amount": bid_amount,
                    "timestamp": now
                }],
                "$sort": {"timestamp": -1},
                "$slice": 5
            }
        }
    }

    updated_auction = db.auctions.find_one_and_update(
        filter_doc,
        update_doc,
        return_document=ReturnDocument.AFTER
    )

    if not updated_auction:
        return (
            False,
            "Bid rejected by atomic query guard! (You were outbid concurrently or the auction ended during transit).",
            {"error_code": "CONCURRENT_OUTBID_OR_EXPIRED"}
        )

    # -------------------------------------------------------------
    # STEP 11: Append to Full Historical Audit Ledger
    # -------------------------------------------------------------
    db.bid_ledger.insert_one({
        "auction_id": auction_id,
        "bidder_id": bidder_id,
        "amount": bid_amount,
        "timestamp": now
    })

    msg = f"Bid accepted! ${bid_amount:.2f} is now the highest bid."
    if extended:
        msg += f" [ANTI-SNIPE TRIGGERED: Auction extended by 3 mins! New deadline: {new_ends_at.strftime('%H:%M:%S UTC')}]"

    return True, msg, {
        "current_bid": bid_amount,
        "extended": extended,
        "new_ends_at": new_ends_at
    }


if __name__ == "__main__":
    import subprocess
    print("ApexBid Bidding Engine: Pure Logic Module.")
    print("Running formal Pytest test suite...\n")
    subprocess.run(["pytest", "tests/test_bidding.py", "-v"])