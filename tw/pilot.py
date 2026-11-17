"""Orchestrate the CHG-TW-001 DEV pilot (local box, no push, no PublicFunds writes)."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tw.city_register import light_fetch, load_sample_csv
from tw.config import EXPECTED_OCDS_SHA256, PUBLICFUNDS_PIN, data_dir, load_config, ocds_input_path
from tw.export import write_public_export
from tw.match import agreeing_details, can_link
from tw.ocds import iter_cape_town_awards, sha256_file
from tw.popia import assert_clean
from tw.warehouse import write_checked_jsonl

SAST = timezone(timedelta(hours=2), name="SAST")
REPORT_PATH_DEFAULT = Path(__file__).resolve().parents[1] / "docs" / "dev" / "CHG-TW-001-run-report.md"


def _now() -> str:
    return datetime.now(SAST).strftime("%Y-%m-%d %H:%M SAST (Africa/Johannesburg)")


def attach_matches(awards: list[dict], city_rows: list[dict]) -> list[dict]:
    for award in awards:
        hits = []
        for city in city_rows:
            if can_link(award, city):
                hits.append(
                    {
                        "tts_reference": city.get("tts_reference"),
                        "decision_reference": city.get("decision_reference"),
                        "period": city.get("period"),
                        "source_url": city.get("source_url"),
                        "details": agreeing_details(award, city),
                    }
                )
        award["city_matches"] = hits
        if hits:
            # Public-safe pointers only (references, not a second copy of a name).
            award["matched_city_tts"] = ";".join(h["tts_reference"] or "" for h in hits)
            award["match_details"] = ";".join(",".join(h["details"]) for h in hits)
        else:
            award["matched_city_tts"] = None
            award["match_details"] = None
    return awards


def run(report_path: Path | None = None) -> dict:
    cfg = load_config()
    if cfg.get("env") != "DEV":
        raise RuntimeError("pilot runs in DEV only")
    started = _now()
    root = data_dir(cfg)
    raw_city = root / "raw" / "city-of-cape-town"
    warehouse = root / "warehouse"
    export_dir = root / "export"

    ocds_path = ocds_input_path(cfg)
    digest = sha256_file(ocds_path)
    if digest != EXPECTED_OCDS_SHA256:
        raise ValueError(f"refusing to ingest unexpected etenders_ocds digest {digest}")
    retrieved_at = cfg["etenders_ocds"]["publicfunds_fetched_at_sast"]
    awards = list(iter_cape_town_awards(ocds_path, retrieved_at=retrieved_at))
    assert_clean(awards, context="warehouse.awards")

    city_fetch = light_fetch(raw_city, cfg)
    city_rows = list(city_fetch.get("rows") or [])
    city_source = "live_fetch"
    if not city_rows:
        city_rows = load_sample_csv()
        city_source = "in_repo_october_2026_sample" + ("; live fetch had no parsed rows" if not city_fetch.get("errors") else "; live fetch failed or was skipped")
    assert_clean(city_rows, context="warehouse.city_register")

    awards = attach_matches(awards, city_rows)
    n_awards = write_checked_jsonl(warehouse / "awards.jsonl", awards, context="warehouse.awards")
    n_city = write_checked_jsonl(warehouse / "city_register.jsonl", city_rows, context="warehouse.city_register")
    public = write_public_export(export_dir, awards)

    by_type = Counter(a.get("supplier_type") for a in awards)
    by_indicator = Counter(a.get("young_supplier_indicator") for a in awards)
    by_band = Counter(a.get("age_band") for a in awards)
    n_matched_awards = sum(1 for a in awards if a.get("city_matches"))
    n_match_links = sum(len(a.get("city_matches") or []) for a in awards)
    n_public_names = sum(1 for r in public if r.get("supplier_name"))
    n_juristic_public = sum(1 for r in public if r.get("supplier_type") == "juristic" and r.get("supplier_name"))

    report = {
        "rfc": "CHG-TW-001",
        "env": "DEV",
        "run_at": started,
        "finished_at": _now(),
        "publicfunds_pin": PUBLICFUNDS_PIN,
        "ocds_path": str(ocds_path),
        "ocds_sha256": digest,
        "awards_loaded": n_awards,
        "unique_ocids": len({a.get("ocid") for a in awards}),
        "suppliers_by_type": dict(by_type),
        "indicator_counts": dict(by_indicator),
        "age_band_counts": dict(by_band),
        "city_register_rows": n_city,
        "city_register_source": city_source,
        "city_fetch": {
            "fetched": city_fetch.get("fetched"),
            "skipped": city_fetch.get("skipped"),
            "errors": [str(e) for e in (city_fetch.get("errors") or [])],
            "robots_allowed": city_fetch.get("robots_allowed"),
            "parsed_rows": len(city_fetch.get("rows") or []),
        },
        "matches": {
            "awards_with_at_least_one_city_link": n_matched_awards,
            "link_pairs": n_match_links,
        },
        "public_export_rows": len(public),
        "public_export_named_suppliers": n_public_names,
        "public_export_named_juristic": n_juristic_public,
        "warehouse_dir": str(warehouse),
        "export_dir": str(export_dir),
    }
    _write_report(report_path or REPORT_PATH_DEFAULT, report)
    (warehouse / "run-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    typ = report["suppliers_by_type"]
    ind = report["indicator_counts"]
    band = report["age_band_counts"]
    fetch = report["city_fetch"]
    body = f"""# CHG-TW-001 DEV run report

