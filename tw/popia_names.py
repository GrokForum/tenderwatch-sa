"""CHG-TW-010: detect one-person business names (POPIA) among rows that would otherwise be shown.

A registered company or close corporation can be named after its owner ("<given name> <surname> Transport CC",
"<initials><surname> Electrical CC"). Its name then identifies a natural person, so it is masked like the
other held rows (CHG-TW-004 §13.2, CHG-TW-008). This module finds such names automatically; the owner's
fail-closed holds file (CHG-TW-008, git-ignored) stays in force for anything the detector misses.

Rule ``personal_stem``: take the legal-name part (before "t/a"), drop outer brackets, trailing legal-form
suffixes and a leading "the"; the *head* is the run of words before the first trade, place or legal word, or
the first word with a digit. If the head has two to four words (name particles such as "van" or "du" not
counted), every one alphabetic, the name is treated as a person's name and held. Initials written together
("JT") count as a word. Over-holding is the safe side: a firm named after its founders is masked too.

Rule ``single_word_stem``: a stem of one word (for example a surname alone, or a coined brand) cannot be told
apart automatically. It is not held; it is listed for a person to review in a git-ignored local file.

No names live in this module or its tests; tests use invented names only.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from tw.supplier_type import (
    _BUSINESS_WORDS,
    _LEGAL_TOKENS,
    _SUFFIX_TABLE,
    normalise_tokens,
    split_trading_as,
    strip_outer_brackets,
)

PARTICLES = {"van", "der", "de", "du", "den", "da", "dos", "la", "le", "el", "ter", "ten", "von", "mc", "mac"}
# Place and trade words for this detector only (supplier_type's list also drives CHG-TW-002 check-queue holds,
# so it is left as it is: adding words there would hold fewer bare names).
EXTRA_NON_NAME_WORDS = {
    "north", "south", "east", "west", "northern", "southern", "eastern", "western", "central", "national",
    "truck", "heavy", "current", "financial", "insurance", "medical", "rail", "harbour", "port", "metro",
    "municipal", "provincial", "province", "gauteng", "natal", "kwazulu", "free", "state", "limpopo",
    "mpumalanga", "durban", "johannesburg", "pretoria", "tshwane", "bloemfontein", "elizabeth",
    "boland", "karoo", "overberg", "garden", "route", "valley", "river", "mountain", "ocean", "sea",
    "bay", "coast", "coastal", "lab", "labs", "auto", "group", "investments", "holdings", "trust",
}
NON_NAME_WORDS = frozenset(_BUSINESS_WORDS | _LEGAL_TOKENS | EXTRA_NON_NAME_WORDS)
AUTO_REASONS = ("personal_stem",)


def name_stem(name: str | None) -> list[str]:
    """Lower-case words of the legal-name part without trailing legal-form suffixes or a leading 'the'."""
    legal, _trading = split_trading_as(name)
    toks = normalise_tokens(strip_outer_brackets(legal))
    changed = True
    while changed:
        changed = False
        if len(toks) > 1 and toks[-1] == "rf":
            toks, changed = toks[:-1], True
            continue
        for seq, _suffix, _sub in _SUFFIX_TABLE:
            n = len(seq)
            if len(toks) > n and tuple(toks[-n:]) == seq:
                toks, changed = toks[:-n], True
                break
    while toks and toks[0] == "the":
        toks = toks[1:]
    return toks


def name_head(stem: Iterable[str]) -> list[str]:
    head: list[str] = []
    for t in stem:
        if t in NON_NAME_WORDS or any(ch.isdigit() for ch in t):
            break
        head.append(t)
    return head


def one_person_reason(name: str | None) -> str | None:
    """'personal_stem' when the name reads as a person's name, 'single_word_stem' when it cannot be told, else None."""
    stem = name_stem(name)
    if not stem:
        return None
    head = name_head(stem)
    counted = [t for t in head if t not in PARTICLES]
    if 2 <= len(counted) <= 4 and all(t.isalpha() for t in head):
        return "personal_stem"
    if len(stem) == 1 and stem[0].isalpha() and len(stem[0]) >= 3:
        return "single_word_stem"
    return None


def _names(row: Mapping) -> list[str]:
    out = [row.get("legal_name"), row.get("supplier_name")]
    return [n for n in out if isinstance(n, str) and n.strip()]


def apply_auto_holds(rows: list[dict]) -> dict:
    """Hold every Confirmed row whose legal or source name reads as a person's name. Returns counts only.

    Only ``confirmed_juristic`` rows are looked at: every other row is already masked, pending or withheld.
    A row already held (classifier or owner holds file) keeps its hold and is counted under ``already_held``.
    """
    counts = {"personal_stem": 0, "already_held": 0, "review_single_word": 0}
    for r in rows:
        if r.get("classification_status") != "confirmed_juristic":
            continue
        reasons = {one_person_reason(n) for n in _names(r)}
        if "personal_stem" in reasons:
            if r.get("popia_hold"):
                counts["already_held"] += 1
            else:
                r["popia_hold"] = True
                r["popia_hold_reason"] = "auto:personal_stem"
                counts["personal_stem"] += 1
        elif "single_word_stem" in reasons and not r.get("popia_hold"):
            r["popia_review"] = "single_word_stem"
            counts["review_single_word"] += 1
    return counts


def write_review_candidates(rows: Iterable[Mapping], path: Path) -> int:
    """Local, git-ignored list for a person to review (names included; never committed, never published)."""
    seen: dict[str, dict] = {}
    for r in rows:
        if r.get("popia_review") or str(r.get("popia_hold_reason") or "").startswith("auto:"):
            key = r.get("name_key") or ""
            seen.setdefault(key, {"name_key": key, "supplier_name": r.get("supplier_name") or "",
                                  "legal_name": r.get("legal_name") or "",
                                  "reason": r.get("popia_review") or r.get("popia_hold_reason"),
                                  "buyer": r.get("buyer_name") or "", "rows": 0})["rows"] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["name_key", "supplier_name", "legal_name", "reason", "buyer", "rows"])
        w.writeheader()
        for k in sorted(seen):
            w.writerow(seen[k])
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return len(seen)
