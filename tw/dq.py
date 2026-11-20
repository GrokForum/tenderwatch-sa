"""CHG-TW-009 and CHG-TW-012: the data-quality report of a run, and the data-quality gate.

CHG-TW-009: the report of a run (git-ignored, data/local/warehouse/dq-report.json).

This change gives the report its first section, ``fetch``: every collector request, ok or failed, with
failed ones classified (tw/fetch_log.py), so a TLS certificate error or an HTTP 500 is visible in the report
instead of a source quietly falling back. A run with fetch errors is reported as ``WARN``, never ``OK``.
Counts, URLs and one-line reasons only; no supplier names and no file paths.
"""
from __future__ import annotations

import contextlib
import csv
import json
import re
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


# --- CHG-TW-012: the data-quality gate --------------------------------------------------------------------

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
# Frozen copy of the published CSV schema: a change to tw/site.py's CSV_FIELDS fails the gate until this is updated
# on purpose in a reviewed change.
EXPECTED_CSV_FIELDS = ("award_date", "buyer", "tender_reference", "ocds_id", "supplier", "supplier_label", "legal_form",
                       "legal_form_label", "year_cell", "usable_value_zar", "value_note", "indicator", "right_of_reply",
                       "sources")
MANIFEST_KEYS = {"site", "status", "responsible_party", "contact", "rules", "input_sha256", "etenders_retrieved",
                 "rows_total", "group_counts", "year_counts", "files", "content_sha256"}
GROUPS = ("unmasked", "held", "personal", "pending", "withheld")
MASK_RE = re.compile(r"^(?:[A-Z0-9]\*{5}[a-z0-9]|\*{7})$")
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
DRAFT = "<strong>DRAFT.</strong>"
PAGES = ("index.html", "method/index.html", "privacy/index.html", "404.html")
ROBOTS = "User-agent: *\nDisallow: /\n"


def _check(name: str, ok: bool, detail: str = "", warn: bool = False) -> dict:
    return {"check": name, "status": PASS if ok else (WARN if warn else FAIL), "detail": detail}


def check_site(out_dir: Path, *, bounds: tuple[int, int], groups: dict | None = None) -> list[dict]:
    """Schema and masking checks on the generated files. Counts and file names only, never a name."""
    out: list[dict] = []
    missing = [p for p in PAGES + ("robots.txt", "register.csv", "manifest.json") if not (out_dir / p).is_file()]
    out.append(_check("files_present", not missing, f"missing: {missing}" if missing else "all managed files"))
    if missing:
        return out
    man = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    out.append(_check("manifest_schema", set(man) == MANIFEST_KEYS and man.get("status") == "DRAFT",
                      f"keys {sorted(set(man) ^ MANIFEST_KEYS) or 'ok'}; status {man.get('status')}"))
    total = man.get("rows_total", -1)
    gc = man.get("group_counts") or {}
    lo, hi = bounds
    out.append(_check("row_count_in_bounds", lo <= total <= hi, f"{total} rows; bounds {lo}-{hi}"))
    out.append(_check("groups_add_up", set(gc) == set(GROUPS) and sum(gc.values()) == total,
                      f"groups {gc}"))
    if groups is not None:
        out.append(_check("groups_expected", gc == groups, f"got {gc}; expected {groups}"))
    with (out_dir / "register.csv").open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        header = tuple(next(rd, ()))
        body = list(rd)
    out.append(_check("csv_schema", header == EXPECTED_CSV_FIELDS, "header matches" if header == EXPECTED_CSV_FIELDS
                      else "header differs from the frozen schema"))
    bad_len = sum(1 for r in body if len(r) != len(EXPECTED_CSV_FIELDS))
    out.append(_check("csv_row_shape", bad_len == 0, f"{bad_len} rows with the wrong number of cells"))
    out.append(_check("csv_rows_match_manifest", len(body) == total - gc.get("withheld", 0),
                      f"{len(body)} CSV rows; {total} - {gc.get('withheld', 0)} withheld expected"))
    if header == EXPECTED_CSV_FIELDS:
        ix = {k: i for i, k in enumerate(header)}
        masked = [r for r in body if len(r) == len(header) and "Masked row (POPIA)" in r[ix["indicator"]]]
        leaks = sum(1 for r in masked if not MASK_RE.match(r[ix["supplier"]]) or r[ix["ocds_id"]] or
                    r[ix["tender_reference"]] or re.search(r"[0-9]", r[ix["year_cell"]]))
        n_masked = gc.get("held", 0) + gc.get("personal", 0)
        out.append(_check("masked_rows_masked", leaks == 0 and len(masked) == n_masked,
                          f"{len(masked)} masked rows (expected {n_masked}); {leaks} with a detail next to the mask"))
        unmasked_star = sum(1 for r in body if len(r) == len(header) and MASK_RE.match(r[ix["supplier"]])
                            and "Masked row (POPIA)" not in r[ix["indicator"]])
        out.append(_check("no_stray_masks", unmasked_star == 0, f"{unmasked_star} mask-shaped names outside masked rows"))
    pages_bad = [p for p in PAGES if NOINDEX not in (t := (out_dir / p).read_text(encoding="utf-8")) or DRAFT not in t]
    out.append(_check("pages_noindex_and_draft", not pages_bad, f"failing: {pages_bad}" if pages_bad else "all pages"))
    out.append(_check("robots_disallow_all", (out_dir / "robots.txt").read_text(encoding="utf-8") == ROBOTS, "robots.txt"))
    return out


