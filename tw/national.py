"""CHG-TW-011: buyers beyond the City of Cape Town, from the pinned eTenders OCDS file (OCP publication 143).

DEV staging only. Rows keep the City pipeline's shape and rules: the CHG-TW-002 classifier (legal form from the
name; no second source, so no City link), POPIA stripping and checks, CHG-TW-010 one-person-name holds at build
time. eTenders carries no CIPC registration numbers, so a registration year (and age band) is never derived for
these rows: ``Year: Unknown``, until a second free public source gives a matching detail (later change).

Stages (config/national.json): ``stage1`` = eThekwini and Mangaung, the two metros the source pack named;
``all`` = every buyer with an award. The City of Cape Town is always excluded here: its rows come from the
CHG-TW-002 DEV export.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from tw.config import ROOT, load_config, ocds_input_path
from tw.ocds import iter_awards
from tw.pilot import apply_classification
from tw.popia import EMAIL_RE, SA_ID_RE, assert_clean
from tw.supplier_type import assert_no_silent_hide

CONFIG = ROOT / "config" / "national.json"
WAREHOUSE = ROOT / "data" / "local" / "warehouse"


class StageOutOfBounds(ValueError):
    pass


def load_national_config(path: Path = CONFIG) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("env") != "DEV":
        raise RuntimeError("CHG-TW-011 config must name env DEV")
    return cfg


def _canon(name: str | None) -> str:
    return " ".join((name or "").split()).casefold()


def buyer_filter_for(stage: str, cfg: dict):
    if stage not in cfg["stages"]:
        raise ValueError(f"unknown stage {stage!r}")
    excluded = {_canon(b) for b in cfg.get("excluded_buyers") or []}
    wanted = cfg["stages"][stage]
    if wanted == "*":
        return lambda b: bool(b) and _canon(b) not in excluded
    names = {_canon(b) for b in wanted} - excluded
    return lambda b: _canon(b) in names


def municipal_buyers(rows: list[dict], cfg: dict) -> set[str]:
    """Buyers whose financial year is the municipal one (1 July to 30 June), by name pattern."""
    pat = re.compile(cfg["municipal_buyer_pattern"])
    names = {r.get("buyer_name") or "" for r in rows} | set(cfg.get("excluded_buyers") or [])
    return {b for b in names if b and pat.search(b)}


REDACTABLE = ("tender_title", "tender_id")


def redact_id_like(rows: list[dict]) -> int:
    """Blank a tender title or id that looks like an SA ID number or an email (POPIA, fail safe).

    A 13-digit tender reference can be a legitimate number, but it cannot be told apart from an ID number, so it
    is not shown. A supplier name with such a value is not redacted here: assert_clean then stops the stage.
    """
    n = 0
    for r in rows:
        for k in REDACTABLE:
            v = r.get(k)
            if isinstance(v, str) and (SA_ID_RE.search(v) or EMAIL_RE.search(v)):
                r[k] = None
                r.setdefault("popia_redacted", []).append(k)
                n += 1
    return n


def ingest(stage: str, *, cfg: dict | None = None, ocds_path: Path | None = None,
           expected_sha256: str | None = None) -> list[dict]:
    """Classified national rows for one stage. Raises if the row count is outside the stage's bounds."""
    cfg = cfg or load_national_config()
    dev = load_config()
    path = ocds_path or ocds_input_path(dev)
    kw = {"expected_sha256": expected_sha256} if expected_sha256 else {}
    rows = list(iter_awards(path, retrieved_at=dev["etenders_ocds"]["publicfunds_fetched_at_sast"],
                            buyer_filter=buyer_filter_for(stage, cfg), **kw))
    redact_id_like(rows)
    assert_clean(rows, context=f"national.{stage}")
    apply_classification(rows, [])
    assert_no_silent_hide(rows, len(rows))
    for r in rows:
        r["source_stage"] = stage
        r["city_names_linked"] = None
    lo, hi = cfg["row_bounds"][stage]
    if not lo <= len(rows) <= hi:
        raise StageOutOfBounds(f"stage {stage}: {len(rows)} rows, outside the bounds {lo}-{hi}")
    keys = Counter((r.get("ocid"), r.get("award_id"), r.get("name_key")) for r in rows)
    if any(n > 1 for n in keys.values()):
        raise StageOutOfBounds(f"stage {stage}: duplicate award-supplier rows in the source")
    return rows


def write_rows(rows: list[dict], stage: str, directory: Path = WAREHOUSE) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / f"national_{stage}.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    return p


def summary(rows: list[dict]) -> dict:
    """Counts only (no names)."""
    return {
        "rows": len(rows),
        "buyers": len({r.get("buyer_name") for r in rows}),
        "status": dict(Counter(r.get("classification_status") for r in rows)),
        "queue_reason": dict(Counter(r.get("queue_reason") for r in rows if r.get("queue_reason"))),
        "supplier_type": dict(Counter(r.get("supplier_type") for r in rows)),
        "fields_redacted_popia": sum(len(r.get("popia_redacted") or []) for r in rows),
        "registration_year_known": sum(1 for r in rows if r.get("registration_year") is not None),
        "award_date_range": [min((r.get("award_date") or "9999") for r in rows) if rows else None,
                             max((r.get("award_date") or "") for r in rows) if rows else None],
    }
