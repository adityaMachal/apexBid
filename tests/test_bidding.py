"""
tests/test_bidding.py
Unit and edge-case verification for the ApexBid atomic bidding engine.
Uses standard Pytest asserts and fixtures.
"""

from datetime import datetime, timezone
import pytest
from bidding_engine import place_bid


class TestBiddingEngine:
    """Test suite verifying all 8 business logic guards and edge cases."""

    def test_standard_valid_bid(self, clean_keyboard_auction, users):
        """Test 1: Valid bid above current highest bid by more than minimum increment."""
        auction = clean_keyboard_auction
        bidder = users["charlie"]

        success, msg, meta = place_bid(auction["_id"], bidder["_id"], 135.00)

        assert success is True
        assert meta["current_bid"] == 135.00
        assert "highest bid" in msg.lower()

    def test_micro_bidding_rejected(self, clean_keyboard_auction, users):
        """Test 2: Bid increment too low (+$1.00 when minimum increment is +$5.00)."""
        auction = clean_keyboard_auction
        bidder = users["diana"]

        # Current bid is $120.00 -> Required minimum is $125.00
        success, msg, meta = place_bid(auction["_id"], bidder["_id"], 121.00)

        assert success is False
        assert meta["error_code"] == "MIN_INCREMENT_NOT_MET"
        assert meta["required_min"] == 125.00

    def test_self_outbidding_rejected(self, clean_keyboard_auction, users):
        """Test 3: Highest bidder cannot bid against themselves."""
        auction = clean_keyboard_auction
        bidder = users["bob"]  # Bob is already highest bidder in fixture

        success, msg, meta = place_bid(auction["_id"], bidder["_id"], 150.00)

        assert success is False
        assert meta["error_code"] == "ALREADY_HIGHEST_BIDDER"

    def test_shill_bidding_rejected(self, clean_keyboard_auction, users):
        """Test 4: Seller cannot bid on their own auction."""
        auction = clean_keyboard_auction
        seller = users["alice"]  # Alice is the seller

        success, msg, meta = place_bid(auction["_id"], seller["_id"], 150.00)

        assert success is False
        assert meta["error_code"] == "SHILL_BIDDING_DISALLOWED"

    def test_insufficient_funds_rejected(self, clean_keyboard_auction, users):
        """Test 5: Bidder cannot bid more than their wallet balance."""
        auction = clean_keyboard_auction
        charlie = users["charlie"]  # Balance is $450.00

        success, msg, meta = place_bid(auction["_id"], charlie["_id"], 1000.00)

        assert success is False
        assert meta["error_code"] == "INSUFFICIENT_FUNDS"

    def test_anti_sniping_soft_close_extension(self, anti_snipe_auction, users):
        """Test 6: Bidding within 120 seconds of deadline automatically extends it by 180s."""
        auction = anti_snipe_auction
        bidder = users["ethan"]  # Diana is seller, Ethan is valid bidder
        original_end = auction["ends_at"]
        if original_end.tzinfo is None:
            original_end = original_end.replace(tzinfo=timezone.utc)

        success, msg, meta = place_bid(auction["_id"], bidder["_id"], 1450.00)

        assert success is True
        assert meta["extended"] is True

        new_end = meta["new_ends_at"]
        if new_end.tzinfo is None:
            new_end = new_end.replace(tzinfo=timezone.utc)

        assert new_end > original_end
        assert "anti-snipe triggered" in msg.lower()

    def test_expired_auction_rejected(self, database, users):
        """Test 7: Bids placed on expired auctions must be rejected."""
        ended_item = database.auctions.find_one({"status": "ended"})
        assert ended_item, "Ended auction fixture missing!"

        # Diana has $5,200 balance, so wallet check passes and expiration check is tested
        bidder = users["diana"]
        success, msg, meta = place_bid(ended_item["_id"], bidder["_id"], 200.00)

        assert success is False
        assert meta["error_code"] in ["AUCTION_NOT_ACTIVE", "AUCTION_EXPIRED"]

    def test_lower_bid_rejected(self, clean_keyboard_auction, users):
        """Test 8: Bids lower than the current highest bid must be rejected."""
        auction = clean_keyboard_auction
        bidder = users["charlie"]

        # Current bid is $120.00
        success, msg, meta = place_bid(auction["_id"], bidder["_id"], 80.00)

        assert success is False
        assert meta["error_code"] == "MIN_INCREMENT_NOT_MET"
