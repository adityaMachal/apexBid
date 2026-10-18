"""
tests/test_concurrency.py
Pytest suite verifying multi-threaded race condition safety under parallel load.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from bidding_engine import place_bid


def test_concurrent_bidding_race_conditions(database):
    """
    Spawns 10 parallel threads attempting to place the exact same bid ($150.00)
    at the exact same millisecond on the same auction document.

    Asserts:
    - Exactly 1 bid is accepted.
    - Exactly 9 bids are rejected.
    - Final database price equals exactly $150.00.
    - Zero dirty writes or race conditions occurred.
    """
    keyboard = database.auctions.find_one({"title": "1984 IBM Model M Mechanical Keyboard"})
    users = list(database.users.find().limit(10))

    assert keyboard and len(users) >= 10, "Required fixtures missing!"

    now = datetime.now(timezone.utc)
    database.auctions.update_one(
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

    identical_bid_amount = 150.00
    results = []

    def worker(user):
        success, msg, meta = place_bid(keyboard["_id"], user["_id"], identical_bid_amount)
        return {"user": user["name"], "success": success, "msg": msg}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, u) for u in users]
        for f in as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if r["success"]]
    rejections = [r for r in results if not r["success"]]

    # Assert exactly 1 winner and 9 rejections
    assert len(successes) == 1, f"Expected 1 winner, but got {len(successes)}"
    assert len(rejections) == 9, f"Expected 9 rejections, but got {len(rejections)}"

    # Assert database state integrity
    refreshed_auction = database.auctions.find_one({"_id": keyboard["_id"]})
    assert refreshed_auction["current_bid"] == 150.00
    assert refreshed_auction["highest_bidder_id"] is not None
    assert len(refreshed_auction.get("recent_bids", [])) == 1
