"""
backend/services/ticket_extractor.py
--------------------------------------
Pure-Python rule-based extractor that parses a repair-shop transcript
(Hindi / English / Hinglish) and returns structured ticket fields.

Design principles
-----------------
- No external AI APIs.  No network calls.  No imports beyond stdlib.
- Never invent data: if a fact is not explicitly present, return None.
- Ambiguous relative dates (e.g. "Friday") are flagged in
  ``needs_confirmation`` rather than silently resolved.
- Confidence score is not claimed (rule-based extraction does not
  produce a calibrated probability).

Usage
-----
    from backend.services.ticket_extractor import TicketExtractor
    result = TicketExtractor().extract("मेरा mixer grinder खराब है")
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Constants — all in one place for easy maintenance
# ---------------------------------------------------------------------------

# Supported devices: (canonical English name, list of trigger patterns)
# Patterns are matched case-insensitively against the normalised transcript.
# IMPORTANT: "Television / TV" comes before "Mobile / Phone" so that "TV"
#            matches before the word "phone" does in "phone number … TV".
_DEVICE_PATTERNS: list[tuple[str, list[str]]] = [
    ("Television / TV",  [
        r"\btelevision\b", r"\btv\b", r"\bled\s+tv\b", r"\blcd\s+tv\b",
        r"\bटीवी\b", r"\bटेलीविजन\b",
    ]),
    ("Laptop",           [
        r"\blaptop\b", r"\bnotebook\b", r"\bmacbook\b",
        r"\bलैपटॉप\b",
    ]),
    ("Computer / PC",    [
        r"\bcomputer\b", r"\bpc\b", r"\bdesktop\b", r"\bcpu\b",
        r"\bकंप्यूटर\b", r"\bकम्प्यूटर\b",
    ]),
    ("Mixer Grinder",    [
        r"\bmixer\s+grinder\b", r"\bmixer-grinder\b",
        r"\bमिक्सर\s+ग्राइंडर\b", r"\bमिक्सर-ग्राइंडर\b",
        r"\bमिक्सर\b",
        r"\bmixer\b",
    ]),
    ("Fan",              [
        r"\bfan\b", r"\bceiling\s+fan\b", r"\btable\s+fan\b",
        r"\bपंखा\b", r"\bफैन\b",
    ]),
    ("Refrigerator / Fridge", [
        r"\brefrigerator\b", r"\bfridge\b",
        r"\bफ्रिज\b", r"\bरेफ्रिजरेटर\b",
    ]),
    ("Washing Machine",  [
        r"\bwashing\s+machine\b",
        r"\bवाशिंग\s+मशीन\b", r"\bधुलाई\s+मशीन\b",
    ]),
    ("Printer",          [
        r"\bprinter\b", r"\binkjet\b", r"\blaser\s+printer\b",
        r"\bप्रिंटर\b",
    ]),
    ("Iron",             [
        r"\biron\b", r"\bsteam\s+iron\b",
        r"\bआयरन\b", r"\bप्रेस\b",
    ]),
    ("Water Pump",       [
        r"\bwater\s+pump\b", r"\bpump\b",
        r"\bवाटर\s+पंप\b", r"\bपंप\b",
    ]),
    ("Geyser / Water Heater", [
        r"\bgeyser\b", r"\bwater\s+heater\b",
        r"\bगीज़र\b", r"\bगीजर\b",
    ]),
    ("Air Conditioner",  [
        r"\bair\s+conditioner\b", r"\bac\b", r"\ba\.c\.\b",
        r"\bएयर\s+कंडीशनर\b",
    ]),
    ("Juicer",           [
        r"\bjuicer\b", r"\bजूसर\b",
    ]),
    ("Microwave",        [
        r"\bmicrowave\b", r"\bमाइक्रोवेव\b",
    ]),
    ("Toaster",          [
        r"\btoaster\b", r"\bटोस्टर\b",
    ]),
    ("Vacuum Cleaner",   [
        r"\bvacuum\s+cleaner\b", r"\bvacuum\b",
        r"\bवैक्यूम\b",
    ]),
    # Mobile / Phone comes LAST so "phone number" does not shadow a TV/laptop etc.
    ("Mobile / Phone",   [
        r"\bmobile\b", r"\bsmartphone\b", r"\bhandset\b",
        r"\biphone\b",  r"\bandroid\b",
        r"\bमोबाइल\b", r"\bफ़ोन\b", r"\bफोन\b",
        # "phone" only when NOT part of "phone number"
        r"\bphone\b(?!\s+number)",
    ]),
]

# Problem keywords that indicate a fault description rather than device name
_PROBLEM_INDICATORS: list[str] = [
    # English
    r"not working", r"doesn'?t work", r"won'?t turn on", r"not charging",
    r"not switching on", r"overheating", r"making noise", r"making sound",
    r"no sound", r"no display", r"blank screen", r"cracked screen",
    r"broken screen", r"battery", r"water damage", r"short circuit",
    r"burning smell", r"smoke", r"sparks?", r"leaking",
    r"not heating", r"not cooling",
    # Hindi / Hinglish
    r"खराब", r"kharab", r"बंद", r"band", r"nahi\s+chal", r"नहीं चल", r"चालू नहीं", r"chalu\s+nahi",
    r"on\s+nahi", r"start\s+nahi", r"garam\s+ho", r"गर्म हो",
    r"आवाज़", r"आवाज", r"awaaz", r"awaz", r"धुआं", r"धुआ", r"जल गया", r"jal\s+gaya", r"टूट गया",
    r"toot\s+gaya", r"tut\s+gaya", r"टूट गई", r"टूटा", r"toota", r"पानी गया", r"pani\s+gaya",
    r"लीक", r"leak", r"शोर", r"shor",
    r"बटन\s+काम\s+नहीं", r"बटन\s+नहीं\s+चल", r"button\s+kaam\s+nahi",
    r"thanda\s+nahi", r"thanda\s+नहीं",
    r"paper\s+nahi", r"jam",
]

# Cost patterns: match "rupees 500", "500 rs", "₹500", "5 sau", "paanch sau"
_COST_PATTERNS: list[re.Pattern[str]] = [
    # ₹500 or Rs 500 or Rs. 500
    re.compile(r"₹\s*(\d[\d,]*(?:\.\d{1,2})?)", re.IGNORECASE),
    re.compile(r"\brs\.?\s*(\d[\d,]*(?:\.\d{1,2})?)", re.IGNORECASE),
    re.compile(r"\b(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rs\.?|rupees?|rupaye?|rupay|rupai|rupiya|रुपये|रुपए|रू\.?)\b", re.IGNORECASE),
    # "500 bucks" colloquial
    re.compile(r"\b(\d[\d,]*)\s*bucks?\b", re.IGNORECASE),
]

# Hindi number words for round hundreds / thousands (simple cases only)
_HINDI_NUMBER_WORDS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\bpaaanch\s+sau\b", re.IGNORECASE), 500),
    (re.compile(r"\bpaanch\s+sau\b",  re.IGNORECASE), 500),
    (re.compile(r"\bpanch\s+sau\b",   re.IGNORECASE), 500),
    (re.compile(r"\bpanch\s+so\b",    re.IGNORECASE), 500),
    (re.compile(r"\bteen\s+sau\b",    re.IGNORECASE), 300),
    (re.compile(r"\bchar\s+sau\b",    re.IGNORECASE), 400),
    (re.compile(r"\bchheh\s+sau\b",   re.IGNORECASE), 600),
    (re.compile(r"\bsaat\s+sau\b",    re.IGNORECASE), 700),
    (re.compile(r"\bathh?\s+sau\b",   re.IGNORECASE), 800),
    (re.compile(r"\bnau\s+sau\b",     re.IGNORECASE), 900),
    (re.compile(r"\bek\s+hazar\b",    re.IGNORECASE), 1000),
    (re.compile(r"\bdo\s+hazar\b",    re.IGNORECASE), 2000),
    (re.compile(r"\bteen\s+hazar\b",  re.IGNORECASE), 3000),
    (re.compile(r"\bpanch\s+hazar\b", re.IGNORECASE), 5000),
    (re.compile(r"\bदो\s+सौ\b",       re.IGNORECASE), 200),
    (re.compile(r"\bतीन\s+सौ\b",      re.IGNORECASE), 300),
    (re.compile(r"\bचार\s+सौ\b",      re.IGNORECASE), 400),
    (re.compile(r"\bपाँच\s+सौ\b",     re.IGNORECASE), 500),
    (re.compile(r"\bछह\s+सौ\b",       re.IGNORECASE), 600),
    (re.compile(r"\bसात\s+सौ\b",      re.IGNORECASE), 700),
    (re.compile(r"\bआठ\s+सौ\b",       re.IGNORECASE), 800),
    (re.compile(r"\bनौ\s+सौ\b",       re.IGNORECASE), 900),
    (re.compile(r"\bएक\s+हज़ार\b",     re.IGNORECASE), 1000),
    (re.compile(r"\bदो\s+हज़ार\b",     re.IGNORECASE), 2000),
]

# Phone number: 10-digit Indian mobile (may have country code prefix)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?91[-\s]?)?([6-9]\d{9})(?!\d)"
)

# Delivery day names → weekday index (Mon=0 … Sun=6)
_DAY_OF_WEEK: dict[str, int] = {
    "monday": 0, "सोमवार": 0, "सोम": 0,
    "tuesday": 1, "मंगलवार": 1, "मंगल": 1,
    "wednesday": 2, "बुधवार": 2, "बुध": 2,
    "thursday": 3, "गुरुवार": 3, "गुरु": 3, "वीरवार": 3,
    "friday": 4, "शुक्रवार": 4, "शुक्र": 4,
    "saturday": 5, "शनिवार": 5, "शनि": 5,
    "sunday": 6, "रविवार": 6, "रवि": 6,
}

# Relative date phrases → day offset.
# IMPORTANT: sorted longest-first so "day after tomorrow" is matched
# before "tomorrow" (which is a substring of the longer phrase).
_RELATIVE_DAY_EXACT: list[tuple[str, int]] = sorted(
    [
        ("today", 0),     ("aaj", 0),     ("आज", 0),
        ("tomorrow", 1),  ("kal", 1),     ("कल", 1),
        ("day after tomorrow", 2), ("parson", 2), ("परसों", 2), ("परसो", 2),
    ],
    key=lambda x: len(x[0]),
    reverse=True,  # longest phrase first → prevents "tomorrow" shadowing "day after tomorrow"
)

# "2-3 din mein", "teen din mein", etc.
_DAYS_FROM_NOW_RE = re.compile(
    r"(\d+)\s*(?:din|days?|दिन)\s*(?:mein|में|me|baad|बाद)?",
    re.IGNORECASE
)

# Sentence splitter (used to separate device sentence from problem sentence)
_SENTENCE_SPLIT_RE = re.compile(r"[।.!?]\s*")


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------

ExtractionResult = dict[str, Any]
"""
Keys
----
success          : bool
fields           : dict[str, str | float | None]
    customer_name, customer_phone, device_description,
    reported_problem, repair_instructions, expected_delivery,
    estimated_cost, transcript_raw
