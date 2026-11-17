"""Classify award supplier names (CHG-TW-001, revised by CHG-TW-002).

CHG-TW-002 (owner decision relayed by the project lead): no supplier is
silently hidden. Every supplier gets exactly one status:

* ``confirmed_juristic`` -- the legal name carries a legal-form suffix
  (method 1). The City of Cape Town register name is used first, the
  OCDS name if needed.
* ``check_queue`` -- everything else, with a recorded reason, for a
  two-person check (method 2).

Suffixes are matched on whole *trailing tokens* after normalisation (case,
punctuation, spacing), never as a substring inside a word: "Mccarthy" is not
"CC", "Trustee" is not "Trust", "Jinc" is not "Inc".

"Trust" is a legal form (owner decision, reversing the CHG-TW-001 rule that a
trust was unknown). A trust is registered with the Master of the High Court,
not CIPC, so its CIPC age indicator stays Unknown unless a sourced year exists.

Names that look like a sole trader or a private person get ``popia_hold`` and
are never written to a public file until the two-person check clears them.

Fixture tests must use synthetic names only -- never real private people.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Iterable, Literal, Mapping, Sequence

SupplierType = Literal["juristic", "natural_person", "unknown"]
SubType = Literal["company", "close_corporation", "npc", "soc", "trust", "jv", "other_juristic"]
Status = Literal["confirmed_juristic", "check_queue"]
QueueReason = Literal[
    "looks_like_personal_name",
    "name_mismatch_between_sources",
    "ambiguous_suffix",
    "no_suffix",
    "empty_name",
]

STATUSES: tuple[str, ...] = ("confirmed_juristic", "check_queue")
QUEUE_REASONS: tuple[str, ...] = (
    "looks_like_personal_name",
    "name_mismatch_between_sources",
    "ambiguous_suffix",
    "no_suffix",
    "empty_name",
)
SUB_TYPES: tuple[str, ...] = ("company", "close_corporation", "npc", "soc", "trust", "jv", "other_juristic")

# Trailing token sequences -> (canonical suffix, sub-type). Longest first, so
# "soc ltd" wins over "ltd" and "proprietary limited" over "limited".
_SUFFIX_TABLE: list[tuple[tuple[str, ...], str, str]] = [
    (("state", "owned", "company"), "SOC", "soc"),
    (("non", "profit", "company"), "NPC", "npc"),
    (("proprietary", "limited"), "(Pty) Ltd", "company"),
    (("close", "corporation"), "CC", "close_corporation"),
    (("joint", "venture"), "JV", "jv"),
    (("soc", "limited"), "SOC Ltd", "soc"),
    (("soc", "ltd"), "SOC Ltd", "soc"),
    (("pty", "limited"), "(Pty) Ltd", "company"),
    (("pty", "ltd"), "(Pty) Ltd", "company"),
    (("incorporated",), "Inc", "company"),
    (("limited",), "Ltd", "company"),
    (("ltd",), "Ltd", "company"),
    (("inc",), "Inc", "company"),
    (("npc",), "NPC", "npc"),
    (("soc",), "SOC", "soc"),
    (("cc",), "CC", "close_corporation"),
    (("trust",), "Trust", "trust"),
    (("jv",), "JV", "jv"),
    (("rf",), "RF", "other_juristic"),
]
_LEGAL_TOKENS = {t for seq, _, _ in _SUFFIX_TABLE for t in seq if t not in {"state", "owned", "company", "non", "profit", "close", "joint"}}
_LEGAL_TOKENS |= {"proprietary", "corporation", "venture", "pty"}

_TRADING_AS_RE = re.compile(r"(?i)(?:^|[\s,;(])(?:t\s*/\s*a|trading\s+as)(?=$|[\s,;:)])")
_TITLE_RE = re.compile(r"(?i)^(?:mr|mrs|ms|miss|dr|prof|adv|rev)\.?\s+\S")

# 1-3 initials (letter, optional period) then an optional particle and a surname, end of string.
_INITIALS_SURNAME_RE = re.compile(
    r"""(?ix)
    ^
    (?:[A-Z](?:\.\s*|\s+)){1,3}
    (?:(?:van|der|de|du|den|da|dos|la|le|el|ter|ten)\s+){0,2}
    [A-Z][A-Za-z'\u2019-]{1,}
    $
    """
)

# Words that mark a business-style name. A name of two to four plain words with
# none of these, no digits and no legal token "looks like a bare personal
# name" and is held for POPIA (over-holding is the safe side).
_BUSINESS_WORDS = {
    "africa", "african", "agency", "agencies", "air", "aqua", "architects", "art", "associates", "attorneys",
    "auto", "automation", "bakery", "bank", "brothers", "build", "builders", "building", "bus", "business",
    "cape", "capital", "care", "catering", "centre", "center", "chemicals", "city", "civil", "civils",
    "cleaning", "clinic", "communications", "company", "computer", "computers", "concepts", "construction",
    "consultants", "consulting", "contractors", "corporation", "creative", "data", "design", "designs",
    "development", "developments", "digital", "distributors", "distribution", "eco", "electric", "electrical",
    "electronics", "energy", "engineering", "engineers", "enterprise", "enterprises", "environmental",
    "equipment", "events", "farm", "fencing", "fire", "fleet", "food", "foods", "forum", "foundation",
    "freight", "fuel", "furniture", "general", "global", "green", "group", "hardware", "health", "holdings",
    "hire", "house", "hygiene", "industrial", "industries", "infrastructure", "institute", "international",
    "investments", "irrigation", "it", "lab", "laboratories", "laboratory", "landscaping", "logistics",
    "machinery", "maintenance", "management", "manufacturing", "marine", "marketing", "media", "medical",
    "mining", "motor", "motors", "network", "networks", "office", "oil", "paint", "partners", "pharma",
    "plant", "plastics", "plumbing", "power", "print", "printers", "printing", "products", "projects",
    "promotions", "properties", "property", "pumps", "resources", "road", "roads", "safety", "sales",
    "security", "service", "services", "shop", "signs", "software", "solar", "solutions", "sport", "sports",
    "steel", "stores", "studio", "supplies", "supply", "surveys", "systems", "tech", "technical",
    "technologies", "technology", "telecoms", "tools", "trade", "traders", "trading", "training",
    "transport", "travel", "trucks", "university", "valves", "water", "waste", "wholesalers", "works",
    "world", "and", "the", "of", "sa", "za",
    # generic trade vocabulary (added in CHG-TW-002 DEV review; not names)
    "auctioneers", "consultancy", "corp", "creations", "driving", "evaluation", "geomatics", "ironmongery",
    "jointing", "konstruksie", "manufacturers", "meters", "mobile", "rentals", "reticulation", "roadmarking",
    "roadworthy", "school", "stations", "structures", "suppliers", "telecom", "integrity", "premier",
}


def normalise_tokens(name: str | None) -> list[str]:
    """Lower-case ASCII tokens; punctuation, brackets and hyphens become spaces."""
    if not name:
        return []
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().casefold()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.split()


def split_trading_as(name: str | None) -> tuple[str, str | None]:
    """Return (legal-name part, trading-name part or None)."""
    s = (name or "").strip()
    m = _TRADING_AS_RE.search(s)
    if not m:
        return s, None
    return s[: m.start()].strip(" ,;("), s[m.end():].strip(" ,;)") or None


@dataclass(frozen=True)
class LegalForm:
    suffix: str
    sub_type: str
    position: str  # "trailing" or "before_trading_as"


def trailing_legal_form(name: str | None) -> LegalForm | None:
    """Legal form from trailing suffix tokens of the *legal-name* part.

    If the name has "t/a", only the part before it is the legal name; a suffix
    on the trading name after "t/a" does not count.
    """
    legal, trading = split_trading_as(name)
    # "C.C." (dotted initials of close corporation) -> "CC"; only with the dots.
    legal = re.sub(r"(?i)(?<![a-z])c\.\s*c\.?\s*$", " CC", legal)
    toks = normalise_tokens(legal)
    if not toks:
        return None
    # "(RF) (Pty) Ltd" and "(Pty) Ltd (RF)": RF is a qualifier on another form.
    core = toks[:-1] if toks[-1] == "rf" and len(toks) > 1 else toks
    for seq, suffix, sub in _SUFFIX_TABLE:
        n = len(seq)
        if len(core) > n and tuple(core[-n:]) == seq:
            if all(t in _LEGAL_TOKENS for t in core[:-n]):
                return None  # nothing but legal words: no entity name in front
            if seq == ("rf",):
                continue  # RF needs another form; bare RF handled below
            return LegalForm(suffix, sub, "before_trading_as" if trading is not None else "trailing")
    if len(toks) > 1 and toks[-1] == "rf" and not all(t in _LEGAL_TOKENS for t in toks[:-1]):
        return LegalForm("RF", "other_juristic", "before_trading_as" if trading is not None else "trailing")
    return None


def has_inner_legal_token(name: str | None) -> bool:
    """A legal-form word appears as a whole token, but not as the trailing suffix."""
    toks = normalise_tokens(name)
    return any(t in _LEGAL_TOKENS for t in toks)


def looks_like_personal_name(name: str | None) -> bool:
    """Sole trader or private-person pattern: t/a without a legal suffix,
    initials plus surname, a title, or a bare two-to-four-word name with no
    business word, digit or legal token."""
    s = (name or "").strip()
    if not s:
        return False
    legal, trading = split_trading_as(s)
    form = trailing_legal_form(s)
    if form is not None:
        # A registered entity name is not personal information, except a trust
        # whose stem is a family or person-style name (e.g. "<name> Family Trust").
        if form.sub_type == "trust":
            stem = normalise_tokens(legal)[:-1]
            return "family" in stem or _stem_is_personal(stem)
        return False
    if trading is not None:
        return True  # sole trader: "<person> t/a <trade name>"
    if _INITIALS_SURNAME_RE.match(legal) or _TITLE_RE.match(legal):
        return True
    toks = normalise_tokens(legal)
    if 2 <= len(toks) <= 4 and not any(ch.isdigit() for ch in legal):
        if not any(t in _BUSINESS_WORDS or t in _LEGAL_TOKENS for t in toks):
            return True
    return False


def _stem_is_personal(tokens: Sequence[str]) -> bool:
    if not tokens:
        return False
    if all(len(t) == 1 for t in tokens[:-1]) and len(tokens) >= 2 and len(tokens[-1]) > 1:
        return True
    return 2 <= len(tokens) <= 3 and not any(t in _BUSINESS_WORDS for t in tokens)


@dataclass
class Classification:
    status: str
    method: str | None = None
    sub_type: str | None = None
    legal_suffix: str | None = None
    legal_name_source: str | None = None
    legal_name: str | None = None
    queue_reason: str | None = None
    queue_notes: list[str] = field(default_factory=list)
    popia_hold: bool = False
    registry: str | None = None
    supplier_type: str = "unknown"
    legal_form_link: str | None = None
    legal_form_fact_label: str | None = None

    def as_fields(self) -> dict:
        d = asdict(self)
        return {
            "classification_status": d["status"],
            "classification_method": d["method"],
            "legal_sub_type": d["sub_type"],
            "legal_suffix": d["legal_suffix"],
            "legal_name_source": d["legal_name_source"],
            "legal_name": d["legal_name"],
            "queue_reason": d["queue_reason"],
            "queue_notes": ";".join(d["queue_notes"]) or None,
            "popia_hold": d["popia_hold"],
            "registry": d["registry"],
            "supplier_type": d["supplier_type"],
            "legal_form_link": d["legal_form_link"],
            "legal_form_fact_label": d["legal_form_fact_label"],
        }


def _registry(sub_type: str | None) -> str | None:
    if sub_type is None:
        return None
    return "master_of_high_court" if sub_type == "trust" else "cipc"


def classify_supplier(
    ocds_name: str | None,
    city_names: Sequence[str] = (),
    *,
    city_tender_only_names: Sequence[str] = (),
    city_tight_names: Sequence[str] = (),
) -> Classification:
    """Give one supplier exactly one status.

    ``city_names``: City register names linked by the two-detail rule *with the
    normalised name agreeing* (so they name the same supplier).
    ``city_tender_only_names``: City names on the same tender/buyer whose name
    does not agree (multi-vendor tenders or a different spelling).
    ``city_tight_names``: the subset of ``city_names`` whose link also shares a
    tender reference. Per CHG-TW-001 section 19, a name-and-buyer-only link is
    not a tight match, so a legal form taken from it is labelled Reported,
    not Confirmed, until a tight link or the two-person check confirms it.
    """
    ocds = (ocds_name or "").strip()
    city = sorted({c.strip() for c in city_names if c and c.strip()})
    all_names = [n for n in [*city, ocds] if n]
    personal = any(looks_like_personal_name(n) for n in all_names)

    if not all_names:
        return Classification(status="check_queue", queue_reason="empty_name", supplier_type="unknown")

    city_forms = {n: trailing_legal_form(n) for n in city}
    city_with = {n: f for n, f in city_forms.items() if f is not None}
    ocds_form = trailing_legal_form(ocds) if ocds else None

    tight = {t.strip() for t in city_tight_names if t}

    def confirmed(form: LegalForm, source: str, legal_name: str) -> Classification:
        method = f"{source}_suffix" + ("_before_trading_as" if form.position == "before_trading_as" else "")
        if source == "ocds":
            link, label = "same_record", "Confirmed"
        elif legal_name in tight:
            link, label = "tender_ref", "Confirmed"
        else:
            link, label = "name_and_buyer_only", "Reported"
        return Classification(
            legal_form_link=link,
            legal_form_fact_label=label,
            status="confirmed_juristic",
            method=method,
            sub_type=form.sub_type,
            legal_suffix=form.suffix,
            legal_name_source=source,
            legal_name=legal_name,
            popia_hold=personal,
            registry=_registry(form.sub_type),
            supplier_type="juristic",
        )

    def queued(reason: str, *notes: str) -> Classification:
        return Classification(
            status="check_queue",
            queue_reason=reason,
            queue_notes=[n for n in notes if n],
            popia_hold=personal,
            supplier_type="natural_person" if personal else "unknown",
        )

    # POPIA first: a personal-looking name is queued and held, whatever else.
    if personal and not (city_with or ocds_form):
        return queued("looks_like_personal_name")

    if city_with:
        subs = {f.sub_type for f in city_with.values()}
        if len(subs) > 1:
            return queued("ambiguous_suffix", "city_spellings_disagree_on_legal_form")
        sub = next(iter(subs))
        if ocds_form is not None and ocds_form.sub_type != sub:
            return queued("name_mismatch_between_sources", "ocds_and_city_legal_form_differ")
        name, form = sorted(city_with.items(), key=lambda kv: (kv[0] not in tight, kv[0]))[0]
        notes = []
        if len(city) > len(city_with):
            notes.append("some_city_spellings_without_suffix")
        c = confirmed(form, "city_register", name)
        c.queue_notes = notes
        return c

    if ocds_form is not None:
        return confirmed(ocds_form, "ocds", ocds)

    if personal:
        return queued("looks_like_personal_name")
    if city_tender_only_names:
        return queued("name_mismatch_between_sources", "city_names_same_tender_differ")
    if any(has_inner_legal_token(n) for n in all_names):
        return queued("ambiguous_suffix", "legal_word_not_trailing")
    return queued("no_suffix")


def classify_supplier_type(name: str | None) -> SupplierType:
    """Return juristic, natural_person, or unknown from one supplier name."""
    s = (name or "").strip()
    if not s:
        return "unknown"
    if trailing_legal_form(s) is not None:
        return "juristic"
    if looks_like_personal_name(s) and (split_trading_as(s)[1] is not None or _INITIALS_SURNAME_RE.match(s) or _TITLE_RE.match(s)):
        return "natural_person"
    return "unknown"


def young_supplier_indicator(
    supplier_type: SupplierType,
    registration_year: int | None,
    award_year: int | None,
) -> str:
    """Return yes, no, or unknown (juristic only; see tw.age)."""
    from tw.age import young_supplier_indicator as _impl

    return _impl(supplier_type, registration_year, award_year)


def public_supplier_name(
    name: str | None,
    supplier_type: SupplierType | None = None,
    *,
    status: str | None = None,
    popia_hold: bool | None = None,
) -> str | None:
    """Name for a public export, or None if it must be withheld.

    Shown only for a confirmed juristic supplier without a POPIA hold. Queued
    rows keep their row, status and reason, but not the name, until the
    two-person check.
    """
    s = (name or "").strip()
    if not s:
        return None
    typ = supplier_type if supplier_type is not None else classify_supplier_type(s)
    if status is not None and status != "confirmed_juristic":
        return None
    hold = popia_hold if popia_hold is not None else looks_like_personal_name(s)
    if typ == "juristic" and not hold:
        return s
    return None


def public_export_rows(rows: Iterable[Mapping]) -> list[dict]:
    """Copy rows for a public export, withholding names that may not be public.

    Every input row is returned (no silent hide); only the name is blanked.
    """
    out: list[dict] = []
    for raw in rows:
        row = dict(raw)
        typ: SupplierType = row.get("supplier_type") or classify_supplier_type(row.get("supplier_name"))
        row["supplier_type"] = typ
        row["supplier_name"] = public_supplier_name(
            row.get("supplier_name"),
            typ,
            status=row.get("classification_status"),
            popia_hold=row.get("popia_hold"),
        )
        if row["supplier_name"] is None:
            row["legal_name"] = None
        out.append(row)
    return out


def classify_awards(awards: list[dict], city_rows: Sequence[Mapping]) -> list[dict]:
    """Attach a classification to every award row (in place) and return them.

    Uses ``award['city_matches']`` from the two-detail matcher: links whose
    details include ``name_key`` supply City names for this supplier; links on
    buyer + tender only are recorded as a mismatch signal.
    """
    from tw.match import agreeing_details, can_link

    for award in awards:
        same_name: list[str] = []
        tender_only: list[str] = []
        tight: list[str] = []
        for city in city_rows:
            if not can_link(award, city):
                continue
            details = agreeing_details(award, city)
            nm = city.get("supplier_name") or city.get("vendor")
            if not nm:
                continue
            (same_name if "name_key" in details else tender_only).append(nm)
            if "name_key" in details and "tender_ref" in details:
                tight.append(nm)
        c = classify_supplier(
            award.get("supplier_name"), same_name, city_tender_only_names=tender_only, city_tight_names=tight
        )
        award.update(c.as_fields())
    assert_no_silent_hide(awards, len(awards))
    return awards


def assert_no_silent_hide(rows: Sequence[Mapping], expected: int) -> None:
    """Every row classified once: valid status; queued rows have a reason."""
    if len(rows) != expected:
        raise AssertionError(f"classified {len(rows)} rows, expected {expected}")
    for r in rows:
        st = r.get("classification_status")
        if st not in STATUSES:
            raise AssertionError(f"row without a valid status: {st!r}")
        if st == "check_queue" and r.get("queue_reason") not in QUEUE_REASONS:
            raise AssertionError("queued row without a reason")
        if st == "confirmed_juristic" and (r.get("legal_sub_type") not in SUB_TYPES or not r.get("classification_method")):
            raise AssertionError("confirmed row without method or sub-type")
