"""Young-supplier indicator and company-age bands (CHG-TW-001 §6 / §16 Q4)."""
from __future__ import annotations

from typing import Literal

from tw.supplier_type import SupplierType

AgeBand = Literal["same", "-1", "-2", "older", "unknown"]
Indicator = Literal["yes", "no", "unknown"]


def age_band(
    supplier_type: SupplierType,
    registration_year: int | None,
    award_year: int | None,
) -> AgeBand:
    """Return same, -1, -2, older, or unknown.

    Recorded for every juristic supplier with a sourced year so bands can be
    trended. Non-juristic suppliers, or missing years, are unknown.
    A registration year after the award year is unknown, not a trend band.
    """
    if supplier_type != "juristic":
        return "unknown"
    if registration_year is None or award_year is None:
        return "unknown"
    if registration_year == award_year:
        return "same"
    if registration_year == award_year - 1:
        return "-1"
    if registration_year == award_year - 2:
        return "-2"
    if registration_year < award_year - 2:
        return "older"
    return "unknown"


def young_supplier_indicator(
    supplier_type: SupplierType,
    registration_year: int | None,
    award_year: int | None,
) -> Indicator:
    """yes only for bands same and -1; -2 and older are no and do not set yes."""
    band = age_band(supplier_type, registration_year, award_year)
    if band in ("same", "-1"):
        return "yes"
    if band in ("-2", "older"):
        return "no"
    return "unknown"


def classify_age(
    supplier_type: SupplierType,
    registration_year: int | None,
    award_year: int | None,
) -> tuple[Indicator, AgeBand]:
    return (
        young_supplier_indicator(supplier_type, registration_year, award_year),
        age_band(supplier_type, registration_year, award_year),
    )
