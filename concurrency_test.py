"""
concurrency_test.py
Phase 4/Bonus: Multi-Threaded Concurrency & Race Condition Verification.

Simulates 10 concurrent threads (users) attacking MongoDB at the exact same millisecond
to prove that find_one_and_update guarantees zero duplicate winners and zero race conditions.
"""

import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_connection import db
from bidding_engine import place_bid


def run_concurrency_race_test():
    print("=" * 80)
    print("      APEXBID: MULTI-THREADED CONCURRENCY RACE CONDITION TEST")
    print("=" * 80)
    print("Objective: Simulate 10 users placing a bid of $150.00 at the EXACT same millisecond.")
    print("Expected:  Exactly 1 bid succeeds. Exactly 9 bids get rejected. Zero dirty writes.\n")

    # Fetch reference test item and users
    keyboard = db.auctions.find_one({"title": "1984 IBM Model M Mechanical Keyboard"})
    users = list(db.users.find().limit(10))

    if not keyboard or len(users) < 10:
        print("ERROR: Test fixtures missing! Please run 'python seed_data.py' first.")
        return

    # Reset keyboard to clean starting state ($100.00 starting price, no bids)
    now = datetime.now(timezone.utc)
    db.auctions.update_one(
        {"_id": keyboard["_id"]},
        {
            "$set": {
                "starting_price": 100.00,
                "current_bid": 100.00,
                "highest_bidder_id": None,
                "status": "active",
                "ends_at": now + timedelta(days=2),
                "recent_bids": []
            }
        }
    )

    print("Baseline State:")
    print(f"  Item:         {keyboard['title']}")
    print(f"  Starting Bid: $100.00")
    print(f"  Competitors:  10 distinct users firing simultaneously\n")

    results = []
    identical_bid_amount = 150.00

    # Thread worker function
    def worker_bid(user):
        start_t = time.perf_counter()
        success, msg, meta = place_bid(keyboard["_id"], user["_id"], identical_bid_amount)
        duration_ms = (time.perf_counter() - start_t) * 1000
        return {
            "user": user["name"],
            "success": success,
            "message": msg,
            "duration_ms": duration_ms
        }

    print(">>> FIRING 10 CONCURRENT WORKER THREADS SIMULTANEOUSLY <<<")

    # Use ThreadPoolExecutor to spawn 10 parallel threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_bid, u) for u in users]
        for f in as_completed(futures):
            results.append(f.result())

    # Analyze outcomes
    successes = [r for r in results if r["success"]]
    rejections = [r for r in results if not r["success"]]

    print("\n" + "-" * 85)
    print(f"{'THREAD / USER':<20} | {'BID AMOUNT':<12} | {'OUTCOME':<10} | {'LATENCY':<10} | {'SERVER RESPONSE'}")
    print("-" * 85)

    for r in results:
        outcome = "ACCEPTED" if r["success"] else "REJECTED"
        print(f"{r['user']:<20} | ${identical_bid_amount:<11.2f} | {outcome:<10} | {r['duration_ms']:>6.1f}ms  | {r['message'][:30]}...")

    print("-" * 85)

    # Database state verification
    fresh_auction = db.auctions.find_one({"_id": keyboard["_id"]})
    winning_user = db.users.find_one({"_id": fresh_auction["highest_bidder_id"]})

    print("\n" + "=" * 80)
    print(" CONCURRENCY AUDIT REPORT")
    print("=" * 80)
    print(f"  Total Simultaneous Threads : {len(results)}")
    print(f"  Successful Bids Committed  : {len(successes)} (Expected: 1)")
    print(f"  Conflicting Bids Rejected  : {len(rejections)} (Expected: 9)")
    print(f"  Final Database Price       : ${fresh_auction['current_bid']:.2f}")
    print(f"  Winner Recorded in DB      : {winning_user['name'] if winning_user else 'None'}")
    print(f"  Embedded Bids Count        : {len(fresh_auction.get('recent_bids', []))} (Subset Pattern)")
    print("=" * 80)

    if len(successes) == 1 and len(rejections) == 9 and fresh_auction["current_bid"] == 150.00:
        print("🎉 CONCURRENCY PROOF: ZERO RACE CONDITIONS! MongoDB serialized all 10 parallel writes.")
    else:
        print("⚠️ CONCURRENCY ANOMALY DETECTED. Review logs.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_concurrency_race_test()
