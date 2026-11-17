"""CHG-TW-004 lookup-pool scoring (pure functions; no I/O, no names printed).

Used by scripts/count_chg_tw_004_lookup_pool.py and tested in
tests/test_lookup_pool.py with synthetic records.

Unknown dates
-------------
`parse_known_date` returns None for anything that is not a real date:
None, empty or blank strings, non-ISO text, the placeholders 9999-12-31,
1900-01-01, 1970-01-01 and 0001-01-01, and any year outside 1990-2099.
An unknown date is never replaced by a fill value: an entity with an unknown
first-seen date or an unknown earliest award date scores 0 young points, and an
unknown earliest award date sorts last in the batch order.
"""
from __future__ import annotations

import datetime as dt
from typing import Iterable, Mapping, MutableMapping, Sequence

YOUNG_FIRST_SEEN_FROM = dt.date(2022, 6, 1)
YOUNG_WINDOW_DAYS = 365
PLACEHOLDER_DATES = frozenset({"9999-12-31", "1900-01-01", "1970-01-01", "0001-01-01"})
MIN_YEAR, MAX_YEAR = 1990, 2099


def parse_known_date(value: object) -> dt.date | None:
    """Return a real date, or None when the value is missing or a placeholder."""
    if not isinstance(value, str):
        return None
    text = value.strip()[:10]
    if not text or text in PLACEHOLDER_DATES:
        return None
    try:
        d = dt.date.fromisoformat(text)
    except ValueError:
        return None
    if not (MIN_YEAR <= d.year <= MAX_YEAR):
        return None
    return d


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


def batch_sort_key(e: Mapping) -> tuple:
    """Score desc, value desc, rows desc, earliest award asc (unknown last),
    tiebreak id asc (unknown last)."""
    award = e["earliest_award"]
    tid = e["tiebreak_id"]
    return (
        -e["score"],
        -(e["value"] or 0),
        -e["n"],
        award is None,
        award.isoformat() if award is not None else "",
        tid is None,
        tid if tid is not None else "",
    )
