"""CHG-TW-002: legal-form suffix confirmation, two-person check queue, POPIA hold.

Synthetic names only -- no real private people or real suppliers.
"""
from __future__ import annotations

import pytest

from tw.export import build_public_export
from tw.pilot import apply_classification
from tw.supplier_type import (
    QUEUE_REASONS,
    STATUSES,
    assert_no_silent_hide,
    classify_awards,
    classify_supplier,
    looks_like_personal_name,
    trailing_legal_form,
)

# --- suffix variants -------------------------------------------------------

SUFFIX_VARIANTS = [
    ("Northriver Widgets (Pty) Ltd", "company"),
    ("Northriver Widgets Pty Ltd", "company"),
    ("Northriver Widgets Pty. Ltd.", "company"),
    ("Northriver Widgets (PTY)LTD", "company"),
    ("NORTHRIVER WIDGETS (PTY) LTD.", "company"),
    ("Northriver   Widgets  ( Pty )  Ltd", "company"),
    ("Northriver Widgets Proprietary Limited", "company"),
    ("Northriver Widgets Ltd", "company"),
    ("Northriver Widgets Limited", "company"),
    ("Northriver Widgets (RF) (Pty) Ltd", "company"),
    ("Northriver Widgets (Pty) Ltd (RF)", "company"),
    ("Northriver Widgets Inc", "company"),
    ("Northriver Widgets Inc.", "company"),
    ("Northriver Widgets Incorporated", "company"),
    ("Harbour Lights CC", "close_corporation"),
    ("Harbour Lights cc.", "close_corporation"),
    ("Harbour Lights C.C.", "close_corporation"),
    ("Harbour Lights Close Corporation", "close_corporation"),
    ("Example Relief NPC", "npc"),
    ("Example Relief Non-Profit Company", "npc"),
    ("National Grid SOC Ltd", "soc"),
    ("National Grid SOC Limited", "soc"),
    ("National Grid (SOC) Ltd.", "soc"),
    ("Example Bursary Trust", "trust"),
    ("River Road Construction JV", "jv"),
    ("River Road Construction Joint Venture", "jv"),
    ("Epsilon Holdings RF", "other_juristic"),
]


@pytest.mark.parametrize("name,sub", SUFFIX_VARIANTS)
def test_suffix_variants(name: str, sub: str) -> None:
    form = trailing_legal_form(name)
    assert form is not None, name
    assert form.sub_type == sub


def test_suffix_before_trading_as_counts_and_after_does_not() -> None:
    form = trailing_legal_form("Northriver Widgets (Pty) Ltd t/a Widget World")
    assert form is not None and form.position == "before_trading_as"
    # A suffix only on the trading name after t/a does not make a legal entity.
    assert trailing_legal_form("A. Q. Testperson t/a Testperson Crafts CC") is None


# --- false positives -------------------------------------------------------

FALSE_POSITIVES = [
    "Mccarthy",
    "J Mcc",
    "MCCARTHY BROTHERS",
    "Fooltd Works",
    "Ltdco Services",
    "Trustee Services",
    "Trustworthy Movers",
    "Jinc Works",
    "Incline Engineering",
    "Limited Edition Printers",
    "Inc Design Studio",
    "Rf Holdings",
    "Soccer Supplies",
    "Joint Ventures Gallery Of Art",  # plural, not the trailing form
    "Harbour Lights C C",  # spaced letters without dots are not read as CC
    "Pty. Ltd.",  # suffix with no entity name in front
    "",
    None,
]


@pytest.mark.parametrize("name", FALSE_POSITIVES)
def test_no_suffix_inside_words(name) -> None:
    assert trailing_legal_form(name) is None


# --- statuses, reasons, no silent hide -------------------------------------


def test_city_name_first_then_ocds() -> None:
    c = classify_supplier("NORTHRIVER WIDGETS", ["Northriver Widgets (Pty) Ltd"])
    assert (c.status, c.method, c.sub_type) == ("confirmed_juristic", "city_register_suffix", "company")
    c = classify_supplier("Harbour Lights CC", [])
    assert (c.status, c.method, c.sub_type) == ("confirmed_juristic", "ocds_suffix", "close_corporation")


def test_conflicting_sources_are_queued() -> None:
    c = classify_supplier("Harbour Lights CC", ["Harbour Lights (Pty) Ltd"])
    assert (c.status, c.queue_reason) == ("check_queue", "name_mismatch_between_sources")
    c = classify_supplier("HARBOUR LIGHTS", ["Harbour Lights (Pty) Ltd", "Harbour Lights CC"])
    assert (c.status, c.queue_reason) == ("check_queue", "ambiguous_suffix")
    c = classify_supplier("CAPE WIDGET SYSTEMS", [], city_tender_only_names=["Other Bidder (Pty) Ltd"])
    assert (c.status, c.queue_reason) == ("check_queue", "name_mismatch_between_sources")
    c = classify_supplier("Cape Widget (Pty) Ltd Supplies Division", [])
    assert (c.status, c.queue_reason) == ("check_queue", "ambiguous_suffix")
    c = classify_supplier("CAPE WIDGET SYSTEMS", [])
    assert (c.status, c.queue_reason) == ("check_queue", "no_suffix")
    c = classify_supplier("", [])
    assert (c.status, c.queue_reason) == ("check_queue", "empty_name")


