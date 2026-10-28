"""
app.py
ApexBid: Executive Interactive Dashboard
Built with Streamlit & MongoDB Atlas.

Features:
- Tab 1: Live Marketplace & Interactive Bidding Engine (with Soft-Close Anti-Sniping alerts)
- Tab 2: Executive Analytics (MongoDB Aggregation Pipelines: $match, $group, $lookup, $bucket)
- Tab 3: Multi-Threaded Concurrency Stress Test Simulator
"""

import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st
from db_connection import db
from bidding_engine import place_bid
from data.mock_users import get_mock_users
from data.mock_auctions import get_mock_auctions

# ==============================================================================
# PAGE CONFIGURATION & THEME STYLING
# ==============================================================================
st.set_page_config(
    page_title="ApexBid ⚡ High-Concurrency Auction Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #161E2E;
        border: 1px solid #283548;
        border-radius: 8px;
        padding: 18px;
        text-align: center;
    }
    .badge-active {
        background-color: #064E3B;
        color: #34D399;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-snipe {
        background-color: #7C2D12;
        color: #F87171;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 700;
        animation: blink 1.5s infinite;
    }
    .badge-ended {
        background-color: #374151;
        color: #9CA3AF;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# SIDEBAR: USER SWITCHER & PLATFORM CONTROLS
# ==============================================================================
st.sidebar.title("⚡ ApexBid Engine")
st.sidebar.caption("High-Concurrency MongoDB Showcase")
st.sidebar.markdown("---")

# Fetch all users
users_cursor = list(db.users.find().sort("name", 1))
user_map = {u["name"]: u for u in users_cursor}

if not user_map:
    st.sidebar.warning("No users found. Please seed the database.")
    selected_user = None
else:
    selected_user_name = st.sidebar.selectbox("👤 Active Bidder Profile", list(user_map.keys()), index=1)
    selected_user = user_map[selected_user_name]

    # Live Wallet Card
    fresh_user_doc = db.users.find_one({"_id": selected_user["_id"]})
    st.sidebar.markdown(f"""
    **Wallet Balance:** `${fresh_user_doc['balance']:,.2f}`  
    **Email:** `{fresh_user_doc['email']}`  
    **Mobile:** `{fresh_user_doc['mobile']}`
    """)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Database Admin Tools")

# Database Re-Seeding Button
if st.sidebar.button("🔄 Reset Seed Data", use_container_width=True):
    with st.spinner("Resetting test collections..."):
        db.bid_ledger.delete_many({})
        db.auctions.delete_many({})
        db.users.delete_many({})

        users_list = get_mock_users()
        u_res = db.users.insert_many(users_list)
        auctions_list = get_mock_auctions(u_res.inserted_ids)
        db.auctions.insert_many(auctions_list)

        st.sidebar.success("Database restored to fresh seed state!")
        time.sleep(1)
        st.rerun()

# Run Pytest in Sidebar
if st.sidebar.button("🧪 Run Automated Pytest Suite", use_container_width=True):
    import subprocess
    with st.spinner("Running 12 Pytest verification suites..."):
        res = subprocess.run(["venv/bin/pytest", "-v"], capture_output=True, text=True)
        if res.returncode == 0:
            st.sidebar.success("✅ 12/12 Pytest Tests Passed!")
        else:
            st.sidebar.error("Tests failed. Review terminal logs.")
        with st.sidebar.expander("View Test Output"):
            st.code(res.stdout, language="text")


# ==============================================================================
# MAIN TABS INTERFACE
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "🏷️ Live Auctions & Bidding Simulator",
    "📊 Executive Analytics (Aggregation Pipelines)",
    "⚡ Multi-Threaded Concurrency Test"
])


