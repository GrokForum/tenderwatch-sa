"""Reviewer A (PR #3): no committed file may carry a queued or held supplier name.

The repository is to be open-sourced. Per-name lists live only in the
git-ignored local files written by tw/classification_report.py.
"""
from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from tw.classification_report import (
    CHECK_QUEUE_PATH,
    _write_report,
    source_field_check,
    summarise,
    withheld_names,
    write_check_queue,
)
from tw.export import build_public_export
from tw.pilot import apply_classification

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "dev" / "CHG-TW-002-classification-report.md"

FIXTURE_NAMES = [
    "Northriver Widgets (Pty) Ltd",  # confirmed
    "QWERTANE ZEPHYR SYSTEMS",  # no_suffix
    "R Qwertane and Associates",  # held
    "Testburg Family Trust",  # trust_personal_name
    "Acme Widgets Ltd / Beta Tools CC",  # ambiguous_suffix
    "A. Q. Testperson t/a Testperson Crafts",  # held
]


def _fixture_awards() -> list[dict]:
    return [
        {"ocid": f"fx-{i}", "award_id": str(i), "supplier_name": n, "buyer_name": "City of Cape Town",
         "award_year": 2025, "registration_year": None, "source_locator": f"fixture:line {i}"}
        for i, n in enumerate(FIXTURE_NAMES, start=1)
    ]


def test_generator_report_has_no_supplier_names(tmp_path: Path) -> None:
    awards = _fixture_awards()
    before = Counter(a.get("supplier_type") for a in awards)
    check = source_field_check(awards, [], None)
    apply_classification(awards, [])
    public = build_public_export(awards)
    stats = summarise(awards, public, before, check, "fixture")
    report = tmp_path / "report.md"
    _write_report(report, stats)
    text = report.read_text(encoding="utf-8")
    for name in FIXTURE_NAMES:
        assert name not in text, name
        assert name.upper() not in text.upper(), name
    assert "DEV run; publishes nothing." in text
    # Per-name list goes to the local CSV instead.
    queue = tmp_path / "check_queue.csv"
    n = write_check_queue(queue, awards)
    assert n == sum(a["classification_status"] == "check_queue" for a in awards) == 5
    rows = list(csv.DictReader(queue.open(encoding="utf-8")))
    assert {r["supplier_name_ocds"] for r in rows} == set(FIXTURE_NAMES) - {"Northriver Widgets (Pty) Ltd"}
    assert all(r["reason"] and r["popia_hold"] in ("yes", "no") for r in rows)
    assert withheld_names(awards) >= set(FIXTURE_NAMES) - {"Northriver Widgets (Pty) Ltd"}


def test_committed_report_has_no_name_table() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "DEV run; publishes nothing." in text
    assert "pushed" not in text.lower()  # wording about pushing goes stale
    assert "Supplier name (OCDS)" not in text
    assert "Name shown" not in text


def _local_queue_names() -> set[str]:
    if not CHECK_QUEUE_PATH.is_file():
        pytest.skip(
            "skipped: data/local/check_queue.csv is git-ignored and absent on a fresh clone; "
            "run the DEV classification first (scripts/run_chg_tw_002_classify.py)"
        )
    names: set[str] = set()
    with CHECK_QUEUE_PATH.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            names.add(r["supplier_name_ocds"].strip())
            names.update(n.strip() for n in (r.get("city_names_linked") or "").split(";"))
    return {n for n in names if n}


def test_no_committed_file_carries_a_local_queue_name() -> None:
    names = _local_queue_names()
    try:
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    hits = []
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.suffix in {".pdf", ".gz", ".png"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").upper()
        hits.extend((f, n) for n in names if n.upper() in text)
    assert hits == [], f"{len(hits)} queued or held names found in tracked files"
