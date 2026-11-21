#!/usr/bin/env python3
"""CHG-TW-011: DEV build of the register with buyers beyond the City of Cape Town (staging; publishes nothing).

    python3 scripts/build_national.py                      # stage1 (eThekwini, Mangaung) into data/local/site-build-national-stage1/
    python3 scripts/build_national.py --stage all          # every buyer with an award
    python3 scripts/build_national.py --out DIR

Reads only the pinned eTenders file and the git-ignored DEV inputs. Exit code: 0 = built and every scan clean;
1 = a scan found something; 2 = a publication rule failed, the stage is out of bounds, or an input is missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw import national  # noqa: E402
from tw.site_build import run_build  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    cfg = national.load_national_config()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stage", default=cfg["default_stage"], choices=sorted(cfg["stages"]))
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    out = a.out or ROOT / "data" / "local" / f"site-build-national-{a.stage}"
    try:
        rows = national.ingest(a.stage, cfg=cfg)
        national.write_rows(rows, a.stage)
        muni = national.municipal_buyers(rows, cfg)
        result = run_build(out, extra_rows=rows, municipal_buyers=muni)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"build": "FAIL", "stage": a.stage, "error": f"{type(e).__name__}: {e}"}, indent=2))
        return 2
    result["stage"] = a.stage
    result["national"] = national.summary(rows)
    result["municipal_buyers"] = len(muni)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scans_clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
