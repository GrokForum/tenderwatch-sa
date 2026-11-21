"""Read-only Cape Town award ingest from the pinned PublicFunds etenders_ocds dump."""
from __future__ import annotations

import gzip
import re
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Iterator

from tw.age import classify_age
from tw.config import (
    DEFAULT_BUYER,
    EXPECTED_OCDS_SHA256,
    INDICATOR_WINDOW_LABEL,
    OCDS_SOURCE_URL,
    RIGHT_OF_REPLY,
)
from tw.normalise import (
    CIPC_RE,
    CSD_RE,
    extract_cipc,
    extract_csd,
    norm_name,
    ocds_value,
    parse_date,
    registration_year_from_cipc,
)
from tw.popia import strip_forbidden
from tw.supplier_type import classify_supplier_type

BUYER_CANON = DEFAULT_BUYER.casefold()


def name_for_classification(name: str | None) -> str | None:
    """Strip CIPC/CSD tokens so a trailing legal suffix still classifies as juristic."""
    if not name:
        return name
    s = CIPC_RE.sub(" ", name)
    s = CSD_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip(" ,;./") or None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def is_cape_town_buyer(name: str | None) -> bool:
    if not name:
        return False
    return " ".join(name.split()).casefold() == BUYER_CANON


def _party_id_texts(rel: dict, supplier_name: str | None, supplier_id: str | None) -> list[str]:
    texts: list[str] = []
    if supplier_name:
        texts.append(supplier_name)
    if supplier_id:
        texts.append(str(supplier_id))
    want = {*( [supplier_name.casefold()] if supplier_name else [] ), *([str(supplier_id)] if supplier_id else [])}
    for party in rel.get("parties") or []:
        if not isinstance(party, dict):
            continue
        pname = (party.get("name") or "").strip()
        pid = party.get("id")
        roles = {str(r).casefold() for r in (party.get("roles") or [])}
        if pname.casefold() not in want and (pid is None or str(pid) not in want) and "supplier" not in roles:
            continue
        ident = party.get("identifier")
        if isinstance(ident, dict):
            for v in ident.values():
                if isinstance(v, str):
                    texts.append(v)
        for ident in party.get("additionalIdentifiers") or []:
            if isinstance(ident, dict):
                for v in ident.values():
                    if isinstance(v, str):
                        texts.append(v)
    return texts


def _pick_cipc_csd(texts: list[str]) -> tuple[str | None, str | None]:
    cipc = None
    csd = None
    for t in texts:
        cipc = cipc or extract_cipc(t)
        csd = csd or extract_csd(t)
    return cipc, csd


