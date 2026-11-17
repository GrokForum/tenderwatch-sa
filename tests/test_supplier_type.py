"""Fixture tests for supplier_type. Synthetic names only — no real private people."""
from __future__ import annotations

import pytest

from tw.supplier_type import (
    classify_supplier_type,
    public_export_rows,
    public_supplier_name,
    young_supplier_indicator,
)

# Clearly fictional organisation names and obviously invented person-style strings.
JURISTIC_CASES = [
    "Northriver Widgets (Pty) Ltd",
    "Northriver Widgets Pty Ltd",
    "Harbour Lights CC",
    "Example Relief NPC",
    "National Grid SOC Ltd",
    "Alpha Beta Trust",
    "River Road Construction JV",
    "Beta Tools Limited",
    "Gamma Widget Inc",
    "Delta Services Proprietary Limited",
    "Epsilon Holdings (RF) Pty Ltd",
    "Zed Analytics Incorporated",
    "Omega Waste Close Corporation",
    "Pipeline Joint Venture",
]

NATURAL_CASES = [
    "Alex Q. Testperson t/a Testperson Crafts",
    "Sam P. Exampleton trading as Exampleton Prints",
    "J. T. Sampleton",
    "A B Fakesurname",
    "M. Van Testburg",
]

UNKNOWN_CASES = [
    "ORANGE RIVER LOGISTICS",
    "MAHUMA GROUP",
    "CAPE AUTOMATION SYSTEMS",
    "",
    None,
    "F L O SPECIALIZED PRODUCT SOLUTIONS",
]


@pytest.mark.parametrize("name", JURISTIC_CASES)
def test_juristic_suffixes(name: str) -> None:
    assert classify_supplier_type(name) == "juristic"


@pytest.mark.parametrize("name", NATURAL_CASES)
def test_natural_person_patterns(name: str) -> None:
    assert classify_supplier_type(name) == "natural_person"


@pytest.mark.parametrize("name", UNKNOWN_CASES)
def test_unknown_without_suffix(name: str | None) -> None:
    assert classify_supplier_type(name) == "unknown"


def test_trading_as_wins_over_juristic_suffix() -> None:
    # The string still names a person trading as an entity.
    assert classify_supplier_type("Alex Q. Testperson t/a Testperson Crafts CC") == "natural_person"


def test_indicator_only_for_juristic() -> None:
    assert young_supplier_indicator("juristic", 2026, 2026) == "yes"
    assert young_supplier_indicator("juristic", 2025, 2026) == "yes"
    assert young_supplier_indicator("juristic", 2024, 2026) == "no"
    assert young_supplier_indicator("juristic", None, 2026) == "unknown"
    # Even if a year is present, non-juristic types stay unknown.
    assert young_supplier_indicator("natural_person", 2026, 2026) == "unknown"
    assert young_supplier_indicator("unknown", 2026, 2026) == "unknown"


def test_public_export_omits_non_juristic_names() -> None:
    rows = [
        {"ocid": "fixture-1", "supplier_name": "Northriver Widgets (Pty) Ltd"},
        {"ocid": "fixture-2", "supplier_name": "Alex Q. Testperson t/a Testperson Crafts"},
        {"ocid": "fixture-3", "supplier_name": "ORANGE RIVER LOGISTICS"},
        {"ocid": "fixture-4", "supplier_name": "J. T. Sampleton"},
    ]
    exported = public_export_rows(rows)
    names = [r["supplier_name"] for r in exported]
    assert names[0] == "Northriver Widgets (Pty) Ltd"
    assert names[1] is None
    assert names[2] is None
    assert names[3] is None
    assert all(
        r["supplier_name"] is None or r["supplier_type"] == "juristic" for r in exported
    )
    # The original non-juristic strings must not appear anywhere in the export.
    blob = repr(exported)
    assert "Testperson" not in blob
    assert "ORANGE RIVER LOGISTICS" not in blob
    assert "Sampleton" not in blob


def test_public_supplier_name_withholds_unknown() -> None:
    assert public_supplier_name("Beta Tools Limited") == "Beta Tools Limited"
    assert public_supplier_name("MAHUMA GROUP") is None
    assert public_supplier_name("A B Fakesurname") is None
