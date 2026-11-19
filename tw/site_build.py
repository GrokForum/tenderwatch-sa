"""CHG-TW-006: load the DEV inputs, build the site and run the public-file scans."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tw.classification_report import withheld_names
from tw.config import load_config
from tw.public_scan import run_all
from tw.site import build_rows, build_site, load_lookups, shown_names

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "local" / "warehouse"
CLASSIFIED = WAREHOUSE / "awards_classified_chg_tw_002.jsonl"
CITY = WAREHOUSE / "city_register.jsonl"
LOOKUPS = ROOT / "data" / "local" / "lookups.csv"
EXPECTED_ROWS = 291


def _jsonl(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _date_only(s: str | None) -> str | None:
    return s[:10] if s and len(s) >= 10 and s[4] == "-" and s[7] == "-" else None


def load_inputs() -> dict:
    if not CLASSIFIED.is_file():
        raise FileNotFoundError("DEV export missing: run scripts/run_chg_tw_002_classify.py first")
    rows = _jsonl(CLASSIFIED)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows in the DEV export, got {len(rows)}")
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
            "withheld": withheld_names(rows), "all_names": all_names, "lookups": load_lookups(LOOKUPS)}


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
        "names_scanned": {"withheld": len(inp["withheld"]), "all": len(inp["all_names"]),
                          "shown_unmasked": len(allowed)},
        "scans": {k: len(v) for k, v in scans.items()},
        "scan_findings": scans,
        "scans_clean": not any(scans.values()),
    }
