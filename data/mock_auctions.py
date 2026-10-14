"""
data/mock_auctions.py
Contains 18 diverse auction listings across 4 categories.
Includes special test cases for anti-sniping and ended auctions for analytics.
"""

from datetime import datetime, timedelta, timezone


def get_mock_auctions(user_ids):
    """
    Returns a list of 18 auction documents ready for insert_many().

    Args:
        user_ids: List of 10 ObjectIds from the inserted users.
                  Index mapping: [0]=Alice, [1]=Bob, [2]=Charlie, [3]=Diana,
                  [4]=Ethan, [5]=Fiona, [6]=George, [7]=Hannah, [8]=Ian, [9]=Julia
    """

    now = datetime.now(timezone.utc)

    # Sellers (3 users who list items)
    seller_alice = user_ids[0]
    seller_diana = user_ids[3]
    seller_ian   = user_ids[8]

    return [
        # ===================== Category: Electronics =====================
        {
            "title": "1984 IBM Model M Mechanical Keyboard",
            "category": "Electronics",
            "seller_id": seller_alice,
            "starting_price": 50.00,
            "current_bid": 120.00,
            "highest_bidder_id": user_ids[1],   # Bob
            "status": "active",
            "ends_at": now + timedelta(days=2),
            "recent_bids": [
                {"bidder_id": user_ids[1], "amount": 120.00, "timestamp": now - timedelta(hours=2)},
                {"bidder_id": user_ids[2], "amount": 90.00,  "timestamp": now - timedelta(hours=5)}
            ]
        },
        {
            "title": "Sony Alpha A7 III Mirrorless Camera",
            "category": "Electronics",
            "seller_id": seller_alice,
            "starting_price": 800.00,
            "current_bid": 950.00,
            "highest_bidder_id": user_ids[4],   # Ethan
            "status": "active",
            "ends_at": now + timedelta(days=3),
            "recent_bids": [
                {"bidder_id": user_ids[4], "amount": 950.00, "timestamp": now - timedelta(hours=1)}
            ]
        },
        {
            "title": "Sennheiser HD 650 Reference Headphones",
            "category": "Electronics",
            "seller_id": seller_ian,
            "starting_price": 150.00,
            "current_bid": 150.00,
            "highest_bidder_id": None,          # No bids yet
            "status": "active",
            "ends_at": now + timedelta(days=1),
            "recent_bids": []
        },
        {
            "title": "Apple Macintosh Classic (1990, Working)",
            "category": "Electronics",
            "seller_id": seller_alice,
            "starting_price": 200.00,
            "current_bid": 340.00,
            "highest_bidder_id": user_ids[6],   # George
            "status": "active",
            "ends_at": now + timedelta(hours=18),
            "recent_bids": [
                {"bidder_id": user_ids[6], "amount": 340.00, "timestamp": now - timedelta(minutes=45)}
            ]
        },

        # ===================== Category: Collectibles =====================
        {
            "title": "First Edition Holographic Charizard (PSA 8)",
            "category": "Collectibles",
            "seller_id": seller_diana,
            "starting_price": 1200.00,
            "current_bid": 1850.00,
            "highest_bidder_id": user_ids[8],   # Ian
            "status": "active",
            "ends_at": now + timedelta(days=4),
            "recent_bids": [
                {"bidder_id": user_ids[8], "amount": 1850.00, "timestamp": now - timedelta(hours=3)},
                {"bidder_id": user_ids[1], "amount": 1600.00, "timestamp": now - timedelta(hours=8)}
            ]
        },
        {
            "title": "Original 1977 Star Wars Movie Poster",
            "category": "Collectibles",
            "seller_id": seller_diana,
            "starting_price": 100.00,
            "current_bid": 220.00,
            "highest_bidder_id": user_ids[5],   # Fiona
            "status": "active",
            "ends_at": now + timedelta(days=1),
            "recent_bids": [
                {"bidder_id": user_ids[5], "amount": 220.00, "timestamp": now - timedelta(hours=6)}
            ]
        },
        {
            "title": "Autographed Apollo 11 Mission Patch",
            "category": "Collectibles",
            "seller_id": seller_ian,
            "starting_price": 500.00,
            "current_bid": 500.00,
            "highest_bidder_id": None,          # No bids yet
            "status": "active",
            "ends_at": now + timedelta(days=3),
            "recent_bids": []
        },

        # ===================== Category: Gaming =====================
        {
            "title": "Nintendo 64 Atomic Purple Console Complete In Box",
            "category": "Gaming",
            "seller_id": seller_alice,
            "starting_price": 80.00,
            "current_bid": 145.00,
            "highest_bidder_id": user_ids[2],   # Charlie
            "status": "active",
            "ends_at": now + timedelta(days=2),
            "recent_bids": [
                {"bidder_id": user_ids[2], "amount": 145.00, "timestamp": now - timedelta(hours=4)}
            ]
        },
        {
            "title": "Cyberpunk 2077 Collector's Edition Statue",
            "category": "Gaming",
            "seller_id": seller_ian,
            "starting_price": 60.00,
            "current_bid": 95.00,
            "highest_bidder_id": user_ids[7],   # Hannah
            "status": "active",
            "ends_at": now + timedelta(hours=12),
            "recent_bids": [
                {"bidder_id": user_ids[7], "amount": 95.00, "timestamp": now - timedelta(hours=1)}
            ]
        },
        {
            "title": "Custom Mechanical Game Boy Advance (IPS V2 Screen)",
            "category": "Gaming",
            "seller_id": seller_alice,
            "starting_price": 110.00,
            "current_bid": 180.00,
            "highest_bidder_id": user_ids[9],   # Julia
            "status": "active",
            "ends_at": now + timedelta(days=1),
            "recent_bids": [
                {"bidder_id": user_ids[9], "amount": 180.00, "timestamp": now - timedelta(hours=10)}
            ]
        },

        # ===================== Category: Watches =====================
        {
            "title": "Omega Seamaster Professional 300M (Vintage 1998)",
            "category": "Watches",
            "seller_id": seller_diana,
            "starting_price": 1500.00,
            "current_bid": 2100.00,
            "highest_bidder_id": user_ids[4],   # Ethan
            "status": "active",
            "ends_at": now + timedelta(days=5),
            "recent_bids": [
                {"bidder_id": user_ids[4], "amount": 2100.00, "timestamp": now - timedelta(hours=1)}
            ]
        },
        {
            "title": "Seiko SKX007 Automatic Diver Watch",
            "category": "Watches",
            "seller_id": seller_ian,
            "starting_price": 200.00,
            "current_bid": 275.00,
            "highest_bidder_id": user_ids[6],   # George
            "status": "active",
            "ends_at": now + timedelta(hours=6),
            "recent_bids": [
                {"bidder_id": user_ids[6], "amount": 275.00, "timestamp": now - timedelta(hours=2)}
            ]
        },

        # ========== ANTI-SNIPING TEST: Ends in 90 seconds! ==========
        {
            "title": "RTX 4090 Founders Edition GPU",
            "category": "Electronics",
            "seller_id": seller_diana,
            "starting_price": 1000.00,
            "current_bid": 1400.00,
            "highest_bidder_id": user_ids[1],   # Bob
            "status": "active",
            "ends_at": now + timedelta(seconds=90),  # Inside 2-min anti-snipe window!
            "recent_bids": [
                {"bidder_id": user_ids[1], "amount": 1400.00, "timestamp": now - timedelta(seconds=30)}
            ]
        },

        # ========== ANTI-SNIPING TEST: Ends in 45 seconds! ==========
        {
            "title": "Signed Lionel Messi 2022 World Cup Jersey",
            "category": "Collectibles",
            "seller_id": seller_ian,
            "starting_price": 500.00,
            "current_bid": 850.00,
            "highest_bidder_id": user_ids[3],   # Diana
            "status": "active",
            "ends_at": now + timedelta(seconds=45),  # Inside 2-min anti-snipe window!
            "recent_bids": [
                {"bidder_id": user_ids[3], "amount": 850.00, "timestamp": now - timedelta(seconds=20)}
            ]
        },

        # ========== ENDED AUCTIONS (For Phase 5 Analytics) ==========
        {
            "title": "Sony PlayStation 1 (Original 1994 Model)",
            "category": "Gaming",
            "seller_id": seller_alice,
            "starting_price": 40.00,
            "current_bid": 95.00,
            "highest_bidder_id": user_ids[2],   # Charlie
            "status": "ended",
            "ends_at": now - timedelta(days=2),
            "recent_bids": [
                {"bidder_id": user_ids[2], "amount": 95.00, "timestamp": now - timedelta(days=2, hours=1)}
            ]
        },
        {
            "title": "Vintage Leica M3 Rangefinder 35mm Film Camera",
            "category": "Electronics",
            "seller_id": seller_diana,
            "starting_price": 900.00,
            "current_bid": 1450.00,
            "highest_bidder_id": user_ids[4],   # Ethan
            "status": "ended",
            "ends_at": now - timedelta(days=1),
            "recent_bids": [
                {"bidder_id": user_ids[4], "amount": 1450.00, "timestamp": now - timedelta(days=1, hours=3)}
            ]
        },
        {
            "title": "Rolex Submariner Date (1985 Reference 16800)",
            "category": "Watches",
            "seller_id": seller_ian,
            "starting_price": 6000.00,
            "current_bid": 8200.00,
            "highest_bidder_id": user_ids[3],   # Diana
            "status": "ended",
            "ends_at": now - timedelta(days=3),
            "recent_bids": [
                {"bidder_id": user_ids[3], "amount": 8200.00, "timestamp": now - timedelta(days=3, hours=2)}
            ]
        },
    ]
