#!/usr/bin/env python3
"""CHG-TW-006: build the DRAFT register site from the DEV export and scan every generated file.

    python3 scripts/build_site.py                 # writes data/local/site-build/ (git-ignored)
    python3 scripts/build_site.py --out DIR       # any other directory (for example a site-repo worktree)

Reads only git-ignored DEV files under data/local/. Publishes nothing, pushes nothing.
Exit code: 0 = built and every scan clean; 1 = a scan found something (files are still written, for review);
2 = a publication rule failed (UnsafeBuild) or an input is missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.site_build import run_build  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "local" / "site-build")
    a = ap.parse_args(argv)
    try:
        result = run_build(a.out)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"build": "FAIL", "error": f"{type(e).__name__}: {e}"}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scans_clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
