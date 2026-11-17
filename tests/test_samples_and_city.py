"""Smoke tests on sanitized in-repo samples (no live network required)."""
import json
from pathlib import Path

from tw.city_register import load_sample_csv
from tw.export import build_public_export
from tw.match import can_link
from tw.ocds import award_rows_from_release, is_cape_town_buyer
from tw.popia import assert_clean, find_forbidden_keys

ROOT = Path(__file__).resolve().parents[1]


def test_city_sample_csv_loads() -> None:
    rows = load_sample_csv()
    assert len(rows) == 3
    assert all(r["buyer_name"] == "City of Cape Town" for r in rows)
    assert all(r["right_of_reply"] == "Right of reply: pending" for r in rows)
    assert all(r["supplier_type"] == "juristic" for r in rows)
    assert {r["name_key"] for r in rows} == {"octopus electronics", "printegration", "zutari"}
    assert_clean(rows, context="city_sample")


def test_ocds_cape_town_samples_parse() -> None:
    path = ROOT / "data/samples/etenders-ocds/ocp-mirror-cape-town-award-samples.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["rows"], "sample must contain rows"
    parsed = []
    for i, raw in enumerate(payload["rows"], start=1):
        # Rehydrate a minimal release from the sanitized sample row.
        rel = {
            "ocid": raw["ocid"],
            "date": raw.get("release_date"),
            "buyer": {"id": raw.get("buyer_id"), "name": raw.get("buyer_name")},
            "tender": {
                "id": raw.get("tender_id"),
                "title": raw.get("tender_title"),
                "procurementMethod": raw.get("procurement_method"),
            },
            "awards": [
                {
                    "id": raw.get("award_id"),
                    "status": raw.get("award_status"),
                    "value": raw.get("award_value") or {},
                    "date": raw.get("award_date_field"),
                    "suppliers": [{"name": raw.get("supplier_name"), "id": raw.get("supplier_id")}],
                }
            ],
        }
        assert is_cape_town_buyer(raw.get("buyer_name"))
        rows = award_rows_from_release(
            rel,
            locator=f"sample:{i}",
            source_file=str(path),
            sha256="sample",
            retrieved_at=payload.get("publicfunds_copy_fetched_at_sast") or "unknown",
            source_url=payload.get("source_url") or "",
        )
        assert rows, raw
        parsed.extend(rows)
        assert all(r["young_supplier_indicator"] == "unknown" for r in rows)
        assert all(r["registration_year"] is None for r in rows)
        assert find_forbidden_keys(rows) == []
    public = build_public_export(parsed)
    for rec, src in zip(public, parsed, strict=True):
        if src["supplier_type"] != "juristic":
            assert rec["supplier_name"] is None
    assert_clean(public, context="sample_public")


def test_sample_zutari_would_match_city_row_on_two_details() -> None:
    city = [r for r in load_sample_csv() if r["name_key"] == "zutari"][0]
    award = {
        "supplier_name": "Zutari (Pty) Ltd.",
        "name_key": "zutari",
        "buyer_name": "City of Cape Town",
        "tender_title": "293C/2024/25",
    }
    assert can_link(award, city) is True
