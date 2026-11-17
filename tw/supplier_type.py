"""Classify award supplier names as juristic, natural_person, or unknown.

Rules are conservative and use only the supplier name string. They exist so
the young-supplier indicator is computed only for juristic suppliers, and so
non-juristic names never appear in a public export.

Juristic suffixes are matched only as the *trailing* legal suffix of the
normalised name, never as a bare word in the middle (so "Limited Edition
Printers" is not juristic). "Trust" is classified unknown, not juristic,
because a family trust can carry a private person's name, unless a later
check (out of scope here) says otherwise.

Fixture tests must use synthetic names only — never real private people.
"""
from __future__ import annotations

import re
from typing import Iterable, Literal, Mapping

SupplierType = Literal["juristic", "natural_person", "unknown"]

# Longer phrases first so "Pty Ltd" wins over "Ltd".
# These are matched only at the end of the normalised name.
_TRAILING_JURISTIC = (
    r"proprietary\s+limited",
    r"\(pty\)\s*ltd\.?",
    r"pty\.?\s*ltd\.?",
    r"state\s+owned(?:\s+company)?",
    r"soc(?:\s+ltd\.?)?",
    r"non-?profit(?:\s+company)?",
    r"close\s+corporation",
    r"joint\s+venture",
    r"incorporated",
    r"limited",
    r"ltd\.?",
    r"inc\.?",
    r"npc",
    r"cc",
    r"jv",
    r"\(rf\)",
    r"rf",
)
_TRAILING_JURISTIC_RE = re.compile(
    r"(?i)(?:^|[\s,./])(?:{})\s*$".format(
        "|".join(f"(?:{p})" for p in _TRAILING_JURISTIC)
    )
)

_TRADING_AS_RE = re.compile(r"(?i)\b(?:t\s*/\s*a|trading\s+as)\b")

# 1–3 initials (letter, optional period) then an optional particle and a surname, end of string.
_INITIALS_SURNAME_RE = re.compile(
    r"""(?ix)
    ^
    (?:[A-Z]\.?\s+){1,3}
    (?:(?:van|der|de|du|den|da|dos|la|le|el|ter|ten)\s+){0,2}
    [A-Z][A-Za-z'’-]{1,}
    $
    """
)


def _normalise_for_suffix(name: str) -> str:
    s = re.sub(r"\s+", " ", name.strip())
    return s.strip(".,;: ")


def classify_supplier_type(name: str | None) -> SupplierType:
    """Return juristic, natural_person, or unknown from a supplier name."""
    s = (name or "").strip()
    if not s:
        return "unknown"
    # t/a is always treated as a natural person, even if the trading style
    # contains a juristic suffix — the string still names a person.
    if _TRADING_AS_RE.search(s):
        return "natural_person"
    if _INITIALS_SURNAME_RE.match(s):
        return "natural_person"
    if _TRAILING_JURISTIC_RE.search(_normalise_for_suffix(s)):
        return "juristic"
    return "unknown"


def young_supplier_indicator(
    supplier_type: SupplierType,
    registration_year: int | None,
    award_year: int | None,
) -> str:
    """Return yes, no, or unknown.

    Computed only for juristic suppliers. Missing years, or any non-juristic
    type, yield unknown — even if years happen to be present. `yes` only
    when the age band is `same` or `-1`; `-2` is a trend band and yields `no`.
    """
    from tw.age import young_supplier_indicator as _impl

    return _impl(supplier_type, registration_year, award_year)


def public_supplier_name(name: str | None, supplier_type: SupplierType | None = None) -> str | None:
    """Name for a public export, or None if it must be withheld.

    natural_person and unknown names never appear in public output.
    """
    typ = supplier_type if supplier_type is not None else classify_supplier_type(name)
    if typ == "juristic" and (name or "").strip():
        return name.strip()
    return None


def public_export_rows(rows: Iterable[Mapping]) -> list[dict]:
    """Copy rows for a public export, dropping non-juristic supplier names.

    Each row may have ``supplier_name`` and optional ``supplier_type``.
    Non-juristic names are replaced with None and never left in
    ``supplier_name``. Rows themselves may still appear, without the name.
    """
    out: list[dict] = []
    for raw in rows:
        row = dict(raw)
        typ: SupplierType = row.get("supplier_type") or classify_supplier_type(row.get("supplier_name"))
        row["supplier_type"] = typ
        row["supplier_name"] = public_supplier_name(row.get("supplier_name"), typ)
        out.append(row)
    return out
