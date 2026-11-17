"""CHG-TW-004 lookup-pool scoring (pure functions; no I/O, no names printed).

Used by scripts/count_chg_tw_004_lookup_pool.py and tested in
tests/test_lookup_pool.py with synthetic records.

Unknown dates
-------------
`parse_known_date` is strict. It accepts only a string that matches

    YYYY-MM-DD
    YYYY-MM-DDTHH:MM[:SS[.fraction]]            (bare time, no zone: date kept as written)
    YYYY-MM-DDTHH:MM[:SS[.fraction]]Z           (UTC)
    YYYY-MM-DDTHH:MM[:SS[.fraction]]+HH:MM / -HH:MM

with nothing before or after: the whole string must match (re.fullmatch, so a
trailing newline is rejected), and digits must be ASCII 0-9 (re.ASCII). A time
with Z or an offset (-00:00 is treated as UTC) is converted to UTC before the
date is taken, so the result is the UTC calendar day. Hour 24 (the ISO 8601
end-of-day form '24:00', with or without a zone) is not accepted and is
unknown. Everything else is unknown (None): None, empty or
blank strings, compact or week dates ('20240101', '2024-W01-1'), trailing text
('2024-08-30garbage'), invalid calendar dates or times, the placeholders
9999-12-31, 1900-01-01, 1970-01-01 and 0001-01-01 (checked on the written date),
and any resulting year outside 1990-2099. The pinned eTenders file uses only
'YYYY-MM-DDTHH:MM:SSZ' for release dates (35,309 of 35,309 on 17 Nov 2026);
the warehouse award_date is a plain 'YYYY-MM-DD'.
An unknown date is never replaced by a fill value: an entity with an unknown
first-seen date or an unknown earliest award date scores 0 young points, and an
unknown earliest award date sorts last in the batch order.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Iterable, Mapping, MutableMapping, Sequence

YOUNG_FIRST_SEEN_FROM = dt.date(2022, 6, 1)
YOUNG_WINDOW_DAYS = 365
PLACEHOLDER_DATES = frozenset({"9999-12-31", "1900-01-01", "1970-01-01", "0001-01-01"})
MIN_YEAR, MAX_YEAR = 1990, 2099
_DATE_RE = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})"
    r"(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?(Z|[+-]\d{2}:\d{2})?)?",
    re.ASCII,
)


def parse_known_date(value: object) -> dt.date | None:
    """Return a real UTC-normalised date, or None when the value is missing,
    malformed or a placeholder (strict; see the module docstring)."""
    if not isinstance(value, str):
        return None
    m = _DATE_RE.fullmatch(value)
    if m is None:
        return None
    y, mo, d, hh, mi, ss, frac, zone = m.groups()
    if f"{y}-{mo}-{d}" in PLACEHOLDER_DATES:
        return None
    try:
        day = dt.date(int(y), int(mo), int(d))
        if hh is not None:
            stamp = dt.datetime.combine(day, dt.time(int(hh), int(mi), int(ss or 0)))
            if zone is not None:
                if zone == "Z":
                    offset = dt.timedelta(0)
                else:
                    sign = 1 if zone[0] == "+" else -1
                    oh, om = int(zone[1:3]), int(zone[4:6])
                    if oh > 23 or om > 59:
                        return None
                    offset = sign * dt.timedelta(hours=oh, minutes=om)
                stamp = (stamp - offset)  # wall time minus offset = UTC
            day = stamp.date()
    except (ValueError, OverflowError):
        return None
    if not (MIN_YEAR <= day.year <= MAX_YEAR):
        return None
    return day


def earliest_known(values: Iterable[object]) -> dt.date | None:
    """Earliest real date among the values; None if none is known (no fill value)."""
    known = [d for d in (parse_known_date(v) for v in values) if d is not None]
    return min(known) if known else None


def is_young(first_seen: dt.date | None, earliest_award: dt.date | None) -> bool:
    """Young-company candidate: both dates known, first_seen on or after
    2022-06-01, and the earliest award 0 to 365 days after first_seen.
    A first_seen later than the award (negative gap) is not young."""
    if first_seen is None or earliest_award is None:
        return False
    if first_seen < YOUNG_FIRST_SEEN_FROM:
        return False
    gap = (earliest_award - first_seen).days
    return 0 <= gap <= YOUNG_WINDOW_DAYS


def lower_nearest_rank(sorted_values: Sequence[float], p: float) -> float:
    """Q(p) = V[floor(p * (n - 1))] on V sorted ascending; no interpolation."""
    return sorted_values[int(p * (len(sorted_values) - 1))]


def value_points(value: float, q50: float | None, q75: float | None) -> int:
    if value is None or value <= 0 or q50 is None or q75 is None:
        return 0
    if value >= q75:
        return 3
    if value >= q50:
        return 2
    return 1


def score_entities(ents: list[MutableMapping]) -> list[MutableMapping]:
    """Score and order entities in place; returns the batch order.

    Each entity needs: value (float, 0 if all missing), n (rows), link
    ("Confirmed"/"Reported"), first_seen (date|None), earliest_award
    (date|None), tiebreak_id (str|None).
    """
    pos = sorted(e["value"] for e in ents if e["value"] and e["value"] > 0)  # ascending
    q50 = lower_nearest_rank(pos, 0.50) if pos else None
    q75 = lower_nearest_rank(pos, 0.75) if pos else None
    for e in ents:
        e["young"] = is_young(e["first_seen"], e["earliest_award"])
        e["value_points"] = value_points(e["value"], q50, q75)
        e["score"] = (
            e["value_points"]
            + (3 if e["young"] else 0)
            + (2 if e["n"] >= 3 else 0)
            + (2 if e["link"] == "Confirmed" else 1)
        )
    return sorted(ents, key=batch_sort_key)


def award_id_sort_key(tid: object) -> tuple:
    """Order award ids: unknown last; all-digit ids numerically ('9' before
    '10') and before any non-numeric id; non-numeric ids by plain string order."""
    if tid is None or tid == "":
        return (1, 0, 0, "")
    text = str(tid)
    if text.isascii() and text.isdigit():
        return (0, 0, int(text), text)
    return (0, 1, 0, text)


def batch_sort_key(e: Mapping) -> tuple:
    """Score desc, value desc, rows desc, earliest award asc (unknown last),
    award id by award_id_sort_key (numeric ids numerically, then other
    ids as strings, unknown last)."""
    award = e["earliest_award"]
    tid = e["tiebreak_id"]
    return (
        -e["score"],
        -(e["value"] or 0),
        -e["n"],
        award is None,
        award.isoformat() if award is not None else "",
        award_id_sort_key(tid),
    )
