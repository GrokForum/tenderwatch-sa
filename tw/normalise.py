"""Name, date, money and identifier helpers (PublicFunds-equivalent rules, local copy)."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CIPC_RE = re.compile(r"(?:19|20)\d{2}/\d{6}/\d{2}")
CSD_RE = re.compile(r"(?i)\bMAAA\d{6,}\b")
SA_ID_RE = re.compile(r"(?<![0-9])[0-9]{13}(?![0-9])")

_LEGAL_SUFFIXES = [
    r"\(pty\)\s*ltd",
    r"\bpty\s*ltd\b",
    r"\(pty\)",
    r"\bproprietary limited\b",
    r"\blimited\b",
    r"\bltd\b",
    r"\bcc\b",
    r"\bnpc\b",
    r"\binc(orporated)?\b",
    r"\bsoc\b",
    r"\b\(rf\)\b",
    r"\brf\b",
    r"\bjv\b",
    r"\bclose corporation\b",
    r"\bjoint venture\b",
]
_STOP = {"the", "and", "of"}
_NULL_TOKENS = {"", "null", "none", "n/a", "na", "-", "nan"}
OCDS_IMPLAUSIBLE_HIGH_CENTS = 20_000_000_000 * 100


def norm_name(name: str | None) -> str | None:
    """Normalise an organisation name: case, accents, punctuation, legal suffixes stripped."""
    if name is None:
        return None
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ")
    for pat in _LEGAL_SUFFIXES:
        s = re.sub(pat, " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    toks = [t for t in s.split() if t not in _STOP]
    return " ".join(toks) or None


def parse_date(s) -> date | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s or s.startswith("0001-01-01"):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def parse_mdy(s: str | None) -> date | None:
    """Parse a City register M/D/YYYY (or D/M if already ISO)."""
    if not s:
        return None
    s = str(s).strip()
    iso = parse_date(s)
    if iso:
        return iso
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_cents(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not money")
    if isinstance(value, (int, float, Decimal)):
        if isinstance(value, float) and value != value:
            return None
        d = Decimal(str(value))
    else:
        s = str(value).strip()
        if s.lower() in _NULL_TOKENS:
            return None
        neg = s.startswith("(") and s.endswith(")")
        s = s.strip("()").replace("R", "").replace("\u00a0", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(",", "")
        elif "," in s:
            groups = s.lstrip("-").split(",")
            if len(groups) > 1 and all(len(g) == 3 for g in groups[1:]) and 1 <= len(groups[0]) <= 3:
                s = s.replace(",", "")
            else:
                head, _, tail = s.rpartition(",")
                s = f"{head.replace(',', '')}.{tail}"
        try:
            d = Decimal(s)
        except InvalidOperation as exc:
            raise ValueError(f"not a money value: {value!r}") from exc
        if neg:
            d = -d
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def ocds_value(amount) -> tuple[float | None, int | None, str | None]:
    """Return (amount_rands or None, cents or None, value_note). 0 is a placeholder."""
    if amount is None:
        return None, None, "missing"
    cents = to_cents(amount)
    if cents is None:
        return None, None, "missing"
    if cents <= 0:
        return None, None, "zero_placeholder"
    rands = float(Decimal(cents) / 100)
    if cents < 100_00:
        return rands, cents, "implausible_low"
    if cents > OCDS_IMPLAUSIBLE_HIGH_CENTS:
        return rands, cents, "implausible_high"
    return rands, cents, None


def extract_cipc(text: str | None) -> str | None:
    if not text:
        return None
    m = CIPC_RE.search(str(text))
    return m.group(0) if m else None


def extract_csd(text: str | None) -> str | None:
    if not text:
        return None
    m = CSD_RE.search(str(text))
    return m.group(0).upper() if m else None


def registration_year_from_cipc(cipc: str | None) -> int | None:
    if not cipc:
        return None
    m = CIPC_RE.search(cipc)
    if not m:
        return None
    return int(m.group(0).split("/")[0])


def contains_sa_id(text: str | None) -> bool:
    if not text:
        return False
    return bool(SA_ID_RE.search(str(text)))


def norm_tender_ref(*values: str | None) -> set[str]:
    out: set[str] = set()
    for v in values:
        if not v:
            continue
        s = re.sub(r"\s+", "", str(v).strip().upper())
        if s:
            out.add(s)
        # also a punct-stripped variant
        t = re.sub(r"[^A-Z0-9]", "", s)
        if t and t != s:
            out.add(t)
    return out
