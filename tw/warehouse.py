"""Local DEV warehouse (gitignored data/local). Never writes to PublicFunds."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from tw.popia import assert_clean


def write_jsonl(path: Path, rows: Iterable[Mapping]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            n += 1
    return n


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_checked_jsonl(path: Path, rows: Iterable[Mapping], *, context: str) -> int:
    recs = list(rows)
    assert_clean(recs, context=context)
    return write_jsonl(path, recs)