Environment: **DEV** (local box only). No push, no Pages, no TEST/PROD, no PublicFunds edits.

- Run: {report['run_at']} to {report['finished_at']} (Africa/Johannesburg)
- PublicFunds pin: `{report['publicfunds_pin']}` (read-only)
- OCDS input: `{report['ocds_path']}`
- SHA-256: `{report['ocds_sha256']}` (matches the RFC / survey file)

## Counts (not invented)

| Measure | Count |
|---|---|
| Award–supplier rows loaded (City of Cape Town) | {report['awards_loaded']} |
| Distinct award OCIDs | {report['unique_ocids']} |
| `supplier_type` juristic | {typ.get('juristic', 0)} |
| `supplier_type` natural_person | {typ.get('natural_person', 0)} |
| `supplier_type` unknown | {typ.get('unknown', 0)} |
| Indicator `yes` | {ind.get('yes', 0)} |
| Indicator `no` | {ind.get('no', 0)} |
| Indicator `unknown` | {ind.get('unknown', 0)} |
| Age band `same` | {band.get('same', 0)} |
| Age band `-1` | {band.get('-1', 0)} |
| Age band `-2` | {band.get('-2', 0)} |
| Age band `older` | {band.get('older', 0)} |
| Age band `unknown` | {band.get('unknown', 0)} |
| City register rows ingested | {report['city_register_rows']} |
| Awards with at least one two-detail City link | {report['matches']['awards_with_at_least_one_city_link']} |
| City link pairs (two-detail rule) | {report['matches']['link_pairs']} |
| Public export rows | {report['public_export_rows']} |
| Named suppliers in the public export (juristic only) | {report['public_export_named_suppliers']} |

City register source: {report['city_register_source']}.

Light fetch: fetched={fetch.get('fetched') or []}; skipped={fetch.get('skipped') or []}; errors={fetch.get('errors') or []}; parsed_rows={fetch.get('parsed_rows')}.

All award rows are fact-labelled **Confirmed** as published by the source. Registration year and the young-supplier indicator are **Unknown** unless a sourced CIPC number in a free public document supplied a year (labelled Confirmed, with a link). `Right of reply: pending` is stored on every row. Nothing was sent or published.

Attribution: National Treasury / OCPO eTenders OCDS; source https://data.open-contracting.org/en/publication/143 and policy https://data.etenders.gov.za/Home/LearnMore. City of Cape Town monthly award register where fetched or sampled, with provenance next to the local file.
"""
    path.write_text(body, encoding="utf-8")
