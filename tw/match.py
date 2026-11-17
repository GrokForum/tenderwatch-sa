"""Two-detail supplier match rule (CHG-TW-001 §5). Under-matching is acceptable; over-matching is not."""
from __future__ import annotations

from typing import Iterable, Mapping

from tw.normalise import norm_name, norm_tender_ref

DETAIL_CIPC = "cipc"
DETAIL_CSD = "csd"
DETAIL_NAME = "name_key"
DETAIL_BUYER = "buyer"
DETAIL_TENDER = "tender_ref"


def _name_key(rec: Mapping) -> str | None:
    return rec.get("name_key") or norm_name(rec.get("supplier_name") or rec.get("vendor") or rec.get("display_name"))


def _cipc(rec: Mapping) -> str | None:
    v = rec.get("cipc_reg_no") or rec.get("cipc")
    return str(v).strip() if v else None


def _csd(rec: Mapping) -> str | None:
    v = rec.get("csd_no") or rec.get("csd")
    return str(v).strip().upper() if v else None


def _buyer_key(rec: Mapping) -> str | None:
    raw = rec.get("buyer_name") or rec.get("jurisdiction") or rec.get("buyer")
    if not raw:
        return None
    return " ".join(str(raw).casefold().split()) or None


def _refs(rec: Mapping) -> set[str]:
    return norm_tender_ref(
        rec.get("ocid"),
        rec.get("tender_id"),
        rec.get("tender_title"),
        rec.get("tender_ref"),
        rec.get("tts_reference"),
        rec.get("decision_reference"),
    )


def agreeing_details(left: Mapping, right: Mapping) -> list[str]:
    """Return the details that agree, in a stable order."""
    agreed: list[str] = []
    lc, rc = _cipc(left), _cipc(right)
    if lc and rc and lc == rc:
        agreed.append(DETAIL_CIPC)
    ls, rs = _csd(left), _csd(right)
    if ls and rs and ls == rs:
        agreed.append(DETAIL_CSD)
    ln, rn = _name_key(left), _name_key(right)
    if ln and rn and ln == rn:
        agreed.append(DETAIL_NAME)
    lb, rb = _buyer_key(left), _buyer_key(right)
    if lb and rb and lb == rb:
        agreed.append(DETAIL_BUYER)
    if _refs(left) and _refs(right) and (_refs(left) & _refs(right)):
        agreed.append(DETAIL_TENDER)
    return agreed


def can_link(left: Mapping, right: Mapping) -> bool:
    """True only when at least two details agree. A name alone is never enough."""
    return len(agreeing_details(left, right)) >= 2


def match_pairs(left_rows: Iterable[Mapping], right_rows: Iterable[Mapping]) -> list[dict]:
    """All pairs that satisfy the two-detail rule, with the agreeing details listed."""
    rights = list(right_rows)
    out: list[dict] = []
    for l in left_rows:
        for r in rights:
            details = agreeing_details(l, r)
            if len(details) >= 2:
                out.append({"left": dict(l), "right": dict(r), "details": details})
    return out
