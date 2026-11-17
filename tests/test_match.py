"""Two-detail match rule: a link on fewer than two agreeing details must fail."""
import pytest

from tw.match import agreeing_details, can_link


CAPE = {
    "supplier_name": "Zutari (Pty) Ltd.",
    "name_key": "zutari",
    "buyer_name": "City of Cape Town",
    "cipc_reg_no": None,
    "csd_no": None,
    "tender_title": "293C/2024/25",
}

OTHER_BUYER = {
    **CAPE,
    "buyer_name": "Other Municipality",
    "tender_title": "999Q/1999/00",
}

NAME_ONLY_RIGHT = {
    "supplier_name": "Zutari (Pty) Ltd.",
    "name_key": "zutari",
    "buyer_name": None,
    "jurisdiction": None,
}


def test_name_only_does_not_link() -> None:
    assert agreeing_details(CAPE, NAME_ONLY_RIGHT) == ["name_key"]
    assert can_link(CAPE, NAME_ONLY_RIGHT) is False


def test_same_name_different_buyer_does_not_link() -> None:
    assert "buyer" not in agreeing_details(CAPE, OTHER_BUYER)
    assert can_link(CAPE, OTHER_BUYER) is False


def test_same_name_same_buyer_links() -> None:
    city = {
        "vendor": "Zutari (Pty) Ltd.",
        "name_key": "zutari",
        "buyer_name": "City of Cape Town",
        "jurisdiction": "City of Cape Town",
        "tts_reference": "293C/2024/25",
    }
    details = agreeing_details(CAPE, city)
    assert "name_key" in details and "buyer" in details
    assert can_link(CAPE, city) is True


def test_same_cipc_and_name_links() -> None:
    left = {**CAPE, "cipc_reg_no": "2020/123456/07", "buyer_name": "City of Cape Town"}
    right = {
        "supplier_name": "Zutari (Pty) Ltd.",
        "name_key": "zutari",
        "cipc_reg_no": "2020/123456/07",
        "buyer_name": "Other Municipality",
    }
    details = agreeing_details(left, right)
    assert "cipc" in details and "name_key" in details
    assert can_link(left, right) is True


def test_fewer_than_two_details_must_fail(subtests=None) -> None:
    # CIPC alone is not enough
    left = {"cipc_reg_no": "2020/123456/07", "supplier_name": "Alpha Tools (Pty) Ltd"}
    right = {"cipc_reg_no": "2020/123456/07", "supplier_name": "Beta Tools (Pty) Ltd"}
    assert agreeing_details(left, right) == ["cipc"]
    assert can_link(left, right) is False


def test_shared_tender_ref_plus_name_links() -> None:
    left = {
        "supplier_name": "Printegration CC",
        "name_key": "printegration",
        "tender_title": "172S/2025/26",
        "buyer_name": None,
    }
    right = {
        "vendor": "Printegration CC",
        "name_key": "printegration",
        "tts_reference": "172S/2025/26",
        "buyer_name": None,
    }
    details = agreeing_details(left, right)
    assert "name_key" in details and "tender_ref" in details
    assert can_link(left, right) is True
