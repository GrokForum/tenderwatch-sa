"""RFC §12 / §16 Q4 age-band and indicator fixtures (synthetic CIPC only)."""
from tw.age import age_band, classify_age, young_supplier_indicator


def test_same_year_is_yes_and_same() -> None:
    ind, band = classify_age("juristic", 2026, 2026)
    assert ind == "yes"
    assert band == "same"
    # CIPC 2026/123456/07, award in 2026
    assert young_supplier_indicator("juristic", 2026, 2026) == "yes"
    assert age_band("juristic", 2026, 2026) == "same"


def test_minus_one_is_yes() -> None:
    ind, band = classify_age("juristic", 2025, 2026)
    assert ind == "yes"
    assert band == "-1"


def test_minus_two_is_no_trend_only() -> None:
    """-2 does not set the indicator (stays no, not yes)."""
    ind, band = classify_age("juristic", 2024, 2026)
    assert band == "-2"
    assert ind == "no"


def test_older_is_no() -> None:
    ind, band = classify_age("juristic", 2023, 2026)
    assert band == "older"
    assert ind == "no"


def test_unknown_without_year() -> None:
    assert classify_age("juristic", None, 2026) == ("unknown", "unknown")
    assert classify_age("juristic", 2026, None) == ("unknown", "unknown")


def test_non_juristic_stays_unknown_even_with_year() -> None:
    assert classify_age("natural_person", 2026, 2026) == ("unknown", "unknown")
    assert classify_age("unknown", 2025, 2026) == ("unknown", "unknown")


def test_future_registration_year_is_unknown() -> None:
    assert classify_age("juristic", 2027, 2026) == ("unknown", "unknown")