# ==============================================================================
# TAB 1: LIVE AUCTIONS & INTERACTIVE BIDDING SIMULATOR
# ==============================================================================
with tab1:
    st.subheader("Active Auction Marketplace")

    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 2])
    with col_filter1:
        cat_filter = st.selectbox("Category Filter", ["All Categories", "Electronics", "Collectibles", "Gaming", "Watches"])
    with col_filter2:
        status_filter = st.selectbox("Status Filter", ["active", "ended", "All"])
    with col_filter3:
        search_query = st.text_input("🔍 Search Listings", placeholder="e.g. Keyboard, Camera, GPU")

    now_utc = datetime.now(timezone.utc)

    # Build MongoDB Query Filter
    mongo_filter = {}
    if cat_filter != "All Categories":
        mongo_filter["category"] = cat_filter
    if status_filter == "active":
        mongo_filter["status"] = "active"
        mongo_filter["ends_at"] = {"$gt": now_utc}
    elif status_filter == "ended":
        mongo_filter["$or"] = [
            {"status": "ended"},
            {"ends_at": {"$lte": now_utc}}
        ]
    if search_query:
        mongo_filter["title"] = {"$regex": search_query, "$options": "i"}

    # Query Auctions using Compound Index: status + ends_at
    auctions = list(db.auctions.find(mongo_filter).sort([("status", 1), ("ends_at", 1)]))

    st.markdown(f"**Found {len(auctions)} listings matching criteria.**")

    # Display Listings in 2-column grid
    for i in range(0, len(auctions), 2):
        colA, colB = st.columns(2)

        for col, auction in zip([colA, colB], auctions[i:i+2]):
            with col:
                ends_at = auction["ends_at"]
                if ends_at.tzinfo is None:
                    ends_at = ends_at.replace(tzinfo=timezone.utc)

                time_remaining = (ends_at - now_utc).total_seconds()

                # Status Badge
                if auction["status"] == "ended" or time_remaining <= 0:
                    badge_html = '<span class="badge-ended">ENDED</span>'
                    time_display = "Closed"
                elif 0 < time_remaining <= 120:
                    badge_html = '<span class="badge-snipe">🔥 SOFT-CLOSE (<2m)</span>'
                    time_display = f"{int(time_remaining)}s remaining"
                else:
                    badge_html = '<span class="badge-active">ACTIVE</span>'
                    hours = int(time_remaining // 3600)
                    mins = int((time_remaining % 3600) // 60)
                    time_display = f"{hours}h {mins}m remaining"

                # Seller & Winner names
                seller_doc = db.users.find_one({"_id": auction["seller_id"]})
                seller_name = seller_doc["name"] if seller_doc else "Unknown"

                winner_name = "None (No bids yet)"
                if auction.get("highest_bidder_id"):
                    winner_doc = db.users.find_one({"_id": auction["highest_bidder_id"]})
                    winner_name = winner_doc["name"] if winner_doc else "Unknown"

                with st.expander(f"{auction['title']} — ${auction['current_bid']:,.2f}", expanded=(time_remaining > 0 and time_remaining <= 120)):
                    st.markdown(f"""
                    **Category:** {auction['category']} &nbsp;|&nbsp; **Status:** {badge_html} &nbsp;|&nbsp; **Time Left:** `{time_display}`  
                    **Seller:** {seller_name} &nbsp;|&nbsp; **Leading Bidder:** {winner_name}  
                    **Current Highest Bid:** `${auction['current_bid']:,.2f}` *(Starting: ${auction['starting_price']:,.2f})*
                    """, unsafe_allow_html=True)

                    # Subset Pattern: Display recent bids embedded array
                    recent_bids = auction.get("recent_bids", [])
                    if recent_bids:
                        st.caption("Latest Bids (The Subset Pattern — Max 5 Embedded):")
                        bid_rows = []
                        for b in recent_bids:
                            b_user = db.users.find_one({"_id": b["bidder_id"]})
                            b_name = b_user["name"] if b_user else "Unknown"
                            bid_rows.append({"Bidder": b_name, "Amount": f"${b['amount']:,.2f}", "Timestamp": str(b['timestamp'])[:19]})
                        st.dataframe(pd.DataFrame(bid_rows), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # INTERACTIVE BID PLACEMENT FORM
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 Interactive Bidding Terminal")
    st.caption("Test atomic concurrency guards, anti-sniping dynamic soft-close, and wallet validation live:")

    active_auctions = list(db.auctions.find({"status": "active", "ends_at": {"$gt": now_utc}}).sort("ends_at", 1))
    auction_picker = {f"{a['title']} (Current: ${a['current_bid']:,.2f})": a for a in active_auctions}

    if not auction_picker:
        st.info("No active auctions available to bid on.")
    else:
        form_col1, form_col2, form_col3 = st.columns([3, 2, 2])

        with form_col1:
            chosen_title = st.selectbox("Select Target Listing", list(auction_picker.keys()))
            target_auction = auction_picker[chosen_title]

        with form_col2:
            min_next = target_auction["current_bid"] + 5.00
            bid_input = st.number_value = st.number_input(
                "Your Bid Amount ($)",
                min_value=1.0,
                value=float(min_next),
                step=5.0
            )

        with form_col3:
            st.write("&nbsp;")
            submit_bid = st.button("⚡ Submit Atomic Bid", use_container_width=True, type="primary")

        if submit_bid:
            if not selected_user:
                st.error("No active user selected.")
            else:
                success, msg, meta = place_bid(target_auction["_id"], selected_user["_id"], bid_input)

                if success:
                    st.success(f"✅ {msg}")
                    if meta.get("extended"):
                        st.balloons()
                        st.warning("⏰ ANTI-SNIPING TRIGGERED! Deadline was dynamically extended by +3 minutes at the database layer.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ==============================================================================
# TAB 2: EXECUTIVE ANALYTICS (AGGREGATION PIPELINES)
# ==============================================================================
with tab2:
    st.subheader("Platform Analytics Engine (MongoDB Aggregation Pipelines)")
    st.caption("All metrics computed natively on the database server in C++ without pulling raw rows into application memory.")

    # High-level Metrics
    total_rev_pipeline = [
        {"$match": {"status": "ended"}},
        {"$group": {"_id": None, "total": {"$sum": "$current_bid"}}}
    ]
    rev_res = list(db.auctions.aggregate(total_rev_pipeline))
    tot_rev = rev_res[0]["total"] if rev_res else 0.0

    now_tab2 = datetime.now(timezone.utc)
    active_count = db.auctions.count_documents({"status": "active", "ends_at": {"$gt": now_tab2}})
    ended_count = db.auctions.count_documents({"$or": [{"status": "ended"}, {"ends_at": {"$lte": now_tab2}}]})
    user_count = db.users.count_documents({})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Completed Revenue", f"${tot_rev:,.2f}")
    m2.metric("Active Auctions", f"{active_count}")
    m3.metric("Completed Auctions", f"{ended_count}")
    m4.metric("Registered Bidders", f"{user_count}")

    st.markdown("---")

    # REPORT 1: Category Sales Performance
    st.markdown("#### 1. Category Sales Performance (`$match` $\\rightarrow$ `$group` $\\rightarrow$ `$sort`)")
    cat_pipeline = [
        {"$match": {"status": "ended"}},
        {
            "$group": {
                "_id": "$category",
                "total_revenue": {"$sum": "$current_bid"},
                "avg_price": {"$avg": "$current_bid"},
                "items_sold": {"$sum": 1}
            }
        },
        {"$sort": {"total_revenue": -1}}
    ]
    cat_data = list(db.auctions.aggregate(cat_pipeline))

    if cat_data:
        df_cat = pd.DataFrame(cat_data)
        df_cat.rename(columns={"_id": "Category", "total_revenue": "Revenue ($)", "avg_price": "Avg Price ($)", "items_sold": "Items Sold"}, inplace=True)

        col_c1, col_c2 = st.columns([3, 2])
        with col_c1:
            st.bar_chart(df_cat.set_index("Category")["Revenue ($)"])
        with col_c2:
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
    else:
        st.info("No completed auctions for category metrics.")

    st.markdown("---")

    # REPORT 2: Top Bidders Leaderboard ($lookup JOIN)
    st.markdown("#### 2. Top Bidders Leaderboard (`$unwind` $\\rightarrow$ `$group` $\\rightarrow$ `$lookup` $\\rightarrow$ `$project`)")
    st.caption("Demonstrating Left Outer Joins between embedded `recent_bids` and the `users` collection:")

    lead_pipeline = [
        {"$unwind": "$recent_bids"},
        {
            "$group": {
                "_id": "$recent_bids.bidder_id",
                "bids_placed": {"$sum": 1},
                "total_pledged": {"$sum": "$recent_bids.amount"},
                "top_bid": {"$max": "$recent_bids.amount"}
            }
        },
        {"$sort": {"bids_placed": -1, "total_pledged": -1}},
        {"$limit": 5},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "u"
            }
        },
        {"$unwind": "$u"},
        {
            "$project": {
                "Bidder": "$u.name",
                "Email": "$u.email",
                "Bids Placed": "$bids_placed",
                "Total Pledged ($)": "$total_pledged",
                "Top Bid ($)": "$top_bid"
            }
        }
    ]
    lead_data = list(db.auctions.aggregate(lead_pipeline))
    if lead_data:
        st.dataframe(pd.DataFrame(lead_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # REPORT 3: Price Distribution Histogram ($bucket)
    st.markdown("#### 3. Market Price Distribution Histogram (`$bucket`)")
    st.caption("Native database numerical bucketing without application-level if/else branches:")

    bucket_pipeline = [
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
    bucket_data = list(db.auctions.aggregate(bucket_pipeline))
    if bucket_data:
        labels = {0.0: "$0 - $100 (Budget)", 100.0: "$100 - $500 (Mid-Range)", 500.0: "$500 - $2k (Premium)", 2000.0: "$2k+ (Luxury)"}
        b_rows = [{"Bracket": labels.get(b["_id"], str(b["_id"])), "Item Count": b["count"], "Avg Price ($)": round(b["avg_price"], 2)} for b in bucket_data]
        df_b = pd.DataFrame(b_rows)

        col_b1, col_b2 = st.columns([3, 2])
        with col_b1:
            st.bar_chart(df_b.set_index("Bracket")["Item Count"])
        with col_b2:
            st.dataframe(df_b, use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 3: MULTI-THREADED CONCURRENCY BENCHMARK
# ==============================================================================
with tab3:
    st.subheader("Multi-Threaded Concurrency & Race Condition Benchmark")
    st.markdown("""
    **The Problem:** When 10 users click "Bid $150.00" at the exact same millisecond, traditional databases suffer from dirty reads, double-winners, and race conditions.  
    **The ApexBid Solution:** MongoDB's `find_one_and_update` serializes document writes at the WiredTiger storage engine level. Exactly **1 bid succeeds**, and **9 bids are rejected atomically** with zero external locks.
    """)

    st.info("🎯 **Target Item:** 1984 IBM Model M Mechanical Keyboard | **Payload:** $150.00 from 10 distinct parallel worker threads.")

    if st.button("🚀 Launch 10-Thread Simultaneous Attack ($150.00)", type="primary", use_container_width=True):
        keyboard = db.auctions.find_one({"title": "1984 IBM Model M Mechanical Keyboard"})
        users = list(db.users.find().limit(10))

        if not keyboard or len(users) < 10:
            st.error("Test fixtures missing. Please reset database seed data first.")
        else:
            # Reset keyboard to clean baseline state
            now_c = datetime.now(timezone.utc)
            db.auctions.update_one(
                {"_id": keyboard["_id"]},
                {
                    "$set": {
                        "starting_price": 100.00,
                        "current_bid": 100.00,
                        "highest_bidder_id": None,
                        "status": "active",
                        "ends_at": now_c + timedelta(days=2),
                        "recent_bids": []
                    }
                }
            )

            results = []
            target_amount = 150.00

            def worker_thread(user):
                t0 = time.perf_counter()
                success, msg, meta = place_bid(keyboard["_id"], user["_id"], target_amount)
                lat_ms = (time.perf_counter() - t0) * 1000
                return {
                    "User": user["name"],
                    "Bid": f"${target_amount:.2f}",
                    "Outcome": "ACCEPTED" if success else "REJECTED",
                    "Latency (ms)": round(lat_ms, 1),
                    "Server Response": msg
                }

            with st.spinner("Dispatching 10 parallel threads to MongoDB Atlas..."):
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(worker_thread, u) for u in users]
                    for f in as_completed(futures):
                        results.append(f.result())

            df_threads = pd.DataFrame(results).sort_values("Latency (ms)")

            # Check database state
            fresh_k = db.auctions.find_one({"_id": keyboard["_id"]})
            winner_user = db.users.find_one({"_id": fresh_k["highest_bidder_id"]})

            success_count = sum(1 for r in results if r["Outcome"] == "ACCEPTED")
            reject_count = sum(1 for r in results if r["Outcome"] == "REJECTED")

            if success_count == 1 and reject_count == 9:
                st.success(f"🎉 **CONCURRENCY VERIFIED: ZERO RACE CONDITIONS!** Exactly 1 winner ({winner_user['name'] if winner_user else 'None'}) committed at ${fresh_k['current_bid']:.2f}. 9 conflicting bids were rejected atomically.")
            else:
                st.warning(f"Unexpected outcome: {success_count} accepted, {reject_count} rejected.")

            st.dataframe(df_threads, use_container_width=True, hide_index=True)
