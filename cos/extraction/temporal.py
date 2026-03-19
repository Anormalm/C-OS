from __future__ import annotations

import re
from datetime import datetime, timezone

from dateutil import parser as dt_parser

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")


def extract_timestamp(text: str) -> datetime | None:
    iso_match = ISO_DATE_RE.search(text)
    if iso_match:
        return datetime.fromisoformat(iso_match.group(1)).replace(tzinfo=timezone.utc)

    try:
        parsed = dt_parser.parse(text, fuzzy=True, default=datetime.now(timezone.utc))
        if parsed.year < 1900:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        pass

    year_match = YEAR_RE.search(text)
    if year_match:
        year = int(year_match.group(1))
        return datetime(year=year, month=1, day=1, tzinfo=timezone.utc)
    return None
