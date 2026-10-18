"""
tests/test_analytics.py
Pytest suite verifying MongoDB aggregation pipelines.
"""

from db_connection import db


def test_category_performance_pipeline():
    """Verifies $match -> $group -> $sort returns valid category aggregations."""
    pipeline = [
        {"$match": {"status": "ended"}},
        {
            "$group": {
                "_id": "$category",
                "items_sold": {"$sum": 1},
                "total_revenue": {"$sum": "$current_bid"},
                "avg_sale_price": {"$avg": "$current_bid"}
            }
        },
        {"$sort": {"total_revenue": -1}}
    ]

    results = list(db.auctions.aggregate(pipeline))

    assert len(results) > 0, "Expected at least 1 category aggregation result"
    for r in results:
        assert "_id" in r
        assert r["items_sold"] >= 1
        assert r["total_revenue"] > 0
        assert r["avg_sale_price"] > 0


def test_top_bidders_lookup_pipeline():
    """Verifies $unwind -> $group -> $lookup cross-collection join."""
    pipeline = [
        {"$unwind": "$recent_bids"},
        {
            "$group": {
                "_id": "$recent_bids.bidder_id",
                "bids_placed": {"$sum": 1},
                "total_pledged": {"$sum": "$recent_bids.amount"}
            }
        },
        {"$sort": {"bids_placed": -1}},
        {"$limit": 5},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }
        },
        {"$unwind": "$user_info"},
        {
            "$project": {
                "name": "$user_info.name",
                "email": "$user_info.email",
                "bids_placed": 1
            }
        }
    ]

    results = list(db.auctions.aggregate(pipeline))

    assert len(results) > 0, "Expected at least 1 leaderboard entry"
    for r in results:
        assert "name" in r and len(r["name"]) > 0
        assert "email" in r and "@" in r["email"]
        assert r["bids_placed"] >= 1


def test_price_tier_bucket_pipeline():
    """Verifies $bucket groups auctions into price intervals."""
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$current_bid",
                "boundaries": [0.0, 100.0, 500.0, 2000.0, 10000.0],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                    "avg_price": {"$avg": "$current_bid"}
                }
            }
        }
    ]

    results = list(db.auctions.aggregate(pipeline))

    assert len(results) > 0, "Expected at least 1 price bucket"
    total_bucketed_items = sum(r["count"] for r in results)
    assert total_bucketed_items >= 10, "Expected at least 10 items in buckets"
