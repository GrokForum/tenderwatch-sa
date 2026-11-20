"""CHG-TW-010: one-person business names are held automatically. Invented names only."""
from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from tw import site_build
from tw.popia_names import apply_auto_holds, one_person_reason, write_review_candidates
from tw.site import UnsafeBuild


@pytest.mark.parametrize("name, reason", [
    ("Thandeka Qwertane Transport CC", "personal_stem"),
    ("JQ Zorblax Electrical CC", "personal_stem"),            # initials written together
    ("Marietjie van der Qwerty (Pty) Ltd", "personal_stem"),  # particles not counted
    ("ZORBLAX QWERTANE AND ASSOCIATES (RF)", "personal_stem"),
    ("The Qwertane Zephyr Family Trust", "personal_stem"),
    ("Thandeka Qwertane t/a Zorblax Plumbing", "personal_stem"),  # legal part before t/a
    ("Zorblax (Pty) Ltd", "single_word_stem"),                # a surname alone or a brand: for review
    ("Cape Qwerty Engineering (Pty) Ltd", None),                # starts with a place/trade word
    ("Zorblax Civil Engineering (Pty) Ltd", None),             # one-word head
    ("Zorblax Southern Qwerty (Pty) Ltd", None),
    ("Qwerty 2000 Trading CC", None),
    ("QZ (Pty) Ltd", None),
    ("", None),
    (None, None),
])
def test_one_person_reason(name, reason):
    assert one_person_reason(name) == reason


def _rows():
    def r(i, name, status="confirmed_juristic", hold=False, legal=None):
        return {"ocid": f"ocds-fx-{i}", "award_id": str(i), "supplier_name": name, "legal_name": legal or name,
                "name_key": name.lower(), "classification_status": status, "popia_hold": hold,
                "buyer_name": "Invented Municipality"}
    return [
        r(1, "Thandeka Qwertane Transport CC"),
        r(2, "Cape Qwerty Engineering (Pty) Ltd"),
        r(3, "Zorblax (Pty) Ltd"),
        r(4, "JQ Zorblax Electrical CC", hold=True),
        r(5, "Thandeka Qwertane", status="check_queue"),
        # the source name is a brand, the linked legal name is a person's: held on either name
        r(6, "Qwerty Widgets", legal="Lindiwe Zorblax Trading CC"),
    ]


def test_apply_auto_holds_counts_and_flags():
    rows = _rows()
    counts = apply_auto_holds(rows)
    assert counts == {"personal_stem": 2, "already_held": 1, "review_single_word": 1}
    held = {r["award_id"] for r in rows if r.get("popia_hold")}
    assert held == {"1", "4", "6"}
    assert rows[0]["popia_hold_reason"] == "auto:personal_stem"
    assert "popia_hold_reason" not in rows[3]           # owner/classifier hold kept as it was
    assert rows[4].get("popia_hold") is False           # check-queue rows are not touched
    assert rows[2]["popia_review"] == "single_word_stem" and not rows[2]["popia_hold"]
    assert apply_auto_holds(rows)["personal_stem"] == 0  # running twice changes nothing


def test_review_candidates_are_local_and_private(tmp_path: Path):
    rows = _rows()
    apply_auto_holds(rows)
    p = tmp_path / "local" / "candidates.csv"
    assert write_review_candidates(rows, p) == 3
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert site_build.REVIEW_CANDIDATES.relative_to(site_build.ROOT).parts[:2] == ("data", "local")


# --- the build: auto holds applied before the scans, and a gate behind them ----------------------------


def _synthetic_inputs(tmp_path: Path, monkeypatch, rows: list[dict]) -> None:
    wh = tmp_path / "wh"
    wh.mkdir()
    cls = wh / "classified.jsonl"
    cls.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    holds = tmp_path / "holds.json"
    holds.write_text(json.dumps({"holds": [{"ocid": rows[0]["ocid"], "award_id": rows[0]["award_id"],
                                            "basis": "Owner decision: masked.", "name_key": rows[0]["name_key"]}]}),
                     encoding="utf-8")
    monkeypatch.setattr(site_build, "CLASSIFIED", cls)
    monkeypatch.setattr(site_build, "CITY", wh / "none.jsonl")
    monkeypatch.setattr(site_build, "LOOKUPS", tmp_path / "none.csv")
    monkeypatch.setattr(site_build, "HOLDS", holds)
    monkeypatch.setattr(site_build, "REVIEW_CANDIDATES", tmp_path / "cand.csv")
    monkeypatch.setattr(site_build, "MIN_HOLDS", 1)
    monkeypatch.setattr(site_build, "EXPECTED_ROWS", len(rows))