def test_trust_registry_is_master_and_indicator_stays_unknown() -> None:
    rows = [
        {
            "supplier_name": "Example Bursary Trust",
            "name_key": "example bursary trust",
            "buyer_name": "City of Cape Town",
            "registration_year": 2024,  # even if a year were present, it is not a CIPC year
            "award_year": 2024,
        }
    ]
    apply_classification(rows, [])
    r = rows[0]
    assert r["legal_sub_type"] == "trust"
    assert r["registry"] == "master_of_high_court"
    assert r["young_supplier_indicator"] == "unknown"
    assert r["age_band"] == "unknown"


def test_company_with_sourced_cipc_year_keeps_indicator() -> None:
    rows = [{"supplier_name": "Northriver Widgets (Pty) Ltd", "buyer_name": "City of Cape Town",
             "registration_year": 2024, "award_year": 2024}]
    apply_classification(rows, [])
    assert rows[0]["registry"] == "cipc"
    assert rows[0]["young_supplier_indicator"] == "yes"
    assert rows[0]["age_band"] == "same"


def _fixture_rows() -> list[dict]:
    names = [
        "Northriver Widgets (Pty) Ltd",
        "HARBOUR LIGHTS",
        "A. Q. Testperson t/a Testperson Crafts",
        "J. T. Sampleton",
        "Mr Q Fakename",
        "Mira Testburg Family Trust",
        "CAPE WIDGET SYSTEMS",
        "",
        "Example Relief NPC",
        "Zed Qwerty",
    ]
    return [
        {"ocid": f"fixture-{i}", "award_id": str(i), "supplier_name": n, "buyer_name": "City of Cape Town",
         "award_year": 2025, "registration_year": None}
        for i, n in enumerate(names)
    ]


def test_no_silent_hide_invariant() -> None:
    rows = _fixture_rows()
    city = [{"supplier_name": "Harbour Lights CC", "name_key": "harbour lights", "buyer_name": "City of Cape Town",
             "jurisdiction": "City of Cape Town", "tts_reference": "999X/2025/26"}]
    n_in = len(rows)
    classify_awards(rows, city)
    assert len(rows) == n_in
    assert all(r["classification_status"] in STATUSES for r in rows)
    assert all(r["queue_reason"] in QUEUE_REASONS for r in rows if r["classification_status"] == "check_queue")
    assert sum(r["classification_status"] == "confirmed_juristic" for r in rows) + sum(
        r["classification_status"] == "check_queue" for r in rows
    ) == n_in
    harbour = rows[1]
    assert harbour["classification_method"] == "city_register_suffix"
    public = build_public_export(rows)
    assert len(public) == n_in  # every row is present in the public export
    assert all(p["classification_status"] for p in public)


def test_invariant_catches_missing_status_and_reason() -> None:
    with pytest.raises(AssertionError):
        assert_no_silent_hide([{"classification_status": None}], 1)
    with pytest.raises(AssertionError):
        assert_no_silent_hide([{"classification_status": "check_queue", "queue_reason": None}], 1)
    with pytest.raises(AssertionError):
        assert_no_silent_hide([{"classification_status": "confirmed_juristic"}], 2)


# --- POPIA hold ------------------------------------------------------------

PERSONAL = [
    "A. Q. Testperson t/a Testperson Crafts",
    "A. Q. Testperson trading as Testperson Crafts",
    "J. T. Sampleton",
    "J.T. Sampleton",
    "A B Fakesurname",
    "M. Van Testburg",
    "Mr Q Fakename",
    "Zed Qwerty",
    "ZED QWERTY FAKENAME",
    "Mira Testburg Family Trust",
]


@pytest.mark.parametrize("name", PERSONAL)
def test_personal_looking_names_are_held(name: str) -> None:
    assert looks_like_personal_name(name)
    c = classify_supplier(name, [])
    assert c.popia_hold is True


@pytest.mark.parametrize("name", ["Northriver Widgets (Pty) Ltd", "CAPE WIDGET SYSTEMS", "Example Relief NPC",
                                  "Northriver Widgets (Pty) Ltd t/a Widget World"])
def test_business_names_are_not_held(name: str) -> None:
    assert not looks_like_personal_name(name)


def test_held_and_queued_names_never_reach_public_export() -> None:
    rows = _fixture_rows()
    classify_awards(rows, [])
    public = build_public_export(rows)
    blob = repr(public)
    for r in rows:
        if r["popia_hold"] or r["classification_status"] != "confirmed_juristic":
            if r["supplier_name"]:
                assert r["supplier_name"] not in blob, r["supplier_name"]
    shown = [p["supplier_name"] for p in public if p["supplier_name"]]
    assert "Northriver Widgets (Pty) Ltd" in shown
    assert "Example Relief NPC" in shown
    assert all(p["supplier_name"] is None for p in public if p["popia_hold"])


def test_queued_personal_name_gets_reason_and_hold() -> None:
    c = classify_supplier("J. T. Sampleton", [])
    assert (c.status, c.queue_reason, c.popia_hold, c.supplier_type) == (
        "check_queue", "looks_like_personal_name", True, "natural_person")


def test_name_only_city_link_is_reported_not_confirmed() -> None:
    c = classify_supplier("NORTHRIVER WIDGETS", ["Northriver Widgets (Pty) Ltd"])
    assert (c.legal_form_link, c.legal_form_fact_label) == ("name_and_buyer_only", "Reported")
    c = classify_supplier("NORTHRIVER WIDGETS", ["Northriver Widgets (Pty) Ltd"],
                          city_tight_names=["Northriver Widgets (Pty) Ltd"])
    assert (c.legal_form_link, c.legal_form_fact_label) == ("tender_ref", "Confirmed")
    c = classify_supplier("Northriver Widgets (Pty) Ltd", [])
    assert (c.legal_form_link, c.legal_form_fact_label) == ("same_record", "Confirmed")
