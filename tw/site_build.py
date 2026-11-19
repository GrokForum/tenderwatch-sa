"""CHG-TW-006: load the DEV inputs, build the site and run the public-file scans."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tw.classification_report import withheld_names
from tw.config import load_config
from tw.public_scan import run_all
from tw.site import UnsafeBuild, build_rows, build_site, load_lookups, shown_names

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "local" / "warehouse"
CLASSIFIED = WAREHOUSE / "awards_classified_chg_tw_002.jsonl"
CITY = WAREHOUSE / "city_register.jsonl"
LOOKUPS = ROOT / "data" / "local" / "lookups.csv"
HOLDS = ROOT / "data" / "local" / "popia_holds.json"  # git-ignored; never committed (CHG-TW-008)
MIN_HOLDS = 3  # holds decided so far (owner, 19 Nov 2026); a shorter local file stops the build
EXPECTED_ROWS = 291


def _jsonl(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _date_only(s: str | None) -> str | None:
    return s[:10] if s and len(s) >= 10 and s[4] == "-" and s[7] == "-" else None


def load_holds(path: Path | None = None) -> list[dict]:
    """CHG-TW-008: POPIA holds from the git-ignored local file, keyed by award record (ocid and award_id).

    The file is never committed (the repository is to be open-sourced, and a record id next to a hold basis
    would let anyone look the name up in the public eTenders data). It is seeded once into each checkout,
    the nightly clone included. A missing, unreadable or short file stops the build (fail closed).
    """
    path = HOLDS if path is None else path
    if not path.is_file():
        raise UnsafeBuild("holds file missing: seed data/local/popia_holds.json (CHG-TW-008); not building")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise UnsafeBuild(f"holds file unreadable: {e.__class__.__name__}") from None
    holds = data.get("holds") if isinstance(data, dict) else None
    if not isinstance(holds, list):
        raise UnsafeBuild("holds file: 'holds' must be a list")
    seen = set()
    out = []
    for i, h in enumerate(holds):
        if not isinstance(h, dict):
            raise UnsafeBuild(f"holds file entry {i}: not an object")
        ocid = h.get("ocid")
        award = h.get("award_id")
        basis = h.get("basis")
        if not isinstance(ocid, str) or not re.fullmatch(r"ocds-[a-z0-9]+-[0-9]+", ocid.strip(), flags=re.ASCII):
            raise UnsafeBuild(f"holds file entry {i}: ocid missing or malformed")
        award = str(award).strip() if isinstance(award, (str, int)) and not isinstance(award, bool) else ""
        if not re.fullmatch(r"[1-9][0-9]*", award, flags=re.ASCII):
            raise UnsafeBuild(f"holds file entry {i}: award_id must be a positive whole number")
        if not isinstance(basis, str) or not basis.strip():
            raise UnsafeBuild(f"holds file entry {i}: basis is required")
        key = (ocid.strip(), award)
        if key in seen:
            raise UnsafeBuild(f"holds file entry {i}: duplicate award record")
        seen.add(key)
        out.append({"ocid": key[0], "award_id": key[1], "basis": basis.strip()})
    if len(out) < MIN_HOLDS:
        raise UnsafeBuild(f"holds file has {len(out)} holds, fewer than the {MIN_HOLDS} decided; not building")
    return out


def _names_of(row: dict) -> set[str]:
    names = {row.get("supplier_name"), row.get("legal_name"), row.get("name_key")}
    names.update((row.get("city_names_linked") or "").split(";"))
    return {n.strip().lower() for n in names if isinstance(n, str) and len(n.strip()) >= 4}


def apply_holds(rows: list[dict], holds: list[dict]) -> int:
    """Set popia_hold on every listed award record.

    Stops the build when a listed record is missing from the input, when it is not a Confirmed row (a hold
    must never move a check-queue or withheld row into a shown group), or when a basis carries any supplier
    name from the input.
    """
    index: dict[tuple[str, str], list[dict]] = {}
    every_name: set[str] = set()
    for r in rows:
        index.setdefault((str(r.get("ocid") or ""), str(r.get("award_id") or "")), []).append(r)
        every_name |= _names_of(r)
    n = 0
    for h in holds:
        basis = h["basis"].lower()
        if any(name in basis for name in every_name):
            raise UnsafeBuild("a hold basis contains a supplier name")
        hits = index.get((h["ocid"], h["award_id"]))
        if not hits:
            raise UnsafeBuild("a hold names an award record that is not in the input")
        for r in hits:
            if r.get("classification_status") != "confirmed_juristic":
                raise UnsafeBuild("a hold names a row that is not Confirmed; check-queue rows keep their own group")
            r["popia_hold"] = True
            n += 1
    return n


def load_inputs() -> dict:
    if not CLASSIFIED.is_file():
        raise FileNotFoundError("DEV export missing: run scripts/run_chg_tw_002_classify.py first")
    rows = _jsonl(CLASSIFIED)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows in the DEV export, got {len(rows)}")
    holds_applied = apply_holds(rows, load_holds())  # before withheld_names, so the scans also look for held names
    city = _jsonl(CITY) if CITY.is_file() else []
    city_meta = {}
    for c in city:
        if c.get("source_url"):
            city_meta.setdefault(c["source_url"], {"retrieved": _date_only(c.get("retrieved_at"))})
    cfg = load_config()
    retrieved = _date_only(cfg["etenders_ocds"].get("publicfunds_fetched_at_sast")) or ""
    digest = hashlib.sha256(CLASSIFIED.read_bytes()).hexdigest()
    all_names = {r.get("supplier_name") for r in rows} | {c.get("supplier_name") for c in city}
    all_names = {n.strip() for n in all_names if n and n.strip()}
    return {"rows": rows, "city_meta": city_meta, "etenders_retrieved": retrieved, "input_sha256": digest,
            "withheld": withheld_names(rows), "all_names": all_names, "lookups": load_lookups(LOOKUPS),
            "holds_applied": holds_applied}


def run_build(out_dir: Path) -> dict:
    inp = load_inputs()
    manifest = build_site(inp["rows"], out_dir, lookups=inp["lookups"], city_meta=inp["city_meta"],
                          etenders_retrieved=inp["etenders_retrieved"], input_sha256=inp["input_sha256"])
    model = build_rows(inp["rows"], lookups=inp["lookups"], city_meta=inp["city_meta"],
                       etenders_retrieved=inp["etenders_retrieved"])
    allowed = shown_names(model["rows"])
    scans = run_all(out_dir, withheld=inp["withheld"], all_names=inp["all_names"], allowed=allowed)
    return {
        "build": "OK",
        "rows_total": manifest["rows_total"],
        "group_counts": manifest["group_counts"],
        "year_counts": manifest["year_counts"],
        "content_sha256": manifest["content_sha256"],
        "input_sha256": manifest["input_sha256"],
        "lookups_loaded": len(inp["lookups"]),
        "holds_applied": inp["holds_applied"],
        "names_scanned": {"withheld": len(inp["withheld"]), "all": len(inp["all_names"]),
                          "shown_unmasked": len(allowed)},
        "scans": {k: len(v) for k, v in scans.items()},
        "scan_findings": scans,
        "scans_clean": not any(scans.values()),
    }
