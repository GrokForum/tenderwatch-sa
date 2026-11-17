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


def test_city_layout_parser_attaches_pending_vendors() -> None:
    from tw.city_register import parse_layout_text

    text = """
TTS Reference   Decision Reference   Description          Vendor                         Date of decision
                                                      Fixture Plant (Pty) Ltd.
123S/2026/27    SCMB 01/10/26        HIRE OF EQUIPMENT    Fixture Trucks (Pty) Ltd.      10/5/2026
"""
    # Build a header with realistic columns by padding
    header = (
        "TTS Reference   Decision Reference   Description"
        + " " * 20
        + "Vendor"
        + " " * 20
        + "Date of decision"
    )
    pending = " " * header.find("Vendor") + "Fixture Plant (Pty) Ltd."
    row = (
        "123S/2026/27    SCMB 01/10/26        HIRE OF EQUIPMENT"
        + " " * (header.find("Vendor") - len("123S/2026/27    SCMB 01/10/26        HIRE OF EQUIPMENT"))
        + "Fixture Trucks (Pty) Ltd."
        + " " * 4
        + "10/5/2026"
    )
    text = "\n".join([header, pending, row, ""])
    rows = parse_layout_text(
        text,
        source_url="https://example.example/tenders-awarded-october-2026.pdf",
        source_file="fixture.pdf",
        retrieved_at="2026-11-17 10:57 SAST (Africa/Johannesburg)",
        period="2026-10",
    )
    names = [r["supplier_name"] for r in rows]
    assert "Fixture Plant (Pty) Ltd" in names
    assert "Fixture Trucks (Pty) Ltd" in names
    assert all(r["tts_reference"] == "123S/2026/27" for r in rows)
    assert all(r["award_date"] == "2026-10-05" for r in rows)
    assert all(r["supplier_type"] == "juristic" for r in rows)


def test_implausible_vendor_fragments_are_dropped() -> None:
    from tw.city_register import is_plausible_vendor

    assert is_plausible_vendor("Zutari (Pty) Ltd")
    assert not is_plausible_vendor(";")
    assert not is_plausible_vendor("2")
    assert not is_plausible_vendor("CC;")
    assert not is_plausible_vendor("2026/03/23")
    assert not is_plausible_vendor("")


def test_light_fetch_pauses_between_requests(tmp_path) -> None:
    """Offline: injected sleep records the configured pause between City requests."""
    from tw.city_register import light_fetch

    pauses: list[float] = []
    urls: list[str] = []

    def fake_sleep(seconds: float) -> None:
        pauses.append(seconds)

    def fake_get(url: str, dest=None, timeout: int = 60) -> bytes:
        urls.append(url)
        if "robots" in url:
            body = b"User-agent: *\nAllow: /\n"
        else:
            body = b"<html><body>no pdfs</body></html>"
        if dest is not None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
        return body

    cfg = {
        "city_register": {
            "robots_url": "https://example.example/robots.txt",
            "index_url": "https://example.example/tenders-awarded/",
            "known_pdf": None,
            "request_pause_s": 1.5,
        }
    }
    result = light_fetch(tmp_path, cfg, sleep=fake_sleep, http_get=fake_get)
    assert urls == [
        "https://example.example/robots.txt",
        "https://example.example/tenders-awarded/",
    ]
    assert pauses == [1.5]
    assert result["errors"] == []
    assert "https://example.example/robots.txt" in result["fetched"]


def test_robots_unavailable_fails_closed(tmp_path) -> None:
    """Offline: if robots.txt cannot be read, no further City requests are made."""
    from tw.city_register import light_fetch

    urls: list[str] = []

    def fake_sleep(seconds: float) -> None:
        raise AssertionError("must not pause or continue after a robots failure")

    def fake_get(url: str, dest=None, timeout: int = 60) -> bytes:
        urls.append(url)
        raise OSError("robots unavailable")

    cfg = {
        "city_register": {
            "robots_url": "https://example.example/robots.txt",
            "index_url": "https://example.example/tenders-awarded/",
            "known_pdf": "https://example.example/tenders-awarded-october-2026.pdf",
        }
    }
    result = light_fetch(tmp_path, cfg, sleep=fake_sleep, http_get=fake_get)
    assert urls == ["https://example.example/robots.txt"]
    assert result["rows"] == []
    assert result["fetched"] == []
    assert any("robots.txt" in e for e in result["errors"])
    assert any("fail closed" in s for s in result["skipped"])
    blob = " ".join(result["errors"] + result["skipped"])
    assert "Allow: /" not in blob
