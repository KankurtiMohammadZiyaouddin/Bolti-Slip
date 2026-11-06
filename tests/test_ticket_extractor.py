"""
tests/test_ticket_extractor.py
--------------------------------
Unit tests for backend.services.ticket_extractor.TicketExtractor.

All 8 required scenarios are covered.
No real Gnani API calls are made — this tests extraction logic only.

Run with:
    cd C:\\Programs\\Project\\Bolti-Slip
    .venv\\Scripts\\python.exe -m pytest tests/test_ticket_extractor.py -v
"""

from __future__ import annotations

import sys
import os
from datetime import date

# Allow running from project root without installing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.services.ticket_extractor import TicketExtractor

EXTRACTOR = TicketExtractor()
TODAY = date(2025, 11, 6)   # Thursday — fixed so tests are deterministic


# ---------------------------------------------------------------------------
# Test 1: Hindi repair request
# ---------------------------------------------------------------------------
def test_hindi_repair_request():
    transcript = "भाई, मेरा mixer grinder खराब हो गया है। इसे Friday तक ठीक करके देना।"
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["device_description"] is not None, "device_description should be extracted"
    assert "Mixer" in f["device_description"] or "mixer" in f["device_description"].lower()
    assert f["reported_problem"] is not None, "problem should be extracted"
    assert f["expected_delivery"] is not None, "Friday delivery should be extracted"
    # Friday (weekday 4). TODAY is Thursday (weekday 3). days_ahead = (4-3)%7 = 1 → 2025-11-07
    assert f["expected_delivery"] == "2025-11-07"
    # Friday is a named weekday → needs_confirmation
    assert "expected_delivery" in result["needs_confirmation"]
    # No phone, no cost given
    assert f["customer_phone"] is None
    assert f["estimated_cost"] is None


# ---------------------------------------------------------------------------
# Test 2: English repair request
# ---------------------------------------------------------------------------
def test_english_repair_request():
    transcript = "My laptop is not working, the screen is completely blank. Please fix it."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["device_description"] == "Laptop"
    assert f["reported_problem"] is not None
    assert "blank" in f["reported_problem"].lower() or "not working" in f["reported_problem"].lower()
    assert f["customer_phone"] is None
    assert f["estimated_cost"] is None
    assert "customer_name" in result["missing_fields"]


# ---------------------------------------------------------------------------
# Test 3: Hinglish repair request
# ---------------------------------------------------------------------------
def test_hinglish_repair_request():
    transcript = "Bhai mera fan band ho gaya hai, please 3 din mein fix kar dena."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["device_description"] == "Fan"
    assert f["reported_problem"] is not None
    # 3 din → today + 3 = 2025-11-09
    assert f["expected_delivery"] == "2025-11-09"
    assert "expected_delivery" not in result["needs_confirmation"]


# ---------------------------------------------------------------------------
# Test 4: Explicit phone number
# ---------------------------------------------------------------------------
def test_explicit_phone_number():
    transcript = "Mera naam Suresh hai, phone number 9876543210. Mera TV kharab hai."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["customer_phone"] == "9876543210"
    assert f["device_description"] == "Television / TV"


# ---------------------------------------------------------------------------
# Test 5: Explicit price / cost
# ---------------------------------------------------------------------------
def test_explicit_cost():
    transcript = "Washing machine repair ka charge ₹850 lagega, aur kal tak de dena."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["device_description"] == "Washing Machine"
    assert f["estimated_cost"] == 850.0
    # "kal" = tomorrow = 2025-11-07
    assert f["expected_delivery"] == "2025-11-07"
    assert "expected_delivery" not in result["needs_confirmation"]


# ---------------------------------------------------------------------------
# Test 6: Ambiguous delivery date (named weekday)
# ---------------------------------------------------------------------------
def test_ambiguous_delivery_date_needs_confirmation():
    transcript = "Refrigerator thanda nahi kar raha hai. Isko Monday tak theek kar dena."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    # Monday (weekday 0). TODAY is Thursday (weekday 3). days_ahead = (0-3)%7 = 4 → 2025-11-10
    assert result["fields"]["expected_delivery"] == "2025-11-10"
    assert "expected_delivery" in result["needs_confirmation"], (
        "Named weekday should be flagged as needs_confirmation"
    )


# ---------------------------------------------------------------------------
# Test 7: No customer information
# ---------------------------------------------------------------------------
def test_no_customer_information():
    transcript = "Printer jam ho gaya hai, paper nahi nikal raha."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    assert result["success"] is True
    f = result["fields"]
    assert f["device_description"] == "Printer"
    assert f["customer_name"] is None
    assert f["customer_phone"] is None
    assert "customer_name" in result["missing_fields"]
    assert "customer_phone" in result["missing_fields"]


# ---------------------------------------------------------------------------
# Test 8: Unknown device
# ---------------------------------------------------------------------------
def test_unknown_device():
    transcript = "Meri chakki kharab hai, please theek kar do."
    result = EXTRACTOR.extract(transcript, today=TODAY)

    # "chakki" is not in device list; fallback_device should provide something
    # and needs_confirmation should flag device_description
    f = result["fields"]
    # Success can be False if even fallback doesn't work — that's acceptable
    if result["success"]:
        assert "device_description" in result["needs_confirmation"]
    else:
        assert f["device_description"] is None
        assert "device_description" in result["missing_fields"]


# ---------------------------------------------------------------------------
# Extra: cost from Hindi number words
# ---------------------------------------------------------------------------
def test_hindi_cost_word():
    transcript = "Fan ki repair ka paanch sau rupaye lagega."
    result = EXTRACTOR.extract(transcript, today=TODAY)
    assert result["fields"]["estimated_cost"] == 500.0


# ---------------------------------------------------------------------------
# Extra: Rs. prefix cost
# ---------------------------------------------------------------------------
def test_rs_prefix_cost():
    transcript = "Mobile screen broken, repair charges Rs. 1,200."
    result = EXTRACTOR.extract(transcript, today=TODAY)
    assert result["fields"]["estimated_cost"] == 1200.0


# ---------------------------------------------------------------------------
# Extra: "day after tomorrow"
# ---------------------------------------------------------------------------
def test_day_after_tomorrow():
    transcript = "Laptop keyboard not working, give it back day after tomorrow."
    result = EXTRACTOR.extract(transcript, today=TODAY)
    # day after tomorrow = today + 2 = 2025-11-08
    assert result["fields"]["expected_delivery"] == "2025-11-08"
    assert "expected_delivery" not in result["needs_confirmation"]


# ---------------------------------------------------------------------------
# Extra: transcript_raw is always preserved
# ---------------------------------------------------------------------------
def test_transcript_raw_preserved():
    transcript = "Fan kharab hai."
    result = EXTRACTOR.extract(transcript, today=TODAY)
    assert result["fields"]["transcript_raw"] == transcript


# ---------------------------------------------------------------------------
# Extra: repair_instructions never inferred from problem alone
# ---------------------------------------------------------------------------
def test_repair_instructions_not_inferred():
    transcript = "Mera TV on nahi ho raha hai."
    result = EXTRACTOR.extract(transcript, today=TODAY)
    # Extractor must NOT invent repair instructions
    assert result["fields"]["repair_instructions"] is None, (
        "repair_instructions must remain null unless explicitly stated"
    )
