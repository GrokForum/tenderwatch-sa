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
  Quartile set = list V of the positive entity values of the ELIGIBLE
  entities, sorted ascending (duplicates kept). Cut points use the lower nearest-rank
  rule with no interpolation: Q(p) = V[floor(p * (len(V) - 1))], so
  Q50 = V[floor(0.50*(n-1))] and Q75 = V[floor(0.75*(n-1))].
  Points: value >= Q75 -> 3; Q50 <= value < Q75 -> 2; 0 < value < Q50 -> 1;
  missing -> 0. Ties at a cut point take the higher band (>=).
* Young-company candidate: +3. first_seen = the earliest real OCDS release
  `date` (first 10 characters) of any release in the pinned file whose
  awards[].suppliers[].name has the same tw.normalise.norm_name as any of the
  entity's supplier_name values. Candidate if first_seen and the entity's
  earliest award_date are both known, first_seen >= 2022-06-01, and the
  earliest award_date is 0 to 365 days after first_seen.
  Unknown dates (None, empty, non-ISO, 9999-12-31, 1900-01-01, 1970-01-01,
  0001-01-01, or a year outside 1990-2099; see tw.lookup_pool) are never
  filled: they score 0 young points and are counted in the output.
* Buyer concentration: +2 if the entity has 3 or more of the 291 rows (all at
  one buyer, City of Cape Town).
* Link: +2 if Confirmed, +1 if Reported.

Batch order (tie-break)
-----------------------
Sort by: score desc; value desc; number of rows desc; earliest award_date asc;
smallest award_id asc (internal only, never printed). An unknown earliest
award date or award id sorts last. Batch 1 = first 10.
"""
from __future__ import annotations

import argparse
import collections
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
from tw.lookup_pool import earliest_known, parse_known_date, score_entities  # noqa: E402

WAREHOUSE = ROOT / "data/local/warehouse/awards_classified_chg_tw_002.jsonl"
CONFIG = ROOT / "config/chg-tw-001-dev.json"
OUT = ROOT / "scripts/count_chg_tw_004_lookup_pool.out.json"
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
            known = parse_known_date(rel.get("date"))
            if known is None:
                continue
            d = known.isoformat()
            for aw in rel.get("awards") or []:
                for s in aw.get("suppliers") or []:
                    k = norm_name(s.get("name"))
                    if k and (k not in first or d < first[k]):
                        first[k] = d
    return first


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
    eligible_rows: list[list[dict]] = []
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
        earliest_award = earliest_known(r.get("award_date") for r in rs)
        keys = [norm_name(r["supplier_name"]) for r in rs]
        first_seen = earliest_known(first.get(k) for k in keys if k)
        ids = [str(r["award_id"]) for r in rs if r.get("award_id") not in (None, "")]
        eligible_rows.append(rs)
        ents.append({
            "link": "Confirmed" if any(r["legal_form_fact_label"] == "Confirmed" for r in rs) else "Reported",
            "value": value,
            "n": len(rs),
            "first_seen": first_seen,
            "earliest_award": earliest_award,
            "tiebreak_id": min(ids) if ids else None,
            "source": {r["legal_name_source"] for r in rs},
        })

    ents = score_entities(ents)
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
        "unknown_dates": {
            "entities_unknown_first_seen": sum(e["first_seen"] is None for e in ents),
            "rows_unknown_first_seen": sum(e["n"] for e in ents if e["first_seen"] is None),
            "entities_unknown_earliest_award": sum(e["earliest_award"] is None for e in ents),
            "rows_unknown_award_date": sum(1 for rs in eligible_rows for r in rs if parse_known_date(r.get("award_date")) is None),
            "entities_first_seen_after_earliest_award": sum(
                1 for e in ents if e["first_seen"] and e["earliest_award"] and e["first_seen"] > e["earliest_award"]
            ),
        },
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
