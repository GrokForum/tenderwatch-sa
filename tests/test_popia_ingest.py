"""POPIA: contacts, addresses and ID keys must not reach the warehouse or export."""
import pytest

from tw.export import build_public_export
from tw.normalise import registration_year_from_cipc
from tw.ocds import award_rows_from_release
from tw.popia import assert_clean, find_forbidden_keys, find_id_or_contact_leaks, strip_forbidden
from tw.supplier_type import public_export_rows


def _release(**extra):
    rel = {
        "ocid": "ocds-9t57fa-fixture-1",
        "date": "2026-06-15T00:00:00Z",
        "buyer": {"id": "59", "name": "City of Cape Town"},
        "tender": {
            "id": "100001",
            "title": "001Q/2026/27",
            "procurementMethod": "open",
            "contactPerson": "SHOULD-DROP Person",
        },
        "parties": [
            {
                "name": "Fixture Tools (Pty) Ltd",
                "id": "99",
                "roles": ["supplier"],
                "address": {"streetAddress": "1 Private Road", "postalCode": "8001", "countryName": "South Africa"},
                "contactPoint": {"name": "SHOULD-DROP", "email": "leak@example.com", "telephone": "0210000000"},
            }
        ],
        "awards": [
            {
                "id": "1",
                "status": "active",
                "value": {"amount": 50000, "currency": "ZAR"},
                "suppliers": [{"name": "Fixture Tools (Pty) Ltd", "id": "99"}],
            }
        ],
        "contracts": [{"awardID": "1", "dateSigned": "2026-06-01"}],
    }
    rel.update(extra)
    return rel


def test_parser_drops_contact_and_address_keys() -> None:
    rows = award_rows_from_release(
        _release(),
        locator="fixture:line 1",
        source_file="fixture.jsonl",
        sha256="abc",
        retrieved_at="2026-11-17 10:00 SAST (Africa/Johannesburg)",
    )
    assert len(rows) == 1
    row = rows[0]
    assert find_forbidden_keys(row) == []
    assert find_id_or_contact_leaks(row) == []
    blob = str(row)
    assert "SHOULD-DROP" not in blob
    assert "1 Private Road" not in blob
    assert "leak@example.com" not in blob
    assert "0210000000" not in blob
    assert row["supplier_type"] == "juristic"
    assert row["young_supplier_indicator"] == "unknown"
    assert row["age_band"] == "unknown"
    assert row["right_of_reply"] == "Right of reply: pending"
    assert row["fact_label"] == "Confirmed"
    assert row["award_date"] == "2026-06-01"
    assert row["award_date_basis"] == "contract.dateSigned"
    assert_clean(rows, context="test")


def test_strip_forbidden_removes_contactpoint_address_contactperson() -> None:
    cleaned = strip_forbidden(
        {
            "tender": {"contactPerson": "X"},
            "parties": [{"address": {"streetAddress": "Y"}, "contactPoint": {"email": "a@b.c"}}],
            "ok": 1,
        }
    )
    assert "contactPerson" not in cleaned["tender"]
    assert "address" not in cleaned["parties"][0]
    assert "contactPoint" not in cleaned["parties"][0]
    assert cleaned["ok"] == 1


def test_assert_clean_fails_on_id_or_email() -> None:
    with pytest.raises(AssertionError):
        assert_clean([{"notes": "ID 8001015009087"}], context="x")
    with pytest.raises(AssertionError):
        assert_clean([{"notes": "write to leak@example.com"}], context="x")
    with pytest.raises(AssertionError):
        assert_clean([{"contactPoint": {"email": "x@y.z"}}], context="x")


def test_csd_is_not_a_year() -> None:
    rel = _release()
    rel["awards"][0]["suppliers"][0]["name"] = "Fixture Tools (Pty) Ltd MAAA1234567"
    rows = award_rows_from_release(
        rel,
        locator="fixture:line 1",
        source_file="fixture.jsonl",
        sha256="abc",
        retrieved_at="2026-11-17",
    )
    assert rows[0]["csd_no"] == "MAAA1234567"
    assert rows[0]["registration_year"] is None
    assert rows[0]["young_supplier_indicator"] == "unknown"
    assert registration_year_from_cipc(None) is None


def test_sourced_cipc_sets_confirmed_year_and_band() -> None:
    rel = _release()
    rel["awards"][0]["suppliers"][0]["name"] = "Fixture Tools (Pty) Ltd 2026/123456/07"
    rows = award_rows_from_release(
        rel,
        locator="fixture:line 1",
        source_file="fixture.jsonl",
        sha256="abc",
        retrieved_at="2026-11-17",
        source_url="https://example.example/public-document",
    )
    row = rows[0]
    assert row["cipc_reg_no"] == "2026/123456/07"
    assert row["registration_year"] == 2026
    assert row["registration_year_label"] == "Confirmed"
    assert row["registration_year_source_url"] == "https://example.example/public-document"
    assert row["young_supplier_indicator"] == "yes"
    assert row["age_band"] == "same"
    assert "0–23 months" in row["indicator_window"]


def test_natural_person_name_withheld_even_with_year_string() -> None:
    rel = _release()
    rel["awards"][0]["suppliers"][0]["name"] = "A. Q. Testperson t/a Testperson Crafts 2026/123456/07"
    rows = award_rows_from_release(
        rel,
        locator="fixture:line 1",
        source_file="fixture.jsonl",
        sha256="abc",
        retrieved_at="2026-11-17",
    )
    row = rows[0]
    assert row["supplier_type"] == "natural_person"
    assert row["registration_year"] is None
    assert row["young_supplier_indicator"] == "unknown"
    public = build_public_export(rows)
    assert public[0]["supplier_name"] is None
    exported = public_export_rows(rows)
    assert exported[0]["supplier_name"] is None
