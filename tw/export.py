"""DEV public export: local files only; non-juristic names are withheld."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Mapping

from tw.popia import assert_clean
from tw.supplier_type import public_export_rows, public_supplier_name

# Fields that may appear in a DEV public export. Names only when juristic.
PUBLIC_FIELDS = [
    "ocid",
    "award_id",
    "buyer_name",
    "buyer_id",
    "tender_title",
    "tender_id",
    "procurement_method",
    "supplier_name",
    "supplier_type",
    "cipc_reg_no",
    "csd_no",
    "registration_year",
    "registration_year_label",
    "registration_year_source_url",
    "value_amount",
    "value_currency",
    "value_note",
    "award_date",
    "award_date_basis",
    "award_year",
    "young_supplier_indicator",
    "indicator_window",
    "age_band",
    "fact_label",
    "right_of_reply",
    "source_url",
    "source_locator",
    "retrieved_at",
    "matched_city_tts",
    "match_details",
]


def to_public_row(row: Mapping) -> dict:
    typ = row.get("supplier_type")
    public = {k: row.get(k) for k in PUBLIC_FIELDS}
    # public_export_rows already blanks the name; do it explicitly too.
    public["supplier_name"] = public_supplier_name(row.get("supplier_name"), typ)
    if typ != "juristic":
        public["supplier_name"] = None
        # identifiers stay only if they are organisation numbers (they should be absent)
        public["cipc_reg_no"] = None
        # CSD can identify a person-linked record; withhold for non-juristic
        public["csd_no"] = None
    return public


def build_public_export(rows: Iterable[Mapping]) -> list[dict]:
    prepared = []
    for raw in public_export_rows(rows):
        prepared.append(to_public_row(raw))
    assert_clean(prepared, context="public_export")
    for rec in prepared:
        typ = rec.get("supplier_type")
        if typ != "juristic" and rec.get("supplier_name"):
            raise AssertionError("non-juristic name leaked into public export")
    return prepared


def write_public_export(directory: Path, rows: Iterable[Mapping]) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    public = build_public_export(rows)
    jsonl = directory / "public_awards.jsonl"
    with jsonl.open("w", encoding="utf-8") as fh:
        for rec in public:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    csv_path = directory / "public_awards.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PUBLIC_FIELDS)
        writer.writeheader()
        for rec in public:
            writer.writerow({k: rec.get(k) if rec.get(k) is not None else "" for k in PUBLIC_FIELDS})
    return public
