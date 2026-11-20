"""CHG-TW-011: buyers beyond the City of Cape Town (DEV staging). Invented buyers and suppliers only."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from tw import national, site
from tw import site_build
from tw.ocds import iter_awards

CITY = "City of Cape Town"
METRO = "Testville Metropolitan Municipality"
DEPT = "Department of Invented Affairs"


def _release(ocid, buyer, supplier, award_id=1, title="T1/2025", date="2025-08-01T00:00:00Z", amount=1000.0):
    return {"ocid": ocid, "id": ocid + "-r", "date": date, "buyer": {"name": buyer, "id": "b"},
            "tender": {"title": title, "id": title},
            "awards": [{"id": award_id, "value": {"amount": amount, "currency": "ZAR"},
                        "suppliers": [{"name": supplier, "id": "0"}]}]}


def _gz(tmp_path: Path, releases) -> tuple[Path, str]:
    p = tmp_path / "full.jsonl.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        for r in releases:
            fh.write(json.dumps(r) + "\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def _cfg(**over):
    cfg = {"env": "DEV", "stages": {"stage1": [METRO], "all": "*"}, "default_stage": "stage1",
           "row_bounds": {"stage1": [1, 10], "all": [1, 10]},
           "municipal_buyer_pattern": "(?i)(\\bmunicipality\\b|\\bmetropolitan\\b|^city of )",
           "excluded_buyers": [CITY]}
    cfg.update(over)
    return cfg


RELEASES = [
    _release("ocds-fx-1", CITY, "Qwerty Pumps (Pty) Ltd"),
    _release("ocds-fx-2", METRO, "Zorblax Civil Engineering (Pty) Ltd"),
    _release("ocds-fx-3", METRO, "QWERTANE ZEPHYR SYSTEMS"),
    _release("ocds-fx-4", DEPT, "Cape Qwerty Engineering (Pty) Ltd"),
    _release("ocds-fx-5", "  testville   metropolitan municipality ", "Thandeka Qwertane Transport CC"),
]


def test_buyer_filter_stages_and_city_always_excluded():
    cfg = _cfg()
    f1 = national.buyer_filter_for("stage1", cfg)
    fa = national.buyer_filter_for("all", cfg)
    assert f1(METRO) and f1(" testville metropolitan  MUNICIPALITY") and not f1(DEPT) and not f1(CITY)
    assert fa(DEPT) and fa(METRO) and not fa(CITY) and not fa("") and not fa(None)
    with pytest.raises(ValueError):
        national.buyer_filter_for("nope", cfg)


def test_iter_awards_checks_the_pin_and_filters(tmp_path):
    p, sha = _gz(tmp_path, RELEASES)
    rows = list(iter_awards(p, retrieved_at="x", buyer_filter=national.buyer_filter_for("all", _cfg()),
                            expected_sha256=sha))
    assert sorted(r["ocid"] for r in rows) == ["ocds-fx-2", "ocds-fx-3", "ocds-fx-4", "ocds-fx-5"]
    assert all(r["registration_year"] is None and r["age_band"] == "unknown" for r in rows)  # no CIPC in eTenders
    assert all("/" not in r["source_file"] for r in rows)  # no box paths in rows
    with pytest.raises(ValueError, match="sha256 mismatch"):
        list(iter_awards(p, retrieved_at="x", buyer_filter=lambda b: True, expected_sha256="0" * 64))


def test_ingest_classifies_bounds_and_redacts(tmp_path):
    id_like = "".join(["80", "01", "01", "5009", "0", "8", "7"])  # built at run time; 13 digits, ID-shaped
    rel = RELEASES + [_release("ocds-fx-6", DEPT, "Qwerty Pumps (Pty) Ltd", title=id_like)]
    p, sha = _gz(tmp_path, rel)
    rows = national.ingest("all", cfg=_cfg(), ocds_path=p, expected_sha256=sha)
    by = {r["ocid"]: r for r in rows}
    assert by["ocds-fx-2"]["classification_status"] == "confirmed_juristic"
    assert by["ocds-fx-3"]["queue_reason"] == "no_suffix"
    assert by["ocds-fx-6"]["tender_title"] is None and by["ocds-fx-6"]["popia_redacted"] == ["tender_title", "tender_id"]
    s = national.summary(rows)
    assert s["rows"] == 5 and s["registration_year_known"] == 0 and s["fields_redacted_popia"] == 2
    with pytest.raises(national.StageOutOfBounds):
        national.ingest("all", cfg=_cfg(row_bounds={"all": [6, 9]}), ocds_path=p, expected_sha256=sha)


def test_municipal_buyers_by_pattern():
    rows = [{"buyer_name": METRO}, {"buyer_name": DEPT}]
    assert national.municipal_buyers(rows, _cfg()) == {METRO, CITY}


def _row(i, name, buyer, *, status="confirmed_juristic", reason=None, hold=False, date="2025-08-01", key=None):
    return {"ocid": f"ocds-fx-{i}", "award_id": str(i), "buyer_name": buyer, "tender_title": f"T{i}",
            "supplier_name": name, "name_key": key or name.lower(), "classification_status": status,
            "popia_hold": hold, "queue_reason": reason, "legal_sub_type": "company" if status == "confirmed_juristic" else None,
            "legal_form_link": "same_record", "legal_form_fact_label": "Confirmed",
            "award_date": date, "value_amount": 1000.0, "value_note": None, "city_matches": []}


def test_i1_is_per_buyer_and_municipal_only():
    rows = [_row(1, "Zorblax Holdings (Pty) Ltd", METRO, key="z"), _row(2, "Zorblax Holdings (Pty) Ltd", METRO, key="z"),
            _row(3, "Zorblax Holdings (Pty) Ltd", DEPT, key="z"), _row(4, "Zorblax Holdings (Pty) Ltd", DEPT, key="z")]
    m = site.build_rows(rows, municipal_buyers={METRO, CITY})
    ind = {d["buyer"]: d["indicator"] for d in m["rows"]}
    assert "received 2 awards" in ind[METRO] and METRO in ind[METRO]
    assert ind[DEPT] is None  # not a municipal buyer: no municipal financial year
    m_all = site.build_rows(rows)  # City-only behaviour (every buyer), still per buyer
    assert all("received 2 awards" in d["indicator"] for d in m_all["rows"])


def test_held_national_row_has_no_city_citation_and_pages_say_national():
    rows = [_row(1, "Zorblax Holdings (Pty) Ltd", METRO, hold=True), _row(2, "Qwerty Pumps (Pty) Ltd", CITY, hold=True)]
    m = site.build_rows(rows, municipal_buyers={METRO, CITY})
    srcs = {d["buyer"]: [s["label"] for s in d["sources"]] for d in m["rows"]}
    assert not any("City of Cape Town" in s for s in srcs[METRO])
    assert any("City of Cape Town" in s for s in srcs[CITY])
    idx = site.render_index(m, etenders_retrieved="2026-10-19")
    assert "This draft covers 2 buyers" in idx and "eTenders alone" in idx
    assert "Buyers beyond the City of Cape Town" in site.render_method(m, etenders_retrieved="2026-10-19")
    city_only = site.build_rows([rows[1]])
    assert "This draft covers one buyer, the City of Cape Town" in site.render_index(city_only, etenders_retrieved="x")
    assert "Buyers beyond" not in site.render_method(city_only, etenders_retrieved="x")


def test_pending_names_shown_elsewhere_exempts_only_plain_pending():
    rows = [_row(1, "Hydroqwerty Systems", CITY),
            _row(2, "Hydroqwerty Systems", METRO, status="check_queue", reason="no_suffix"),
            _row(3, "Zorblax Pumps", CITY),
            _row(4, "Zorblax Pumps", METRO, status="check_queue", reason="looks_like_personal_name", hold=True)]
    withheld = {"Hydroqwerty Systems", "Zorblax Pumps"}
    allowed = {"HYDROQWERTY SYSTEMS", "Zorblax Pumps"}
    assert site_build.pending_names_shown_elsewhere(rows, withheld, allowed) == {"Hydroqwerty Systems"}


def test_run_build_refuses_a_national_row_that_repeats_a_city_row(tmp_path, monkeypatch):
    city = [_row(1, "Zorblax Civil Engineering (Pty) Ltd", CITY, key="zce")]
    cls = tmp_path / "c.jsonl"
    cls.write_text(json.dumps(city[0]) + "\n", encoding="utf-8")
    monkeypatch.setattr(site_build, "CLASSIFIED", cls)
    monkeypatch.setattr(site_build, "EXPECTED_ROWS", 1)
    with pytest.raises(site.UnsafeBuild, match="repeats a City row"):
        site_build.load_inputs(extra_rows=[dict(city[0])])


# --- DEV data (git-ignored; skipped on a fresh clone) --------------------------


def test_dev_stage1_counts_and_scans(tmp_path):
    from tw.config import load_config, ocds_input_path
    if not site_build.CLASSIFIED.is_file() or not site_build.HOLDS.is_file():
        pytest.skip("skipped: the DEV export and holds file are git-ignored")
    try:
        ocds_input_path(load_config())
    except FileNotFoundError:
        pytest.skip("skipped: the pinned eTenders file is not on this machine")
    rows = national.ingest("stage1")
    assert national.summary(rows)["rows"] == 138 and national.summary(rows)["buyers"] == 2
    res = site_build.run_build(tmp_path, extra_rows=rows,
                               municipal_buyers=national.municipal_buyers(rows, national.load_national_config()))
    assert res["rows_total"] == 429 and res["buyers"] == 3
    assert res["group_counts"] == {"unmasked": 56, "held": 10, "personal": 36, "pending": 321, "withheld": 6}
    assert res["names_scanned"]["pending_names_shown_elsewhere"] == 1
    assert res["scans_clean"], res["scan_findings"]
