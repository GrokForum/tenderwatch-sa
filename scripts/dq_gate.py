#!/usr/bin/env python3
"""CHG-TW-012: data-quality gate. Builds the site into a scratch directory and checks it. Publishes nothing.

    python3 scripts/dq_gate.py --fixtures --out DIR   # CI: committed synthetic fixtures only (no real data, no secrets)
    python3 scripts/dq_gate.py                        # on the box: the real DEV build; adds the gate to dq-report.json

Exit code: 0 = PASS or WARN (fetch errors are warnings), 1 = FAIL, 2 = the build could not run.
Prints counts and check names only, never a supplier name.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw import dq  # noqa: E402

CONFIG = ROOT / "config" / "dq.json"
REPORT = ROOT / "data" / "local" / "warehouse" / "dq-report.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixtures", action="store_true", help="build the committed synthetic fixtures (CI)")
    ap.add_argument("--out", type=Path, help="scratch build directory (default: a temporary directory)")
    a = ap.parse_args(argv)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    out = a.out or Path(tempfile.mkdtemp(prefix="tw-dq-"))
    try:
        if a.fixtures:
            fx = cfg["fixtures"]
            lo, hi = fx["rows"]
            with dq.synthetic_inputs(ROOT / fx["dir"], rows_expected=hi) as sb:
                result = sb.run_build(out)
            report = dq.gate(result, out, bounds=(lo, hi), groups=fx["groups"])
            report["mode"] = "fixtures"
        else:
            from tw.site_build import run_build
            result = run_build(out)
            prev = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.is_file() else {}
            report = dq.gate(result, out, bounds=tuple(cfg["dev"]["rows"]), fetch=prev.get("fetch"))
            report["mode"] = "dev"
            prev["gate"] = report
            dq.write_report(REPORT, prev)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "ERROR", "error": f"{type(e).__name__}: {e}"}, indent=2))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == dq.FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