def award_rows_from_release(
    rel: dict,
    *,
    locator: str,
    source_file: str,
    sha256: str,
    retrieved_at: str,
    source_url: str = OCDS_SOURCE_URL,
    buyer_filter=None,
) -> list[dict]:
    """One compiled release → award-supplier rows, contacts already dropped.

    ``buyer_filter`` (CHG-TW-011) picks the buyers; the default is the City of Cape Town only.
    """
    rel = strip_forbidden(rel)
    buyer = rel.get("buyer") or {}
    buyer_name = (buyer.get("name") or "").strip() or None
    if not (buyer_filter or is_cape_town_buyer)(buyer_name):
        return []
    tender = rel.get("tender") or {}
    signed = {}
    for c in rel.get("contracts") or []:
        if not isinstance(c, dict):
            continue
        d = parse_date(c.get("dateSigned"))
        if d is None:
            continue
        if c.get("awardID") is not None:
            signed[str(c.get("awardID"))] = d
    release_date = parse_date(rel.get("date"))
    rows: list[dict] = []
    for a in rel.get("awards") or []:
        if not isinstance(a, dict):
            continue
        amount, cents, vnote = ocds_value((a.get("value") or {}).get("amount"))
        currency = ((a.get("value") or {}).get("currency")) if a.get("value") else None
        award_id = a.get("id")
        award_date = signed.get(str(award_id)) if award_id is not None else None
        if award_date is not None:
            basis = "contract.dateSigned"
        else:
            award_date = release_date
            basis = "release.date" if award_date else None
        # awards.date is typically empty; use only if both of the above are missing
        if award_date is None:
            award_date = parse_date(a.get("date"))
            if award_date is not None:
                basis = "awards.date"
        award_year = award_date.year if isinstance(award_date, date) else None
        sups = a.get("suppliers") or []
        if not sups:
            sups = [{}]
        for s in sups:
            if not isinstance(s, dict):
                s = {}
            sname = (s.get("name") or "").strip() or None
            sid = s.get("id")
            # portal id "0" is not a registration number
            portal_id = None if sid in (None, "", 0, "0") else str(sid)
            cipc, csd = _pick_cipc_csd(_party_id_texts(rel, sname, portal_id or (str(sid) if sid not in (None, "") else None)))
            typ = classify_supplier_type(name_for_classification(sname))
            reg_year = registration_year_from_cipc(cipc) if typ == "juristic" else None
            if typ != "juristic":
                cipc = None
                reg_year = None
            indicator, band = classify_age(typ, reg_year, award_year)
            year_label = "Confirmed" if reg_year is not None else "Unknown"
            year_source = source_url if reg_year is not None else None
            rows.append({
                "ocid": rel.get("ocid"),
                "award_id": str(award_id) if award_id is not None else None,
                "buyer_name": buyer_name,
                "buyer_id": buyer.get("id"),
                "tender_title": tender.get("title"),
                "tender_id": tender.get("id"),
                "procurement_method": tender.get("procurementMethod"),
                "supplier_name": sname,
                "name_key": norm_name(sname),
                "supplier_id_portal": portal_id,
                "supplier_type": typ,
                "cipc_reg_no": cipc,
                "csd_no": csd,
                "registration_year": reg_year,
                "registration_year_label": year_label,
                "registration_year_source_url": year_source,
                "value_amount": amount,
                "value_currency": currency or "ZAR",
                "value_cents": cents,
                "value_note": vnote,
                "award_date": award_date.isoformat() if award_date else None,
                "award_date_basis": basis,
                "award_year": award_year,
                "young_supplier_indicator": indicator,
                "indicator_window": INDICATOR_WINDOW_LABEL,
                "age_band": band,
                "fact_label": "Confirmed",
                "right_of_reply": RIGHT_OF_REPLY,
                "source_url": source_url,
                "source_file": source_file,
                "source_locator": locator,
                "sha256": sha256,
                "retrieved_at": retrieved_at,
            })
    return rows


def iter_cape_town_awards(
    path: Path,
    *,
    retrieved_at: str,
    expected_sha256: str = EXPECTED_OCDS_SHA256,
) -> Iterator[dict]:
    digest = sha256_file(path)
    if digest != expected_sha256:
        raise ValueError(f"etenders_ocds sha256 mismatch: got {digest}, expected {expected_sha256}")
    source_file = str(path)
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            rel = json.loads(line)
            locator = f"{path.name}:line {i}"
            for row in award_rows_from_release(
                rel,
                locator=locator,
                source_file=source_file,
                sha256=digest,
                retrieved_at=retrieved_at,
            ):
                yield row


def iter_awards(
    path: Path,
    *,
    retrieved_at: str,
    buyer_filter,
    expected_sha256: str = EXPECTED_OCDS_SHA256,
) -> Iterator[dict]:
    """CHG-TW-011: award-supplier rows for any set of buyers from the pinned file (same row shape as above)."""
    digest = sha256_file(path)
    if digest != expected_sha256:
        raise ValueError(f"etenders_ocds sha256 mismatch: got {digest}, expected {expected_sha256}")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            rel = json.loads(line)
            yield from award_rows_from_release(
                rel,
                locator=f"{path.name}:line {i}",
                source_file=path.name,
                sha256=digest,
                retrieved_at=retrieved_at,
                buyer_filter=buyer_filter,
            )