def _row(i, name, *, sub="company", key=None):
    return {"ocid": f"ocds-fx-{i}", "award_id": str(i), "buyer_name": "City of Cape Town",
            "tender_title": f"{i}Q/2025/26", "supplier_name": name, "name_key": key or name.lower(),
            "classification_status": "confirmed_juristic", "popia_hold": False, "queue_reason": None,
            "legal_sub_type": sub, "legal_form_link": "name_and_buyer_only", "legal_form_fact_label": "Reported",
            "award_date": "2025-08-01", "value_amount": 1000000.0, "value_note": None, "city_matches": []}


def _site_rows():
    return [
        _row(1, "Zorblax Holdings (Pty) Ltd", key="zorblax holdings"),
        _row(2, "Cape Qwerty Engineering (Pty) Ltd", key="cape qwerty"),
        _row(3, "Thandeka Qwertane Transport CC", sub="close_corporation", key="thandeka qwertane"),
    ]


def test_build_holds_a_person_named_firm_and_scans_for_it(tmp_path: Path, monkeypatch):
    _synthetic_inputs(tmp_path, monkeypatch, _site_rows())
    res = site_build.run_build(tmp_path / "out")
    assert res["group_counts"]["held"] == 2 and res["group_counts"]["unmasked"] == 1
    assert res["auto_holds"]["personal_stem"] == 1
    assert res["scans_clean"], res["scan_findings"]
    blob = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "out").rglob("*") if p.is_file()).upper()
    assert "QWERTANE" not in blob and "THANDEKA" not in blob


def test_build_gate_stops_when_the_detector_is_bypassed(tmp_path: Path, monkeypatch):
    _synthetic_inputs(tmp_path, monkeypatch, _site_rows())
    monkeypatch.setattr(site_build, "apply_auto_holds", lambda rows: {"personal_stem": 0})
    with pytest.raises(UnsafeBuild, match="person's name"):
        site_build.run_build(tmp_path / "out")


@pytest.mark.parametrize("name, reason", [
    ("Zorblax (Pty) Ltd t/a Thandeka Qwertane", "personal_stem"),
    ("Cape Qwerty Engineering (Pty) Ltd T/A Lindiwe Qwertane Services", "personal_stem"),
    ("Zorblax Holdings (Pty) Ltd t.a. Sipho Zorblax", "personal_stem"),
    ("Zorblax Holdings (Pty) Ltd trading as Marietjie van der Qwerty", "personal_stem"),
    ("Cape Qwerty Engineering (Pty) Ltd t/a North Coast Plumbing", None),
])
def test_one_person_reason_checks_trading_as_variants(name, reason):
    assert one_person_reason(name) == reason


def test_build_holds_trading_as_personal_name_and_legal_name_only(tmp_path: Path, monkeypatch):
    rows = [
        _row(1, "Zorblax Holdings (Pty) Ltd", key="zorblax holdings"),
        _row(2, "Cape Qwerty Engineering (Pty) Ltd t.a. Lindiwe Qwertane", key="cape qwerty"),
        # supplier_name is non-personal, linked legal_name is personal (catches dropping legal_name in _names)
        {**_row(3, "Qwerty Widgets (Pty) Ltd", key="qwerty widgets"), "legal_name": "Thandeka Qwertane Transport CC"},
    ]
    _synthetic_inputs(tmp_path, monkeypatch, rows)
    res = site_build.run_build(tmp_path / "out")
    assert res["group_counts"]["held"] == 3 and res["group_counts"]["unmasked"] == 0
    assert res["auto_holds"]["personal_stem"] == 2
    assert res["scans_clean"], res["scan_findings"]
    blob = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "out").rglob("*") if p.is_file()).upper()
    assert "LINDIWE" not in blob and "THANDEKA" not in blob and "QWERTANE" not in blob


def test_gate_failure_leaves_previous_output_untouched(tmp_path: Path, monkeypatch):
    rows = _site_rows()
    _synthetic_inputs(tmp_path, monkeypatch, rows)
    out = tmp_path / "out"
    site_build.run_build(out)
    prev_index = (out / "index.html").read_bytes()
    sentinel = out / "sentinel.txt"
    sentinel.write_text("keep-me", encoding="utf-8")

    monkeypatch.setattr(site_build, "apply_auto_holds", lambda r: {"personal_stem": 0})
    with pytest.raises(UnsafeBuild, match="person's name"):
        site_build.run_build(out)

    assert (out / "index.html").read_bytes() == prev_index
    assert sentinel.read_text(encoding="utf-8") == "keep-me"
    assert not list(tmp_path.glob(f".{out.name}.tmp-*"))
