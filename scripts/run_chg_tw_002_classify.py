#!/usr/bin/env python3
"""CHG-TW-002 DEV: classify the CHG-TW-001 award suppliers and write the DEV report. Local only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.classification_report import run  # noqa: E402
from tw.config import load_config, ocds_input_path  # noqa: E402


def main() -> int:
    cfg = load_config()
    try:
        ocds = ocds_input_path(cfg)
    except FileNotFoundError:
        ocds = None
    stats = run(ocds_path=ocds)
    print(json.dumps({k: v for k, v in stats.items()}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
