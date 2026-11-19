#!/usr/bin/env python3
"""CHG-TW-007: count the green-night streak from the nightly results log (read-only).

    python3 scripts/nightly_streak.py            # reads data/local/nightly-log/nightly/results.csv, else data/local/nightly/results.csv
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.nightly import LOG_WORKTREE, NIGHTLY_DIR, SAST, streak  # noqa: E402


def main() -> int:
    for p in (LOG_WORKTREE / "nightly" / "results.csv", NIGHTLY_DIR / "results.csv"):
        if p.is_file():
            rows = list(csv.DictReader(p.open(encoding="utf-8")))
            break
    else:
        print(json.dumps({"streak": 0, "nights": [], "reaches_14": False, "note": "no results yet"}))
        return 0
    print(json.dumps(streak(rows, datetime.now(SAST).strftime("%Y-%m-%d")), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
