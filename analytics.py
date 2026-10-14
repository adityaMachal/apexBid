"""
analytics.py
Phase 5: Executive Market Analytics via MongoDB Aggregation Pipelines.

Demonstrates all major syllabus-level Aggregation stages:
1. Category Sales Performance:   $match -> $group -> $sort
2. Top Bidders Leaderboard:      $unwind -> $group -> $sort -> $limit -> $lookup -> $project
3. Market Price Distribution:    $bucket
"""

from db_connection import db


def run_category_performance_report():
    print("\n" + "=" * 80)
    print(" 📊 REPORT 1: CATEGORY SALES PERFORMANCE ($match -> $group -> $sort)")
    print("=" * 80)
    print("SQL Equivalent: SELECT category, COUNT(*), SUM(price), AVG(price) ... GROUP BY category")

    pipeline = [
        # Stage 1: Filter only settled or ended auctions
        {"$match": {"status": "ended"}},

        # Stage 2: Group by category and compute summary metrics
        {
            "$group": {
                "_id": "$category",
                "items_sold": {"$sum": 1},
                "total_revenue": {"$sum": "$current_bid"},
                "avg_sale_price": {"$avg": "$current_bid"},
                "highest_sale": {"$max": "$current_bid"}
            }
        },

        # Stage 3: Sort by highest revenue at the top
        {"$sort": {"total_revenue": -1}}
    ]

    results = list(db.auctions.aggregate(pipeline))

    if not results:
        print("No completed auctions found. Run 'python seed_data.py' first.")
        return

    print("\n" + "-" * 75)
    print(f"{'CATEGORY':<18} | {'SOLD':<6} | {'AVG PRICE':<14} | {'TOP SALE':<14} | {'TOTAL REVENUE'}")
    print("-" * 75)

    total_platform_revenue = 0.0
    for row in results:
        cat_name = row["_id"]
        sold = row["items_sold"]
        avg_p = f"${row['avg_sale_price']:,.2f}"
        max_p = f"${row['highest_sale']:,.2f}"
        rev = f"${row['total_revenue']:,.2f}"
        total_platform_revenue += row["total_revenue"]

        print(f"{cat_name:<18} | {sold:<6} | {avg_p:<14} | {max_p:<14} | {rev}")

    print("-" * 75)
    print(f"{'TOTAL PLATFORM REVENUE':<42} : ${total_platform_revenue:,.2f}")
    print("-" * 75)


def run_top_bidders_leaderboard():
    print("\n" + "=" * 80)
    print(" 🏆 REPORT 2: TOP BIDDERS LEADERBOARD ($unwind -> $group -> $lookup -> $project)")
    print("=" * 80)
    print("Demonstrates: Array deconstruction ($unwind) and Cross-Collection JOIN ($lookup)")

    pipeline = [
        # Stage 1: Deconstruct the recent_bids array into flat documents
        {"$unwind": "$recent_bids"},

        # Stage 2: Group by bidder_id to count activity and total commitment
        {
            "$group": {
                "_id": "$recent_bids.bidder_id",
                "bids_placed": {"$sum": 1},
                "highest_bid": {"$max": "$recent_bids.amount"},
                "total_pledged": {"$sum": "$recent_bids.amount"}
            }
        },

        # Stage 3: Sort by most active bidders
        {"$sort": {"bids_placed": -1, "total_pledged": -1}},

        # Stage 4: Top 5 bidders
        {"$limit": 5},

        # Stage 5: Cross-Collection JOIN with 'users' to fetch real human names & email
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }
        },

        # Stage 6: Flatten joined user_info array
        {"$unwind": "$user_info"},

        # Stage 7: Project clean, formatted presentation columns
        {
            "$project": {
                "name": "$user_info.name",
                "email": "$user_info.email",
                "wallet_balance": "$user_info.balance",
                "bids_placed": 1,
                "highest_bid": 1,
                "total_pledged": 1
            }
        }
    ]

    results = list(db.auctions.aggregate(pipeline))

    if not results:
        print("No bids found in dataset.")
        return

    print("\n" + "-" * 88)
    print(f"{'RANK':<5} | {'BIDDER NAME':<18} | {'BIDS':<6} | {'TOP BID':<12} | {'TOTAL PLEDGED':<15} | {'WALLET'}")
    print("-" * 88)

    for idx, row in enumerate(results, 1):
        name = row["name"]
        bids = row["bids_placed"]
        top_b = f"${row['highest_bid']:,.2f}"
        pledged = f"${row['total_pledged']:,.2f}"
        wallet = f"${row['wallet_balance']:,.2f}"

        print(f"#{idx:<4} | {name:<18} | {bids:<6} | {top_b:<12} | {pledged:<15} | {wallet}")

    print("-" * 88)


def run_price_tier_histogram():
    print("\n" + "=" * 80)
    print(" 📈 REPORT 3: MARKET PRICE BRACKET HISTOGRAM ($bucket)")
    print("=" * 80)
    print("Calculates item volume across price tiers without if/else code branches")

    tier_labels = {
        0.0:    "Budget Tier        ($0 - $100)",
        100.0:  "Mid-Range Tier     ($100 - $500)",
        500.0:  "Premium Tier       ($500 - $2,000)",
        2000.0: "Luxury Investment  ($2,000+)"
    }

    pipeline = [
        {
            "$bucket": {
                "groupBy": "$current_bid",
                "boundaries": [0.0, 100.0, 500.0, 2000.0, 10000.0],
                "default": "Ultra-Luxury (> $10k)",
                "output": {
                    "count": {"$sum": 1},
                    "avg_price": {"$avg": "$current_bid"},
                    "sample_item": {"$first": "$title"}
                }
            }
        }
    ]

    results = list(db.auctions.aggregate(pipeline))

    print("\n" + "-" * 85)
    print(f"{'PRICE TIER':<32} | {'ITEMS':<6} | {'AVG PRICE':<14} | {'EXAMPLE ITEM'}")
    print("-" * 85)

    for row in results:
        lower_bound = row["_id"]
        label = tier_labels.get(lower_bound, f"Tier starting at ${lower_bound}")
        count = row["count"]
        avg_p = f"${row['avg_price']:,.2f}"
        sample = row["sample_item"][:26] + "..." if len(row["sample_item"]) > 26 else row["sample_item"]

        print(f"{label:<32} | {count:<6} | {avg_p:<14} | {sample}")

    print("-" * 85)


def run_all_analytics():
    print("\n" + "#" * 80)
    print("        APEXBID EXECUTIVE ANALYTICS DASHBOARD (MONGODB PIPELINES)")
    print("#" * 80)

    run_category_performance_report()
    run_top_bidders_leaderboard()
    run_price_tier_histogram()

    print("\n" + "#" * 80)
    print(" ✅ ALL 3 AGGREGATION PIPELINES EXECUTED SUCCESSFULLY ON MONGODB ATLAS")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    run_all_analytics()
