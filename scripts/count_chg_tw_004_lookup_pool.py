#!/usr/bin/env python3
"""CHG-TW-004 lookup-pool counts (counts only; never prints names or ids).

Reproduces the numbers in docs/rfc/CHG-TW-004.md §4.2, §4.3 and §13.1 from
the local DEV outputs of CHG-TW-001 / CHG-TW-002.

Inputs (read-only)
------------------
* data/local/warehouse/awards_classified_chg_tw_002.jsonl  (the 291 classified rows)
* The pinned eTenders OCDS file named in config/chg-tw-001-dev.json
  (`etenders_ocds.paths`, SHA-256 checked against `etenders_ocds.sha256`).
  It is the same pilot input the warehouse was built from, and it is needed only
  for the "first seen as an eTenders winner" date of the young-company rule.
Nothing is written except, with --write, scripts/count_chg_tw_004_lookup_pool.out.json
(counts only, no timestamps, so repeated runs give identical output).

Pool and eligibility (§4.2)
---------------------------
* Entity = one distinct `legal_name` string among rows with
  classification_status == "confirmed_juristic".
* Excluded: any row of the entity has popia_hold; any row has legal_sub_type
  "jv" or "trust"; tw.supplier_type.is_multi_entity() is true for any row's
  legal_name or supplier_name.
* link = "Confirmed" if any row of the entity has legal_form_fact_label
  "Confirmed", else "Reported".

Score per factor (§4.3)
-----------------------
* Value: entity value = sum of value_amount over its rows whose value_note is
  null (rows with value_note "zero_placeholder", "implausible_high",
  "implausible_low", or a null value_amount, count as missing). Entities with
  value <= 0 (all missing) score 0 and are left out of the quartile set.
  Quartile set = sorted list V of the positive entity values of the
  ELIGIBLE entities (duplicates kept). Cut points use the lower nearest-rank
  rule with no interpolation: Q(p) = V[floor(p * (len(V) - 1))], so
  Q50 = V[floor(0.50*(n-1))] and Q75 = V[floor(0.75*(n-1))].
  Points: value >= Q75 -> 3; Q50 <= value < Q75 -> 2; 0 < value < Q50 -> 1;
  missing -> 0. Ties at a cut point take the higher band (>=).
* Young-company candidate: +3. first_seen = the earliest OCDS release `date`
  (first 10 characters) of any release in the pinned file whose
  awards[].suppliers[].name has the same tw.normalise.norm_name as any of the
  entity's supplier_name values. Candidate if first_seen >= 2022-06-01 AND
  (earliest award_date of the entity - first_seen) <= 365 days.
* Buyer concentration: +2 if the entity has 3 or more of the 291 rows (all at
  one buyer, City of Cape Town).
* Link: +2 if Confirmed, +1 if Reported.

Batch order (tie-break)
-----------------------
Sort by: score desc; value desc; number of rows desc; earliest award_date asc;
smallest award_id asc (internal only, never printed). Batch 1 = first 10.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tw.normalise import norm_name  # noqa: E402
from tw.supplier_type import is_multi_entity  # noqa: E402

WAREHOUSE = ROOT / "data/local/warehouse/awards_classified_chg_tw_002.jsonl"
CONFIG = ROOT / "config/chg-tw-001-dev.json"
OUT = ROOT / "scripts/count_chg_tw_004_lookup_pool.out.json"
YOUNG_FIRST_SEEN_FROM = "2022-06-01"
YOUNG_WINDOW_DAYS = 365
BATCH = 10


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ocds_path() -> tuple[Path, str]:
    cfg = json.loads(CONFIG.read_text())["etenders_ocds"]
    for p in cfg["paths"]:
        path = Path(p)
        if path.exists():
            digest = sha256(path)
            if digest != cfg["sha256"]:
                raise SystemExit(f"OCDS SHA-256 mismatch at {path}")
            return path, digest
    raise SystemExit("pinned OCDS file not found")


def first_seen_dates(path: Path) -> dict[str, str]:
    first: dict[str, str] = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            rel = json.loads(line)
            d = (rel.get("date") or "")[:10]
            if not d:
                continue
            for aw in rel.get("awards") or []:
                for s in aw.get("suppliers") or []:
                    k = norm_name(s.get("name"))
                    if k and (k not in first or d < first[k]):
                        first[k] = d
    return first


def q(values: list[float], p: float) -> float:
    return values[int(p * (len(values) - 1))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the counts-only .out.json")
    args = ap.parse_args()

    rows = [json.loads(l) for l in WAREHOUSE.open()]
    path, digest = ocds_path()
    first = first_seen_dates(path)

    confirmed = [r for r in rows if r["classification_status"] == "confirmed_juristic"]
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in confirmed:
        groups[r["legal_name"]].append(r)

    ents = []
    excl = collections.Counter()
    for legal_name, rs in groups.items():
        held = any(r["popia_hold"] for r in rs)
        subs = {r["legal_sub_type"] for r in rs}
        multi = any(is_multi_entity(r["legal_name"]) or is_multi_entity(r["supplier_name"]) for r in rs)
        if held:
            excl["popia_hold"] += 1
            continue
        if subs & {"jv", "trust"}:
            excl["jv_or_trust"] += 1
            continue
        if multi:
            excl["multi_entity"] += 1
            continue
        value = sum((r["value_amount"] or 0) for r in rs if r["value_note"] is None)
        award_min = min(r["award_date"][:10] for r in rs)
        fs = min(first.get(norm_name(r["supplier_name"]) or "", "9999-12-31") for r in rs)
        young = fs >= YOUNG_FIRST_SEEN_FROM and (
            dt.date.fromisoformat(award_min) - dt.date.fromisoformat(fs)
        ).days <= YOUNG_WINDOW_DAYS
        ents.append({
            "link": "Confirmed" if any(r["legal_form_fact_label"] == "Confirmed" for r in rs) else "Reported",
            "value": value,
            "n": len(rs),
            "young": young,
            "award_min": award_min,
            "tiebreak_id": min(str(r["award_id"]) for r in rs),
            "source": {r["legal_name_source"] for r in rs},
        })

    pos = sorted(e["value"] for e in ents if e["value"] > 0)
    q50, q75 = q(pos, 0.50), q(pos, 0.75)
    for e in ents:
        v = e["value"]
        vp = 0 if v <= 0 else 3 if v >= q75 else 2 if v >= q50 else 1
        e["value_points"] = vp
        e["score"] = vp + (3 if e["young"] else 0) + (2 if e["n"] >= 3 else 0) + (2 if e["link"] == "Confirmed" else 1)
    ents.sort(key=lambda e: (-e["score"], -e["value"], -e["n"], e["award_min"], e["tiebreak_id"]))
    batch1 = ents[:BATCH]

    reported_rows = [r for r in confirmed if r["legal_form_fact_label"] == "Reported"]
    out = {
        "inputs": {"warehouse_rows": len(rows), "ocds_sha256": digest},
        "chg_tw_002_confirmed_rows": len(confirmed),
        "confirmed_rows_by_legal_name_source": dict(sorted(collections.Counter(r["legal_name_source"] for r in confirmed).items())),
        "reported_rows": len(reported_rows),
        "reported_rows_by_legal_name_source": dict(sorted(collections.Counter(r["legal_name_source"] for r in reported_rows).items())),
        "reported_rows_held": sum(1 for r in reported_rows if r["popia_hold"]),
        "pool_distinct_legal_names": len(groups),
        "excluded": dict(sorted(excl.items())),
        "eligible": len(ents),
        "eligible_by_link": dict(sorted(collections.Counter(e["link"] for e in ents).items())),
        "eligible_by_legal_name_source": dict(sorted(collections.Counter("+".join(sorted(e["source"])) for e in ents).items())),
        "award_rows_behind_eligible_by_link": {k: sum(e["n"] for e in ents if e["link"] == k) for k in ("Confirmed", "Reported")},
        "value_known": sum(1 for e in ents if e["value"] > 0),
        "value_points": dict(sorted(collections.Counter(e["value_points"] for e in ents).items())),
        "young_candidates": sum(e["young"] for e in ents),
        "three_plus_rows": sum(e["n"] >= 3 for e in ents),
        "score_spread": {str(k): v for k, v in sorted(collections.Counter(e["score"] for e in ents).items(), reverse=True)},
        "batch1": {
            "size": len(batch1),
            "by_link": dict(sorted(collections.Counter(e["link"] for e in batch1).items())),
            "young": sum(e["young"] for e in batch1),
            "three_plus_rows": sum(e["n"] >= 3 for e in batch1),
            "value_known": sum(e["value"] > 0 for e in batch1),
            "scores": [e["score"] for e in batch1],
        },
        "batches_needed": -(-len(ents) // BATCH),
    }
    text = json.dumps(out, indent=2, sort_keys=False) + "\n"
    sys.stdout.write(text)
    if args.write:
        OUT.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
