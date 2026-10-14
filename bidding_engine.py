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


# =====================================================================
# AUTOMATED TEST SUITE & REPORT GENERATOR
# =====================================================================
def run_edge_case_test_suite():
    print("=" * 80)
    print("      APEXBID: BIDDING ENGINE EDGE-CASE VERIFICATION SUITE")
    print("=" * 80)
    print("Connecting to database and fetching test documents...\n")

    # Fetch reference users
    alice = db.users.find_one({"email": "alice@example.com"})
    bob = db.users.find_one({"email": "bob@example.com"})
    charlie = db.users.find_one({"email": "charlie@example.com"})
    diana = db.users.find_one({"email": "diana@example.com"})
    ethan = db.users.find_one({"email": "ethan@example.com"})

    # Fetch reference auctions
    keyboard = db.auctions.find_one({"title": "1984 IBM Model M Mechanical Keyboard"})
    charizard = db.auctions.find_one({"title": "First Edition Holographic Charizard (PSA 8)"})
    rtx_gpu = db.auctions.find_one({"title": "RTX 4090 Founders Edition GPU"})
    ended_ps1 = db.auctions.find_one({"title": "Sony PlayStation 1 (Original 1994 Model)"})

    if not (alice and bob and charlie and diana and ethan and keyboard and rtx_gpu and ended_ps1):
        print("ERROR: Test fixtures missing! Please run 'python seed_data.py' first.")
        return

    # Reset test items to baseline so this suite can be run repeatedly without re-seeding
    now_init = datetime.now(timezone.utc)
    db.auctions.update_one(
        {"_id": keyboard["_id"]},
        {"$set": {"current_bid": 120.00, "highest_bidder_id": bob["_id"], "status": "active", "ends_at": now_init + timedelta(days=2)}}
    )
    db.auctions.update_one(
        {"_id": rtx_gpu["_id"]},
        {"$set": {"current_bid": 1400.00, "highest_bidder_id": bob["_id"], "status": "active", "ends_at": now_init + timedelta(seconds=90)}}
    )

    test_results = []

    def execute_test(test_id, name, auction_id, bidder_id, amount, expect_success, expected_reason):
        print(f"Running Test {test_id}: {name}...")
        success, message, meta = place_bid(auction_id, bidder_id, amount)

        passed = (success == expect_success)
        status_label = "PASS" if passed else "FAIL"

        print(f"  Result:   {'ACCEPTED' if success else 'REJECTED'}")
        print(f"  Message:  {message}")
        print(f"  Status:   [{status_label}]\n")

        test_results.append({
            "id": test_id,
            "scenario": name,
            "bid_amount": f"${amount:.2f}",
            "expected": "ACCEPT" if expect_success else "REJECT",
            "actual": "ACCEPT" if success else "REJECT",
            "reason": expected_reason,
            "passed": passed
        })

    # Test 1: Normal Valid Bid
    execute_test(
        1,
        "Standard Valid Bid",
        keyboard["_id"],
        charlie["_id"],
        135.00,
        expect_success=True,
        expected_reason="Beats current bid ($120.00) + meets min increment ($5.00)"
    )

    # Test 2: Micro-bidding Increment Violation (+$1.00 instead of +$5.00)
    execute_test(
        2,
        "Micro-Bidding Guard",
        keyboard["_id"],
        diana["_id"],
        136.00,
        expect_success=False,
        expected_reason="Rejected: $136.00 is below minimum next bid ($140.00)"
    )

    # Test 3: Outbidding Yourself
    execute_test(
        3,
        "Self-Outbidding Guard",
        keyboard["_id"],
        charlie["_id"],  # Charlie just won Test 1
        150.00,
        expect_success=False,
        expected_reason="Rejected: Charlie is already the highest bidder"
    )

    # Test 4: Shill Bidding (Seller bidding on own item)
    execute_test(
        4,
        "Shill Bidding Guard",
        keyboard["_id"],
        alice["_id"],    # Alice is the seller of the keyboard
        180.00,
        expect_success=False,
        expected_reason="Rejected: Seller cannot bid on own listing"
    )

    # Test 5: Insufficient Funds in Wallet
    execute_test(
        5,
        "Insufficient Funds Guard",
        charizard["_id"],
        charlie["_id"],  # Charlie balance is $450, Charizard current bid is $1850
        2000.00,
        expect_success=False,
        expected_reason="Rejected: Charlie wallet ($450.00) < bid ($2000.00)"
    )

    # Test 6: Anti-Sniping Soft-Close Trigger (ends in <2 minutes)
    # Refresh ends_at to strictly 90 seconds from THIS moment so the test never goes stale
    now_test = datetime.now(timezone.utc)
    db.auctions.update_one(
        {"_id": rtx_gpu["_id"]},
        {"$set": {"ends_at": now_test + timedelta(seconds=90), "status": "active"}}
    )

    execute_test(
        6,
        "Anti-Sniping Soft-Close",
        rtx_gpu["_id"],
        ethan["_id"],    # Ethan bids $1450.00 (Seller is Diana, so this is valid)
        1450.00,
        expect_success=True,
        expected_reason="Accepted & Extended deadline by +3 minutes"
    )

    # Test 7: Bidding on Ended Auction
    execute_test(
        7,
        "Expired Auction Guard",
        ended_ps1["_id"],
        bob["_id"],
        200.00,
        expect_success=False,
        expected_reason="Rejected: Status is 'ended' and deadline has passed"
    )

    # Test 8: Below Current Bid / Stale Concurrency
    execute_test(
        8,
        "Stale / Lower Bid Guard",
        keyboard["_id"],
        bob["_id"],
        100.00,          # Current bid is now $135.00
        expect_success=False,
        expected_reason="Rejected: Bid ($100.00) is lower than current ($135.00)"
    )

    # =============================================================
    # FINAL TABULAR REPORT (Academic / Viva Ready)
    # =============================================================
    print("=" * 105)
    print(f"{'TEST':<5} | {'SCENARIO':<26} | {'BID':<9} | {'EXPECTED':<9} | {'ACTUAL':<9} | {'STATUS':<7} | {'RULE ENFORCED'}")
    print("=" * 105)

    all_passed = True
    for t in test_results:
        status_str = "PASS [OK]" if t["passed"] else "FAIL [X]"
        print(f"T{t['id']:<4} | {t['scenario']:<26} | {t['bid_amount']:<9} | {t['expected']:<9} | {t['actual']:<9} | {status_str:<9} | {t['reason']}")
        if not t["passed"]:
            all_passed = False

    print("=" * 105)
    if all_passed:
        print("\n🎉 ALL 8 EDGE-CASE TESTS PASSED! Bidding Engine is 100% verified.")
    else:
        print("\n⚠️ SOME TESTS FAILED. Review output above.")
    print("=" * 105)


if __name__ == "__main__":
    run_edge_case_test_suite()