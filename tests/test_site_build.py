"""CHG-TW-006: DRAFT register site build. Invented names only; no real supplier or person."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tw import site
from tw.public_scan import run_all, scan_names, scan_paths_and_bot_names, scan_pii, scan_wording, public_files


def _row(i, name, *, status="confirmed_juristic", hold=False, reason=None, sub="company",
         link="name_and_buyer_only", label="Reported", key=None, date="2025-08-01", value=1000000.0, note=None):
    return {
        "ocid": f"ocds-fx-{i}", "award_id": str(i), "buyer_name": "City of Cape Town", "tender_title": f"{i}Q/2025/26",
        "supplier_name": name, "name_key": key or name.lower(), "classification_status": status,
        "popia_hold": hold, "queue_reason": reason, "legal_sub_type": sub if status == "confirmed_juristic" else None,
        "legal_form_link": link if status == "confirmed_juristic" else None,
        "legal_form_fact_label": label if status == "confirmed_juristic" else None,
        "award_date": date, "value_amount": value, "value_note": note,
        "city_matches": [{"tts_reference": f"{i}Q/2025/26", "period": "2026-05",
                          "source_url": "https://www.capetown.gov.za/media/example/tenders-awarded-may-2026.pdf"}],
    }


def fixture_rows():
    return [
        _row(1, "Northriver Widgets (Pty) Ltd", key="northriver"),
        _row(2, "Northriver Widgets (Pty) Ltd", key="northriver", date="2025-09-01"),
        _row(3, "Northriver Widgets (Pty) Ltd", key="northriver", date="2026-01-15", value=0.0, note="zero_placeholder"),
        _row(4, "Harbour Lights CC", sub="close_corporation", link="tender_ref", label="Confirmed", key="harbour"),
        _row(5, "Qwertane Zephyr Joint Venture", sub="jv", link="same_record", label="Confirmed", key="qzjv"),
        _row(6, "Testfield Qwerty (Pty) Ltd", hold=True, key="testfield"),
        _row(7, "R Qwertane and Associates", status="check_queue", hold=True, reason="looks_like_personal_name"),
        _row(8, "QWERTANE ZEPHYR SYSTEMS", status="check_queue", reason="no_suffix"),
        _row(9, "Mismatchia Trading", status="check_queue", reason="name_mismatch_between_sources"),
    ]


# --- mask ------------------------------------------------------------------

@pytest.mark.parametrize("name,mask", [
    ("Qwertane Widget Supplies", "Q*****s"),
    ("Northriver Widgets (Pty) Ltd", "N*****s"),
    ("(R Qwertane and Associates)", "R*****s"),
    ("Harbour Lights CC", "H*****s"),
    ("Harbour Lights C.C.", "H*****s"),
    ("Zebra Qwop (RF) (Pty) Ltd", "Z*****p"),
    ("élan qwerty", "E*****y"),
    ("A", "*******"),
    ("", "*******"),
    ("(Pty) Ltd", "P*****y"),  # only legal words: the stem keeps what is left
])
def test_mask_is_fixed_seven_characters(name, mask):
    assert site.mask_name(name) == mask
    assert len(site.mask_name(name)) == 7


def test_mask_hides_length():
    assert len(site.mask_name("Ab")) == len(site.mask_name("A very long invented supplier name for testing")) == 7


# --- groups, year cells, counts ----------------------------------------------

def test_every_row_in_exactly_one_group_and_counts_add_up():
    rows = fixture_rows()
    model = site.build_rows(rows, etenders_retrieved="2026-10-19")
    gc = model["group_counts"]
    assert gc == {"unmasked": 5, "held": 1, "personal": 1, "pending": 1, "withheld": 1}
    assert sum(gc.values()) == model["total"] == len(rows)
    assert len(model["rows"]) == len(rows) - gc["withheld"]
    assert sum(model["year_counts"].values()) == len(rows)


def test_withheld_row_and_names_never_shown(tmp_path: Path):
    site.build_site(fixture_rows(), tmp_path, etenders_retrieved="2026-10-19")
    blob = "".join(p.read_text(encoding="utf-8") for p in public_files(tmp_path)).upper()
    for hidden in ("MISMATCHIA", "R QWERTANE", "QWERTANE ZEPHYR SYSTEMS", "TESTFIELD", "OCDS-FX-9", "9Q/2025/26",
                   "OCDS-FX-6", "6Q/2025/26", "OCDS-FX-7", "7Q/2025/26"):
        assert hidden not in blob, hidden
    assert "NORTHRIVER WIDGETS (PTY) LTD" in blob  # unmasked row is named
    assert "T*****Y" in blob and "R*****S" in blob
    assert site.NAME_PENDING.upper() in blob


def test_year_cells_without_lookups():
    model = site.build_rows(fixture_rows())
    cells = {d["supplier"]: d["year_cell"] for d in model["rows"]}
    assert cells["T*****y"] == site.YEAR_UNKNOWN  # held: no lookup returned
    assert cells["R*****s"] == site.YEAR_MASKED_ROW
    assert cells[site.NAME_PENDING] == site.YEAR_UNKNOWN
    assert model["year_counts"] == {"Year: Unknown": 7, "Year: not shown (masked row)": 1, "Row withheld (no cell)": 1}


def test_year_cells_with_lookups():
    lk = {
        "northriver": {"result": "found", "year": 2019, "label": "Confirmed"},
        "harbour": {"result": "found", "year": 2021, "label": "Reported, Unconfirmed"},
        "qzjv": {"result": "found", "year": 2020, "label": "Confirmed"},
        "testfield": {"result": "found", "year": 2022, "label": "Reported, Unconfirmed"},
        "r qwertane and associates": {"result": "found", "year": 2023, "label": "Confirmed"},
        "qwertane zephyr systems": {"result": "found", "year": 2023, "label": "Confirmed"},
    }
    model = site.build_rows(fixture_rows(), lookups=lk)
    by = {}
    for d in model["rows"]:
        by.setdefault(d["supplier"], set()).add(d["year_cell"])
    assert by["Northriver Widgets (Pty) Ltd"] == {"Year: 2019, Confirmed"}
    assert by["Harbour Lights CC"] == {site.YEAR_PLACEHOLDER}
    assert by["Qwertane Zephyr Joint Venture"] == {site.YEAR_UNKNOWN}  # a JV has no CIPC year
    assert by["T*****y"] == {site.YEAR_PLACEHOLDER}  # held company row carries the placeholder
    assert by["R*****s"] == {site.YEAR_MASKED_ROW}  # personal-looking rows never take a lookup
    assert by[site.NAME_PENDING] == {site.YEAR_UNKNOWN}
    for d in model["rows"]:
        if d["group"] in ("held", "personal") or d["year_cell"] == site.YEAR_PLACEHOLDER:
            assert not re.search(r"[0-9]", d["year_cell"])
    assert sum(model["year_counts"].values()) == 9


@pytest.mark.parametrize("result", ["not_found", "several_matches"])
def test_held_row_unknown_on_no_single_match(result):
    model = site.build_rows(fixture_rows(), lookups={"testfield": {"result": result, "year": None, "label": None}})
    assert [d["year_cell"] for d in model["rows"] if d["group"] == "held"] == [site.YEAR_UNKNOWN]


def test_held_row_with_confirmed_year_stops_the_build():
    with pytest.raises(site.UnsafeBuild):
        site.build_rows(fixture_rows(), lookups={"testfield": {"result": "found", "year": 2020, "label": "Confirmed"}})


def test_masked_rows_carry_no_identifying_detail():
    model = site.build_rows(fixture_rows())
    for d in model["rows"]:
        if d["group"] in ("held", "personal"):
            assert d["tender_reference"] == d["ocds_id"] == ""
            assert d["indicator"] is None and not d["right_of_reply"]
            assert all("register-level" in s["label"] for s in d["sources"])
            assert d["popia_note"]
    personal = [d for d in model["rows"] if d["group"] == "personal"][0]
    assert personal["legal_form"] == "Unknown"


def test_label_reported_is_always_written_unconfirmed(tmp_path: Path):
    site.build_site(fixture_rows(), tmp_path)
    assert scan_wording(public_files(tmp_path), tmp_path) == []
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Reported, Unconfirmed" in text
    assert site.label_text("Reported") == "Reported, Unconfirmed"
    with pytest.raises(site.UnsafeBuild):
        site.label_text("Probably")


def test_i1_indicator_counts_per_financial_year():
    model = site.build_rows(fixture_rows())
    nr = [d for d in model["rows"] if d["supplier"].startswith("Northriver")]
    fy2526 = [d for d in nr if d["award_date"] >= "2025-07-01"]
    assert len(fy2526) == 3
    assert all("received 3 awards" in d["indicator"] and d["indicator_highlight"] for d in fy2526)
    assert all("not a finding" in d["indicator"] and d["right_of_reply"] == "Right of reply: pending" for d in nr)
    assert all("2 have no usable value" not in d["indicator"] for d in fy2526)
    assert all("1 of the 3 have no usable value" in d["indicator"] for d in fy2526)
    assert site.financial_year("2025-06-30") == "2024/25" and site.financial_year("2025-07-01") == "2025/26"


# --- pages -----------------------------------------------------------------

def test_every_page_has_draft_noindex_privacy_csp(tmp_path: Path):
    site.build_site(fixture_rows(), tmp_path)
    pages = sorted(tmp_path.rglob("*.html"))
    assert {p.relative_to(tmp_path).as_posix() for p in pages} == {
        "index.html", "method/index.html", "privacy/index.html", "404.html"}
    for p in pages:
        t = p.read_text(encoding="utf-8")
        assert '<meta name="robots" content="noindex, nofollow">' in t, p
        assert "<strong>DRAFT.</strong>" in t and "<title>DRAFT · " in t, p
        assert 'href="/privacy/"' in t, p
        assert 'http-equiv="Content-Security-Policy"' in t and "script-src" not in t.split("Content-Security-Policy")[0], p
        assert '<link rel="icon" href="data:,">' in t, p
        assert "<script" not in t, p
    assert (tmp_path / "robots.txt").read_text() == "User-agent: *\nDisallow: /\n"
    priv = (tmp_path / "privacy" / "index.html").read_text(encoding="utf-8")
    assert "mailto:privacy@grokforum.site" in priv and "GrokForum" in priv
    assert "its buyer and usable value" in priv  # masked rows have no tender reference
    assert "https://inforegulator.org.za/" in priv


def test_build_is_deterministic(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    ma = site.build_site(fixture_rows(), a, etenders_retrieved="2026-10-19")
    mb = site.build_site(fixture_rows(), b, etenders_retrieved="2026-10-19")
    assert ma == mb
    for rel in site.MANAGED_FILES:
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel
    m = json.loads((a / "manifest.json").read_text())
    assert m["status"] == "DRAFT" and m["rows_total"] == 9 and set(m["files"]) == set(site.MANAGED_FILES) - {"manifest.json"}


def test_lookups_file_validation(tmp_path: Path):
    p = tmp_path / "lookups.csv"
    p.write_text("name_key,result,registration_year,registration_year_label\n"
                 "northriver,found,2019,Confirmed\nharbour,found,2021,Reported\nx,not_found,,\n", encoding="utf-8")
    lk = site.load_lookups(p)
    assert lk["northriver"] == {"result": "found", "year": 2019, "label": "Confirmed"}
    assert lk["harbour"]["label"] == "Reported, Unconfirmed"
    assert site.load_lookups(tmp_path / "absent.csv") == {}
    p.write_text("name_key,result,registration_year,registration_year_label\nn,found,19x9,Confirmed\n", encoding="utf-8")
    with pytest.raises(site.UnsafeBuild):
        site.load_lookups(p)


def test_unknown_status_fails_closed():
    with pytest.raises(site.UnsafeBuild):
        site.row_group({"classification_status": "something_new"})
    assert site.row_group({"classification_status": "check_queue", "queue_reason": "ambiguous_suffix"}) == "withheld"


# --- scans -----------------------------------------------------------------

def test_scans_pass_on_clean_build(tmp_path: Path):
    rows = fixture_rows()
    site.build_site(rows, tmp_path)
    model = site.build_rows(rows)
    withheld = {"Testfield Qwerty (Pty) Ltd", "R Qwertane and Associates", "QWERTANE ZEPHYR SYSTEMS", "Mismatchia Trading"}
    res = run_all(tmp_path, withheld=withheld, all_names={r["supplier_name"] for r in rows},
                  allowed=site.shown_names(model["rows"]))
    assert res == {k: [] for k in res}, res


def test_scans_catch_planted_problems(tmp_path: Path):
    (tmp_path / "a.html").write_text(
        "mail someone@example.org, call 082 555 1234 or +27 21 555 1234, id 1234567890123, "
        "lives at 12 Example Street; built in /workspace/x by ChatGPT; a corrupt deal; label Reported here; "
        "Mismatchia Trading", encoding="utf-8")
    files = public_files(tmp_path)
    pii = scan_pii(files, tmp_path)
    assert any("email" in f for f in pii) and any("phone" in f for f in pii)
    assert any("13-digit" in f for f in pii) and any("address" in f for f in pii)
    pb = scan_paths_and_bot_names(files, tmp_path)
    assert any("private path" in f for f in pb) and any("bot, agent" in f for f in pb)
    (tmp_path / "b.html").write_text("an invented agent name: Zorblax", encoding="utf-8")
    assert scan_paths_and_bot_names([tmp_path / "b.html"], tmp_path, extra=["zorblax"]) != []
    assert scan_paths_and_bot_names([tmp_path / "b.html"], tmp_path, extra=[]) == []
    w = scan_wording(files, tmp_path)
    assert any("loaded word" in f for f in w) and any("bare 'Reported'" in f for f in w)
    assert scan_names(files, tmp_path, {"Mismatchia Trading"}) != []
    assert "Mismatchia" not in " ".join(scan_names(files, tmp_path, {"Mismatchia Trading"}))  # never echo the name


def test_role_address_and_grokforum_are_allowed(tmp_path: Path):
    (tmp_path / "p.html").write_text("Contact privacy@grokforum.site. Responsible party: GrokForum.", encoding="utf-8")
    files = public_files(tmp_path)
    assert scan_pii(files, tmp_path) == [] and scan_paths_and_bot_names(files, tmp_path) == []


def test_withheld_name_also_shown_is_a_finding(tmp_path: Path):
    (tmp_path / "p.html").write_text("Northriver Widgets (Pty) Ltd", encoding="utf-8")
    files = public_files(tmp_path)
    assert scan_names(files, tmp_path, {"Northriver Widgets (Pty) Ltd"}, {"Northriver Widgets (Pty) Ltd"}) != []
    assert scan_names(files, tmp_path, {"Northriver Widgets (Pty) Ltd"}, {"Northriver Widgets (Pty) Ltd"},
                      conflicts_are_findings=False) == []


# --- DEV data (git-ignored; skipped on a fresh clone) --------------------------

def test_dev_export_counts_and_scans(tmp_path: Path):
    from tw import site_build
    if not site_build.CLASSIFIED.is_file():
        pytest.skip("skipped: the DEV export is git-ignored; run scripts/run_chg_tw_002_classify.py first")
    res = site_build.run_build(tmp_path)
    assert res["rows_total"] == 291
    assert res["group_counts"] == {"unmasked": 58, "held": 8, "personal": 27, "pending": 192, "withheld": 6}
    if res["lookups_loaded"] == 0:
        assert res["year_counts"] == {"Year: Unknown": 258, "Year: not shown (masked row)": 27,
                                      "Row withheld (no cell)": 6}
    assert res["tracked_holds_applied"] == 3
    assert res["names_scanned"]["withheld"] == 203 and res["names_scanned"]["all"] == 718
    assert res["scans_clean"], res["scan_findings"]


# --- CHG-TW-008: tracked holds -------------------------------------------------

def _holds_file(tmp_path: Path, holds) -> Path:
    p = tmp_path / "holds.json"
    p.write_text(json.dumps({"holds": holds}), encoding="utf-8")
    return p


def test_tracked_hold_masks_a_confirmed_row(tmp_path: Path):
    from tw import site_build
    rows = fixture_rows()
    holds = site_build.load_holds(_holds_file(tmp_path, [{"ocid": "ocds-fx-4", "award_id": "4", "basis": "test"}]))
    assert site_build.apply_holds(rows, holds) == 1
    model = site.build_rows(rows)
    d = next(d for d in model["rows"] if d["group"] == "held" and d["supplier"] == site.mask_name("Harbour Lights CC"))
    assert d["tender_reference"] == "" and d["ocds_id"] == "" and d["supplier_label"] is None
    assert d["year_cell"] == site.YEAR_UNKNOWN
    out = tmp_path / "site"
    site.build_site(rows, out)
    text = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in out.rglob("*") if p.is_file())
    assert "Harbour Lights" not in text and "4Q/2025/26" not in text


def test_tracked_hold_for_a_missing_record_stops_the_build(tmp_path: Path):
    from tw import site_build
    holds = site_build.load_holds(_holds_file(tmp_path, [{"ocid": "ocds-nope", "award_id": "1", "basis": "test"}]))
    with pytest.raises(site.UnsafeBuild):
        site_build.apply_holds(fixture_rows(), holds)


@pytest.mark.parametrize("bad", [[{"ocid": "x", "award_id": "1"}], [{"ocid": "", "award_id": "1", "basis": "b"}],
                                 [{"ocid": "x", "award_id": "1", "basis": "b"}, {"ocid": "x", "award_id": "1", "basis": "b"}]])
def test_holds_file_entries_are_checked(tmp_path: Path, bad):
    from tw import site_build
    with pytest.raises(site.UnsafeBuild):
        site_build.load_holds(_holds_file(tmp_path, bad))


def test_committed_holds_file_has_three_records_and_no_names():
    from tw import site_build
    holds = site_build.load_holds()
    assert len(holds) == 3
    allowed = {"ocid", "award_id", "basis"}
    assert all(set(h) <= allowed for h in holds)
    assert all(re.fullmatch(r"ocds-[a-z0-9]+-[0-9]+", h["ocid"]) and h["award_id"].isdigit() for h in holds)
