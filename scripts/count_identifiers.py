#!/usr/bin/env python3
"""Reproducible identifier counts for the TenderWatch SA source survey.

Reads the PublicFunds copy of the eTenders OCDS compiled-releases dump and
prints a JSON report (and a short text summary) of CIPC and CSD coverage.

Default input
-------------
  /workspace/publicfunds/src/full.jsonl.gz
  size: 11,676,874 bytes
  sha256: a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225
  PublicFunds fetch: 2026-10-19 09:38 SAST (Africa/Johannesburg)
  OCP Data Registry last retrieved: 2026-09-20
  Source URL: https://data.open-contracting.org/en/publication/143/download?name=full.jsonl.gz

Regexes
-------
  CIPC:  r'(?:19|20)\\d{2}/\\d{6}/\\d{2}'     (year/serial/type, no spaces)
  CSD:   r'(?i)\\bMAAA\\d{6,}\\b'            (case-insensitive, word-bounded)

Units and duplicates
--------------------
  A *release* is one JSON line (one compiled OCDS release).
  An *award-supplier row* is one element of awards[].suppliers[]
  (or one empty placeholder if an award has no suppliers list).
  Counts of rows are not deduplicated by supplier name: two awards to
  the same name are two rows. Release counts are one per ocid line.

Tenderers join
--------------
  A tenderer is CSD-bearing if its ``name`` matches the CSD regex.
  The winner name and the tenderer name are folded as follows:
    * Unicode case-fold
    * CSD tokens removed
    * punctuation / parentheses converted to spaces
    * whitespace collapsed
  A join counts when the folded winner name has at least
  MIN_JOIN_NAME_CHARS (5) characters AND is equal to, or a substring of,
  the folded tenderer name (or vice versa, same minimum length).
  At most one join is counted per award-supplier row (first match wins).
  Winners that already have a CSD token in name or id are reported
  separately and are also included in the 'any join' total.

Usage
-----
  python3 scripts/count_identifiers.py
  python3 scripts/count_identifiers.py --input PATH --json
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_INPUT = Path("/workspace/publicfunds/src/full.jsonl.gz")
EXPECTED_SHA256 = "a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225"
EXPECTED_SIZE = 11_676_874
CIPC_RE = re.compile(r"(?:19|20)\d{2}/\d{6}/\d{2}")
CSD_RE = re.compile(r"(?i)\bMAAA\d{6,}\b")
MIN_JOIN_NAME_CHARS = 5


def sha256_file(path: Path, buf: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(buf)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fold_name(raw: str | None) -> str:
    if not raw:
        return ""
    s = CSD_RE.sub(" ", raw)
    s = s.casefold()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def names_join(winner: str, tenderer: str) -> bool:
    w = fold_name(winner)
    t = fold_name(tenderer)
    if len(w) < MIN_JOIN_NAME_CHARS or len(t) < MIN_JOIN_NAME_CHARS:
        return False
    return w == t or w in t or t in w


def count(path: Path) -> dict:
    n_releases = 0
    n_award_supplier_rows = 0
    n_awards = 0
    buyers_with_awards: Counter[str] = Counter()

    releases_with_cipc_anywhere = 0
    cipc_numbers: Counter[str] = Counter()
    cipc_in_supplier_name_or_id = 0

    releases_with_csd_anywhere = 0
    award_releases_with_csd_anywhere = 0
    releases_with_csd_in_tenderers = 0
    award_releases_with_csd_in_tenderers = 0
    csd_in_supplier_name_or_id = 0
    csd_in_identifier_id = 0  # structured Identifier.id
    join_any = 0
    join_additional = 0  # join and winner did not itself carry a CSD token

    portal_id_zero = 0
    awards_with_value = 0
    awards_with_award_date = 0
    contracts = 0
    contracts_with_date = 0

    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            n_releases += 1
            rel = json.loads(line)
            awards = rel.get("awards") or []
            has_awards = bool(awards)
            buyer = ((rel.get("buyer") or {}).get("name") or "")

            if CIPC_RE.search(line):
                releases_with_cipc_anywhere += 1
                for m in CIPC_RE.findall(line):
                    cipc_numbers[m] += 1
            if CSD_RE.search(line):
                releases_with_csd_anywhere += 1
                if has_awards:
                    award_releases_with_csd_anywhere += 1

            tenderers = (rel.get("tender") or {}).get("tenderers") or []
            csd_tenderers = []
            for t in tenderers:
                tn = t.get("name") if isinstance(t, dict) else (t if isinstance(t, str) else "")
                if tn and CSD_RE.search(str(tn)):
                    csd_tenderers.append(str(tn))
            if csd_tenderers:
                releases_with_csd_in_tenderers += 1
                if has_awards:
                    award_releases_with_csd_in_tenderers += 1

            for a in awards:
                n_awards += 1
                if (a.get("value") or {}).get("amount") is not None:
                    awards_with_value += 1
                if a.get("date"):
                    awards_with_award_date += 1
                sups = a.get("suppliers") or [{}]
                if not a.get("suppliers"):
                    # still count a placeholder row so totals stay honest
                    pass
                for s in (a.get("suppliers") or [{}]):
                    n_award_supplier_rows += 1
                    if has_awards:
                        buyers_with_awards[buyer] += 1
                    sname = (s.get("name") or "") if isinstance(s, dict) else ""
                    sid = str((s.get("id") if isinstance(s, dict) else "") or "")
                    if sid.strip() == "0":
                        portal_id_zero += 1
                    ident = s.get("identifier") if isinstance(s, dict) else None
                    if isinstance(ident, dict) and ident.get("id"):
                        if CSD_RE.search(str(ident.get("id"))):
                            csd_in_identifier_id += 1
                        if CIPC_RE.search(str(ident.get("id"))):
                            pass
                    winner_has_csd = bool(CSD_RE.search(sname) or CSD_RE.search(sid))
                    if winner_has_csd:
                        csd_in_supplier_name_or_id += 1
                    if CIPC_RE.search(sname) or CIPC_RE.search(sid):
                        cipc_in_supplier_name_or_id += 1
                    joined = False
                    if sname and csd_tenderers:
                        for tn in csd_tenderers:
                            if names_join(sname, tn):
                                joined = True
                                break
                    if joined:
                        join_any += 1
                        if not winner_has_csd:
                            join_additional += 1

            for c in rel.get("contracts") or []:
                contracts += 1
                if c.get("dateSigned") or c.get("date"):
                    contracts_with_date += 1

    # buyers_with_awards was incremented per supplier row; that's correct for "awards" as used in the survey (291 Cape Town)
    cpt = buyers_with_awards.get("City of Cape Town", 0)
    n_buyers = len([b for b, n in buyers_with_awards.items() if n])

    def pct(n: int, d: int) -> float:
        return round(100.0 * n / d, 2) if d else 0.0

    report = {
        "input": {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "publicfunds_fetched_at_sast": "2026-10-19 09:38 SAST (Africa/Johannesburg)",
            "ocp_last_retrieved": "2026-09-20",
            "source_url": "https://data.open-contracting.org/en/publication/143/download?name=full.jsonl.gz",
        },
        "method": {
            "cipc_regex": CIPC_RE.pattern,
            "csd_regex": CSD_RE.pattern,
            "min_join_name_chars": MIN_JOIN_NAME_CHARS,
            "name_fold": "casefold; strip CSD tokens; non-alphanumerics to space; collapse whitespace",
            "join": (
                "award-supplier row joins a CSD-bearing tenderer.name when the folded "
                "winner name has length >= min_join_name_chars and equals or is a "
                "substring of the folded tenderer name (or vice versa). One join per row."
            ),
            "duplicates": (
                "Release counts are one per JSON line. Award-supplier rows are not "
                "deduplicated by name: two awards to the same supplier count twice."
            ),
        },
        "corpus": {
            "releases": n_releases,
            "awards": n_awards,
            "award_supplier_rows": n_award_supplier_rows,
            "buyers_with_awards": n_buyers,
            "city_of_cape_town_award_supplier_rows": cpt,
            "portal_supplier_id_zero": portal_id_zero,
            "awards_with_value": awards_with_value,
            "awards_with_award_date_field": awards_with_award_date,
            "contracts": contracts,
            "contracts_with_date": contracts_with_date,
        },
        "cipc": {
            "releases_with_cipc_anywhere": releases_with_cipc_anywhere,
            "unique_numbers": dict(cipc_numbers),
            "in_supplier_name_or_id": cipc_in_supplier_name_or_id,
        },
        "csd": {
            "structured_identifier_id": csd_in_identifier_id,
            "in_supplier_name_or_id": csd_in_supplier_name_or_id,
            "in_supplier_name_or_id_pct_of_rows": pct(csd_in_supplier_name_or_id, n_award_supplier_rows),
            "releases_with_csd_anywhere": releases_with_csd_anywhere,
            "award_releases_with_csd_anywhere": award_releases_with_csd_anywhere,
            "releases_with_csd_in_tenderers": releases_with_csd_in_tenderers,
            "award_releases_with_csd_in_tenderers": award_releases_with_csd_in_tenderers,
            "winner_joined_to_csd_tenderer": join_any,
            "winner_joined_to_csd_tenderer_additional": join_additional,
            "winner_joined_to_csd_tenderer_pct_of_rows": pct(join_any, n_award_supplier_rows),
            "winner_joined_additional_pct_of_rows": pct(join_additional, n_award_supplier_rows),
        },
    }
    return report


def text_summary(report: dict) -> str:
    c, d, k = report["corpus"], report["csd"], report["cipc"]
    lines = [
        f"Input: {report['input']['path']}",
        f"SHA-256: {report['input']['sha256']}",
        f"Releases: {c['releases']:,}  awards: {c['awards']:,}  award-supplier rows: {c['award_supplier_rows']:,}",
        f"Buyers with awards: {c['buyers_with_awards']}  City of Cape Town rows: {c['city_of_cape_town_award_supplier_rows']}",
        f"CIPC in supplier name/id: {k['in_supplier_name_or_id']} / {c['award_supplier_rows']}",
        f"CIPC unique numbers: {k['unique_numbers']}",
        f"CIPC releases anywhere: {k['releases_with_cipc_anywhere']}",
        f"CSD structured Identifier.id: {d['structured_identifier_id']}",
        f"CSD in winner name/id: {d['in_supplier_name_or_id']} / {c['award_supplier_rows']} ({d['in_supplier_name_or_id_pct_of_rows']}%)",
        f"Releases with CSD anywhere: {d['releases_with_csd_anywhere']}",
        f"Award-releases with CSD anywhere: {d['award_releases_with_csd_anywhere']}",
        f"Releases with CSD in tenderers: {d['releases_with_csd_in_tenderers']}",
        f"Award-releases with CSD in tenderers: {d['award_releases_with_csd_in_tenderers']}",
        f"Winners joined to a CSD-bearing tenderer (any): {d['winner_joined_to_csd_tenderer']} / {c['award_supplier_rows']} ({d['winner_joined_to_csd_tenderer_pct_of_rows']}%)",
        f"Winners joined, excluding those already with CSD in name/id: {d['winner_joined_to_csd_tenderer_additional']} / {c['award_supplier_rows']} ({d['winner_joined_additional_pct_of_rows']}%)",
        f"Portal supplier id '0': {c['portal_supplier_id_zero']}",
        f"Contracts: {c['contracts']} with date: {c['contracts_with_date']}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--json", action="store_true", help="print the full JSON report")
    args = ap.parse_args(argv)
    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2
    report = count(args.input)
    digest = report["input"]["sha256"]
    size = report["input"]["size_bytes"]
    if digest != EXPECTED_SHA256 or size != EXPECTED_SIZE:
        report["input"]["sha256_warning"] = (
            f"does not match the 19 Oct 2026 PublicFunds copy "
            f"(expected sha256={EXPECTED_SHA256}, size={EXPECTED_SIZE})"
        )
    print(text_summary(report), end="")
    if args.json:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