missing_fields   : list[str]  — fields that are None
needs_confirmation : list[str] — fields where the extracted value is uncertain
unresolved_phrases : list[str] — text fragments that were not mapped
"""


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class TicketExtractor:
    """
    Stateless transcript extractor.  Instantiate once and reuse.

    All extraction is deterministic regex/rule-based.
    No network calls, no AI APIs.
    """

    # Required fields (must be non-null for a complete ticket)
    _REQUIRED = ("device_description",)

    def extract(self, transcript: str, *, today: date | None = None) -> ExtractionResult:
        """
        Parse *transcript* and return an ExtractionResult dict.

        Parameters
        ----------
        transcript : str
            Raw STT output — Hindi, English, or Hinglish.
        today : date, optional
            Reference date for relative day resolution.
            Defaults to ``datetime.date.today()``.
        """
        if today is None:
            today = date.today()

        text = transcript.strip()

        fields: dict[str, Any] = {
            "customer_name":      None,
            "customer_phone":     None,
            "device_description": None,
            "reported_problem":   None,
            "repair_instructions": None,
            "expected_delivery":  None,
            "estimated_cost":     None,
            "transcript_raw":     text,
        }
        needs_confirmation: list[str] = []
        unresolved_phrases: list[str] = []

        # --- 1. Phone number -------------------------------------------------
        phone = _extract_phone(text)
        if phone:
            fields["customer_phone"] = phone

        # --- 2. Device description -------------------------------------------
        # Pass extracted phone so device extractor can mask the phone-number
        # region (prevents "phone number 9876…" from triggering Mobile device).
        device, device_span = _extract_device(text, phone)
        if device:
            fields["device_description"] = device
        else:
            # Fallback: first noun-phrase-ish clause before first problem word
            fallback = _fallback_device(text)
            if fallback:
                fields["device_description"] = fallback
                needs_confirmation.append("device_description")
            else:
                unresolved_phrases.append("device_description")

        # --- 3. Reported problem ---------------------------------------------
        problem = _extract_problem(text, device_span)
        if problem:
            fields["reported_problem"] = problem

        # --- 4. Estimated cost -----------------------------------------------
        cost, cost_unresolved = _extract_cost(text)
        if cost is not None:
            fields["estimated_cost"] = cost
        elif cost_unresolved:
            unresolved_phrases.append(cost_unresolved)

        # --- 5. Expected delivery --------------------------------------------
        delivery, delivery_needs_confirm, delivery_unresolved = _extract_delivery(text, today)
        if delivery:
            fields["expected_delivery"] = delivery
            if delivery_needs_confirm:
                needs_confirmation.append("expected_delivery")
        elif delivery_unresolved:
            unresolved_phrases.append(delivery_unresolved)

        # --- 6. Missing fields -----------------------------------------------
        missing = [
            k for k in (
                "customer_name", "customer_phone", "device_description",
                "reported_problem", "repair_instructions", "expected_delivery", "estimated_cost"
            )
            if fields[k] is None
        ]

        return {
            "success": fields["device_description"] is not None,
            "fields": fields,
            "missing_fields": missing,
            "needs_confirmation": needs_confirmation,
            "unresolved_phrases": unresolved_phrases,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lower-case; normalise Unicode; collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text.lower()).strip()


def _extract_phone(text: str) -> str | None:
    m = _PHONE_RE.search(text)
    return m.group(1) if m else None


def _extract_device(
    text: str, known_phone: str | None = None
) -> tuple[str | None, tuple[int, int] | None]:
    """
    Return (canonical_device_name, (start, end)) for the first matching device.
    span is used by _extract_problem() to skip the device name region.

    If a phone number was already extracted we mask that digit sequence so
    patterns like ``\\bphone\\b`` inside "phone number 9876543210" do not
    trigger the Mobile device before we have a chance to match a later device
    (e.g. TV).
    """
    norm = _normalise(text)

    # Mask the phone-number region so it cannot accidentally match device names
    if known_phone:
        norm = norm.replace(known_phone, " " * len(known_phone))

    # Also mask the phrase "phone number" to avoid matching \bphone\b there
    norm = re.sub(r"\bphone\s+number\b", " " * len("phone number"), norm, flags=re.IGNORECASE)

    for canonical, patterns in _DEVICE_PATTERNS:
        for pat in patterns:
            m = re.search(pat, norm, re.IGNORECASE)
            if m:
                return canonical, (m.start(), m.end())
    return None, None


def _fallback_device(text: str) -> str | None:
    """
    When no known device keyword is found, take the first clause
    (up to the first comma, 'है', '।', or problem indicator) as a
    best-guess device description.  Caller marks this needs_confirmation.
    """
    norm = _normalise(text)
    # Strip greeting words
    norm = re.sub(
        r"^(bhai\s*|yaar\s*|sir\s*|ji\s*|haan\s*|hello\s*|भाई\s*|यार\s*|सर\s*|जी\s*)+",
        "", norm
    ).strip()

    # Cut at first problem indicator
    for indicator in _PROBLEM_INDICATORS:
        m = re.search(indicator, norm, re.IGNORECASE)
        if m:
            candidate = norm[: m.start()].strip().rstrip(",; ")
            if len(candidate) > 2:
                return candidate
    # Cut at comma or clause boundary
    parts = re.split(r"[,।]", norm, maxsplit=1)
    candidate = parts[0].strip()
    if 2 < len(candidate) < 200:
        return candidate
    return None


def _extract_problem(text: str, device_span: tuple[int, int] | None) -> str | None:
    """
    Extract the fault description.  Strategy:
    1. Find the first problem-indicator word.
    2. Grab the clause that contains it.
    3. Avoid echoing the device name verbatim as the problem.
    """
    norm = _normalise(text)

    # Remove device span region from search to avoid "mixer grinder" being
    # the "problem" text.
    if device_span:
        # We search only after the device mention
        search_start = device_span[1]
    else:
        search_start = 0

    best_match_pos = len(norm)
    best_indicator = None

    for indicator in _PROBLEM_INDICATORS:
        m = re.search(indicator, norm[search_start:], re.IGNORECASE)
        if m:
            abs_pos = search_start + m.start()
            if abs_pos < best_match_pos:
                best_match_pos = abs_pos
                best_indicator = m

    if best_indicator is None:
        # Retry from position 0 in case device_span pushed search_start too far
        for indicator in _PROBLEM_INDICATORS:
            m = re.search(indicator, norm, re.IGNORECASE)
            if m:
                abs_pos = m.start()
                if abs_pos < best_match_pos:
                    best_match_pos = abs_pos
                    best_indicator = m

    if best_indicator is None:
        return None

    # Extend the problem clause to end of sentence
    abs_start = best_match_pos
    # Find sentence / clause boundary after the indicator
    after = norm[abs_start:]
    sentence_end = re.search(r"[,।.!?]|\b(?:please|isko|ise|इसे|इसको|aur|और)\b", after)
    if sentence_end:
        clause = after[: sentence_end.start()].strip()
    else:
        clause = after.strip()

    # Clean up: remove leading conjunctions/particles
    clause = re.sub(
        r"^(aur|aur\s*bhi|or|,\s*|और\s*|भी\s*|है\s*|ko\s*|को\s*)", "", clause, flags=re.IGNORECASE
    ).strip()

    if len(clause) < 2:
        return None

    # Capitalise first letter for English phrases
    if re.match(r"[a-zA-Z]", clause):
        clause = clause[0].upper() + clause[1:]

    return clause or None


def _extract_cost(text: str) -> tuple[float | None, str | None]:
    """
    Return (amount, None) if found, or (None, unresolved_phrase) if
    a cost keyword is present but unparseable.
    """
    # Try numeric patterns first
    for pat in _COST_PATTERNS:
        m = pat.search(text)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                return float(raw), None
            except ValueError:
                pass

    # Try Hindi number words
    norm = _normalise(text)
    for pat, value in _HINDI_NUMBER_WORDS:
        # Only return if it's near a currency word
        if pat.search(norm):
            context = norm
            if re.search(r"rupee|rupay|rupai|rs|₹|रुपये|रुपए|रूपए|paisa|paise|charge|cost|lagega|lagenge", context, re.IGNORECASE):
                return value, None

    # Check whether a cost was implied but unextractable
    if re.search(r"rupee|rupay|rs\.?|₹|रुपये|रुपए|charge|cost|lagega", text, re.IGNORECASE):
        return None, "estimated_cost (cost word found but amount unclear)"

    return None, None


def _extract_delivery(
    text: str, today: date
) -> tuple[str | None, bool, str | None]:
    """
    Return (iso_date_str, needs_confirmation, unresolved_phrase).

    needs_confirmation=True when the phrase is a named weekday
    (we cannot know *which* upcoming occurrence is intended without asking).
    """
    norm = _normalise(text)

    # 1. Exact relative days (today, tomorrow, day after tomorrow)
    #    _RELATIVE_DAY_EXACT is sorted longest-first to prevent "tomorrow"
    #    matching inside "day after tomorrow".
    for phrase, offset in _RELATIVE_DAY_EXACT:
        if re.search(r"\b" + re.escape(phrase) + r"\b", norm, re.IGNORECASE):
            resolved = today + timedelta(days=offset)
            return resolved.isoformat(), False, None

    # 2. "N din mein / N days"
    m = _DAYS_FROM_NOW_RE.search(norm)
    if m:
        try:
            n = int(m.group(1))
            if 0 < n <= 365:
                resolved = today + timedelta(days=n)
                return resolved.isoformat(), False, None
        except ValueError:
            pass

    # 3. Named weekday → flag as needs_confirmation
    for day_name, weekday_index in _DAY_OF_WEEK.items():
        if re.search(r"\b" + re.escape(day_name) + r"\b", norm, re.IGNORECASE):
            # Compute the *next* occurrence of that weekday
            current_weekday = today.weekday()
            days_ahead = (weekday_index - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7   # "Friday" on a Friday means next Friday
            tentative = today + timedelta(days=days_ahead)
            # Return tentative but flag as needs_confirmation
            return tentative.isoformat(), True, None

    # 4. Explicit ISO date in transcript (YYYY-MM-DD)
    iso_m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_m:
        return iso_m.group(1), False, None

    # 5. dd/mm/yyyy or dd-mm-yyyy
    dmy_m = re.search(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b", text)
    if dmy_m:
        d, mo, y = dmy_m.group(1), dmy_m.group(2), dmy_m.group(3)
        if len(y) == 2:
            y = "20" + y
        try:
            parsed = date(int(y), int(mo), int(d))
            return parsed.isoformat(), False, None
        except ValueError:
            pass

    # 6. Delivery word with no resolvable date
    if re.search(r"\bdelivery\b|\bdeliver\b|\btak\b|\bतक\b|\bde\s+dena\b|\bदे\s+देना\b", norm):
        return None, False, "expected_delivery (delivery mentioned but date unclear)"

    return None, False, None
