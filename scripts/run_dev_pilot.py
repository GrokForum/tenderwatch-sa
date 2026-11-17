#!/usr/bin/env python3
"""Run the CHG-TW-001 DEV pilot ingest and write the local run report. Does not push."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.pilot import run  # noqa: E402


def main() -> int:
    report = run()
    print(json.dumps({k: report[k] for k in (
        "awards_loaded",
        "suppliers_by_type",
        "indicator_counts",
        "age_band_counts",
        "city_register_rows",
        "city_register_source",
        "matches",
        "public_export_rows",
        "public_export_named_suppliers",
        "ocds_sha256",
        "publicfunds_pin",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
