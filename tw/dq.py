"""CHG-TW-009: the data-quality report of a run (git-ignored, data/local/warehouse/dq-report.json).

This change gives the report its first section, ``fetch``: every collector request, ok or failed, with
failed ones classified (tw/fetch_log.py), so a TLS certificate error or an HTTP 500 is visible in the report
instead of a source quietly falling back. A run with fetch errors is reported as ``WARN``, never ``OK``.
Counts, URLs and one-line reasons only; no supplier names and no file paths.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tw import fetch_log


def fetch_section(*logs: Any) -> dict:
    return fetch_log.merge(*logs)


def build_report(*, rfc: str, run_at: str, fetch: dict, fallbacks: list[str] | None = None) -> dict:
    errors = fetch["summary"]["errors"]
    notes = []
    for kind, n in fetch["summary"]["errors_by_kind"].items():
        notes.append(f"{n} fetch error(s) of kind {kind}")
    for f in fallbacks or []:
        notes.append(f"fallback used: {f}")
    return {
        "rfc": rfc,
        "env": "DEV",
        "run_at": run_at,
        "status": "WARN" if errors or fallbacks else "OK",
        "fetch": fetch,
        "fallbacks": list(fallbacks or []),
        "notes": notes,
    }


def write_report(path: Path, report: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