def gate(result: dict, out_dir: Path, *, bounds: tuple[int, int], groups: dict | None = None,
         fetch: dict | None = None) -> dict:
    """PASS only if the build passed every scan and every site check. Fetch errors are reported as WARN."""
    checks = [_check("build_ok", result.get("build") == "OK", str(result.get("build")))]
    scans = result.get("scans") or {}
    for k in sorted(scans):
        checks.append(_check(f"scan_{k}", scans[k] == 0, f"{scans[k]} finding(s)"))
    checks.append(_check("scans_present", {"names_withheld", "names_all_except_shown", "pii"} <= set(scans),
                         f"scans run: {sorted(scans)}"))
    checks.extend(check_site(out_dir, bounds=bounds, groups=groups))
    if fetch is not None:
        s = fetch.get("summary") or {}
        checks.append(_check("source_fetch_errors", not s.get("errors"),
                             f"{s.get('errors', 0)} error(s) by kind {s.get('errors_by_kind') or {}}; "
                             f"TLS hosts {s.get('tls_error_hosts') or []}", warn=True))
    status = FAIL if any(c["status"] == FAIL for c in checks) else (WARN if any(c["status"] == WARN for c in checks)
                                                                    else PASS)
    return {"status": status, "checks": checks, "rows_total": result.get("rows_total"),
            "group_counts": result.get("group_counts"), "content_sha256": result.get("content_sha256")}


@contextlib.contextmanager
def synthetic_inputs(fixture_dir: Path, rows_expected: int):
    """Point the site build at the committed synthetic fixtures (CI); restores the module afterwards.

    CI never sees the real holds file or DEV data: the real build stays on the box (CHG-TW-012).
    """
    from tw import public_scan, site_build
    saved = {k: getattr(site_build, k) for k in ("CLASSIFIED", "CITY", "LOOKUPS", "HOLDS", "EXPECTED_ROWS")}
    saved_extra = public_scan.EXTRA_TERMS_PATH
    try:
        site_build.CLASSIFIED = fixture_dir / "classified.jsonl"
        site_build.CITY = fixture_dir / "city_register.jsonl"  # absent: no City rows
        site_build.LOOKUPS = fixture_dir / "lookups.csv"  # absent
        site_build.HOLDS = fixture_dir / "popia_holds.synthetic.json"
        site_build.EXPECTED_ROWS = rows_expected
        public_scan.EXTRA_TERMS_PATH = fixture_dir / "public_scan_extra_terms.txt"  # absent
        yield site_build
    finally:
        for k, v in saved.items():
            setattr(site_build, k, v)
        public_scan.EXTRA_TERMS_PATH = saved_extra
