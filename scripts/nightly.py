#!/usr/bin/env python3
"""CHG-TW-007: TenderWatch nightly build, gated publish and live check.

    python3 scripts/nightly.py                 # scheduled run: build, gate, dry-run publish, live check, record
    python3 scripts/nightly.py --manual        # a by-hand re-run: recorded, but never counted for the streak
    python3 scripts/nightly.py --publish       # publishes ONLY if config/nightly.json also has "publish_enabled": true

Prints a short report: RESULT, each step, the failed live checks and where the record was written.
Exit code: 0 = night PASS, 1 = night FAIL (recorded), 2 = the run itself crashed (nothing recorded).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.nightly import NIGHTLY_DIR, run_nightly  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="TenderWatch nightly (CHG-TW-007)")
    ap.add_argument("--publish", action="store_true", help="allow publishing (also needs publish_enabled in config)")
    ap.add_argument("--manual", action="store_true", help="mark this run as a manual re-run")
    ap.add_argument("--site-dir", type=Path, default=None, help="site repository checkout (default: sibling tenderwatch-site)")
    a = ap.parse_args(argv)
    try:
        rec = run_nightly(publish_flag=a.publish, manual=a.manual, site_dir=a.site_dir)
    except Exception as e:  # noqa: BLE001
        print(f"RESULT: FAIL (the nightly run crashed: {type(e).__name__}); nothing recorded")
        return 2
    print(f"RESULT: {rec['result']}")
    for k in ("date_sast", "trigger", "branch", "repo_head", "refresh", "build", "gate", "tracked_clean", "publish",
              "check_live", "content_sha256", "log"):
        print(f"{k}: {rec.get(k, '')}")
    if rec["check_live_failed"]:
        print("check_live failed: " + rec["check_live_failed"])
    if "scans" in rec["steps"]:
        print("scans: " + json.dumps(rec["steps"]["scans"], sort_keys=True))
    print(f"record: {NIGHTLY_DIR.relative_to(ROOT)}/results.csv and the log branch")
    return 0 if rec["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
