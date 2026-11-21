"""CHG-TW-006: load the DEV inputs, build the site and run the public-file scans."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from tw.classification_report import withheld_names
from tw.config import load_config
from tw.popia_names import apply_auto_holds, one_person_reason, write_review_candidates
from tw.public_scan import run_all
from tw.site import UnsafeBuild, build_rows, build_site, load_lookups, shown_names

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "local" / "warehouse"
CLASSIFIED = WAREHOUSE / "awards_classified_chg_tw_002.jsonl"
CITY = WAREHOUSE / "city_register.jsonl"
LOOKUPS = ROOT / "data" / "local" / "lookups.csv"
HOLDS = ROOT / "data" / "local" / "popia_holds.json"  # git-ignored; never committed (CHG-TW-008)
REVIEW_CANDIDATES = ROOT / "data" / "local" / "popia_review_candidates.csv"  # git-ignored (CHG-TW-010)
HOLD_KEYS = {"ocid", "award_id", "basis", "name_key"}
# Words too common to count as a name in the basis check (legal forms and trade words).
GENERIC_WORDS = {"and", "associates", "association", "company", "corporation", "electrical", "engineering",
                 "enterprises", "group", "holdings", "incorporated", "joint", "limited", "venture", "projects", "proprietary",
                 "services", "solutions", "supplies", "trading", "transport", "construction", "consulting"}
MIN_HOLDS = 3  # holds decided so far (owner, 19 Nov 2026); a shorter local file stops the build
EXPECTED_ROWS = 291


def _jsonl(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _date_only(s: str | None) -> str | None:
    return s[:10] if s and len(s) >= 10 and s[4] == "-" and s[7] == "-" else None


def load_holds(path: Path | None = None) -> list[dict]:
    """CHG-TW-008: POPIA holds from the git-ignored local file, keyed by award record (ocid and award_id).

    The file is never committed (the repository is to be open-sourced, and a record id next to a hold basis
    would let anyone look the name up in the public eTenders data). It is seeded once into each checkout,
    the nightly clone included. A missing, unreadable or short file stops the build (fail closed).
    """
    path = HOLDS if path is None else path
    if not path.is_file():
        raise UnsafeBuild("holds file missing: seed data/local/popia_holds.json (CHG-TW-008); not building")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise UnsafeBuild(f"holds file unreadable: {e.__class__.__name__}") from None
    holds = data.get("holds") if isinstance(data, dict) else None
    if not isinstance(holds, list):
        raise UnsafeBuild("holds file: 'holds' must be a list")
    seen = set()
    out = []
    for i, h in enumerate(holds):
        if not isinstance(h, dict):
            raise UnsafeBuild(f"holds file entry {i}: not an object")
        extra = set(h) - HOLD_KEYS
        if extra:
            raise UnsafeBuild(f"holds file entry {i}: unexpected keys {sorted(extra)}")
        ocid = h.get("ocid")
        award = h.get("award_id")
        basis = h.get("basis")
        if not isinstance(ocid, str) or not re.fullmatch(r"ocds-[a-z0-9]+-[0-9]+", ocid.strip(), flags=re.ASCII):
            raise UnsafeBuild(f"holds file entry {i}: ocid missing or malformed")
        award = str(award).strip() if isinstance(award, (str, int)) and not isinstance(award, bool) else ""
        if not re.fullmatch(r"[1-9][0-9]*", award, flags=re.ASCII):
            raise UnsafeBuild(f"holds file entry {i}: award_id must be a positive whole number")
        if not isinstance(basis, str) or not basis.strip():
            raise UnsafeBuild(f"holds file entry {i}: basis is required")
        name_key = h.get("name_key")
        if not isinstance(name_key, str) or not name_key.strip():
            raise UnsafeBuild(f"holds file entry {i}: name_key is required (second detail, CHG-TW-008 rev 3)")
        key = (ocid.strip(), award)
        if key in seen:
            raise UnsafeBuild(f"holds file entry {i}: duplicate award record")
        seen.add(key)
        out.append({"ocid": key[0], "award_id": key[1], "basis": basis.strip(), "name_key": name_key.strip()})
    if len(out) < MIN_HOLDS:
        raise UnsafeBuild(f"holds file has {len(out)} holds, fewer than the {MIN_HOLDS} decided; not building")
    return out


def _names_of(row: dict) -> set[str]:
    names = {row.get("supplier_name"), row.get("legal_name"), row.get("name_key")}
    names.update((row.get("city_names_linked") or "").split(";"))
    return {n.strip().lower() for n in names if isinstance(n, str) and len(n.strip()) >= 4}


def _name_words(row: dict) -> set[str]:
    """Words of four or more letters in a row's names (for example a surname), less generic trade words."""
    words: set[str] = set()
    for n in _names_of(row):
        words.update(w for w in re.findall(r"[^\W\d_]{4,}", n) if w not in GENERIC_WORDS)
    return words


def apply_holds(rows: list[dict], holds: list[dict]) -> int:
    """Set popia_hold on every listed award record.

    Stops the build when a listed record is missing from the input, when it is not a Confirmed row (a hold
    must never move a check-queue or withheld row into a shown group), when the record's name key does not
    match the hold's (second detail), or when a basis carries any supplier name from the input or any
    four-letter-plus word of the held supplier's own name (for example a surname).
    """
    index: dict[tuple[str, str], list[dict]] = {}
    every_name: set[str] = set()
    for r in rows:
        index.setdefault((str(r.get("ocid") or ""), str(r.get("award_id") or "")), []).append(r)
        every_name |= _names_of(r)
    n = 0
    for h in holds:
        basis = h["basis"].lower()
        if any(name in basis for name in every_name):
            raise UnsafeBuild("a hold basis contains a supplier name")
        hits = index.get((h["ocid"], h["award_id"]))
        if not hits:
            raise UnsafeBuild("a hold names an award record that is not in the input")
        for r in hits:
            if r.get("classification_status") != "confirmed_juristic":
                raise UnsafeBuild("a hold names a row that is not Confirmed; check-queue rows keep their own group")
            # Second detail (two-detail rule): the record id and the name key must both agree, so a hold on the
            # wrong record stops the build instead of masking one firm and leaving the intended one shown.
            if (r.get("name_key") or "").strip().lower() != h["name_key"].lower():
                raise UnsafeBuild("a hold's record id and name key do not agree")
            basis_words = set(re.findall(r"[^\W\d_]{4,}", basis))
            if basis_words & _name_words(r):
                raise UnsafeBuild("a hold basis contains a word of the held supplier's name")
            r["popia_hold"] = True
            n += 1
    return n


def pending_names_shown_elsewhere(rows: list[dict], withheld: set[str], allowed: set[str]) -> set[str]:
    """CHG-TW-011: names that are on the withheld list only because a row of *another* award is name-pending.

    The same supplier string can be a shown, Confirmed company on a City row (legal form from the City register)
    and a name-pending row for another buyer, where eTenders prints it without a suffix. The pending row still
    shows "Supplier name pending check" (no cross-buyer link is made), but its name is already public on the
    other row, so it is not a finding of the withheld-name scan. A name tied to any held, personal-looking or
    withheld row is never exempted, and the exemption is counted in the build result.
    """
    allowed_up = {a.strip().upper() for a in allowed if a and a.strip()}
    blocked: set[str] = set()
    for r in rows:
        if r.get("classification_status") == "confirmed_juristic" and not r.get("popia_hold"):
            continue
        plain_pending = (r.get("classification_status") == "check_queue" and r.get("queue_reason") == "no_suffix"
                         and not r.get("popia_hold"))
        if not plain_pending:
            names = {r.get("supplier_name"), r.get("legal_name"), *(r.get("city_names_linked") or "").split(";")}
            blocked |= {n.strip().upper() for n in names if isinstance(n, str) and n.strip()}
    return {w for w in withheld if w.strip().upper() in allowed_up and w.strip().upper() not in blocked}


def load_inputs(extra_rows: list[dict] | None = None) -> dict:
    """The City DEV export (exactly EXPECTED_ROWS rows), plus CHG-TW-011 national rows when given."""
    if not CLASSIFIED.is_file():
        raise FileNotFoundError("DEV export missing: run scripts/run_chg_tw_002_classify.py first")
    rows = _jsonl(CLASSIFIED)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows in the DEV export, got {len(rows)}")
    if extra_rows:
        city_keys = {(r.get("ocid"), r.get("award_id"), r.get("name_key")) for r in rows}
        if any((r.get("ocid"), r.get("award_id"), r.get("name_key")) in city_keys for r in extra_rows):
            raise UnsafeBuild("a national row repeats a City row; not building")
        rows = rows + [dict(r) for r in extra_rows]
    holds_applied = apply_holds(rows, load_holds())  # before withheld_names, so the scans also look for held names
    auto_holds = apply_auto_holds(rows)  # CHG-TW-010: one-person business names, also before withheld_names
    write_review_candidates(rows, REVIEW_CANDIDATES)
    city = _jsonl(CITY) if CITY.is_file() else []
    city_meta = {}
    for c in city:
        if c.get("source_url"):
            city_meta.setdefault(c["source_url"], {"retrieved": _date_only(c.get("retrieved_at"))})
    cfg = load_config()
    retrieved = _date_only(cfg["etenders_ocds"].get("publicfunds_fetched_at_sast")) or ""
    digest = hashlib.sha256(CLASSIFIED.read_bytes()).hexdigest()
    all_names = {r.get("supplier_name") for r in rows} | {c.get("supplier_name") for c in city}
    all_names = {n.strip() for n in all_names if n and n.strip()}
    return {"rows": rows, "city_meta": city_meta, "etenders_retrieved": retrieved, "input_sha256": digest,
            "withheld": withheld_names(rows), "all_names": all_names, "lookups": load_lookups(LOOKUPS),
            "holds_applied": holds_applied, "auto_holds": auto_holds}


def _replace_dir(tmp_dir: Path, out_dir: Path) -> None:
    if not out_dir.exists():
        os.replace(tmp_dir, out_dir)
        return
    backup = Path(tempfile.mkdtemp(prefix=f".{out_dir.name or 'site'}.old-", dir=out_dir.parent))
    backup.rmdir()
    os.replace(out_dir, backup)
    try:
        os.replace(tmp_dir, out_dir)
    except BaseException:
        if not out_dir.exists() and backup.exists():
            os.replace(backup, out_dir)
        raise
    shutil.rmtree(backup, ignore_errors=True)


def run_build(out_dir: Path, *, extra_rows: list[dict] | None = None,
              municipal_buyers: set[str] | None = None) -> dict:
    inp = load_inputs(extra_rows)
    if extra_rows:  # CHG-TW-011: the input hash covers the national rows too
        h = hashlib.sha256(inp["input_sha256"].encode())
        for r in extra_rows:
            h.update(json.dumps(r, sort_keys=True).encode("utf-8"))
        inp["input_sha256"] = h.hexdigest()
    target = Path(out_dir).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f".{target.name or 'site'}.tmp-", dir=target.parent))
    try:
        manifest = build_site(inp["rows"], tmp_dir, lookups=inp["lookups"], city_meta=inp["city_meta"],
                              etenders_retrieved=inp["etenders_retrieved"], input_sha256=inp["input_sha256"],
                              municipal_buyers=municipal_buyers)
        model = build_rows(inp["rows"], lookups=inp["lookups"], city_meta=inp["city_meta"],
                           etenders_retrieved=inp["etenders_retrieved"], municipal_buyers=municipal_buyers)
        allowed = shown_names(model["rows"])
        # CHG-TW-010 gate: no shown name may read as a person's name (defence in depth behind apply_auto_holds).
        if any(one_person_reason(n) == "personal_stem" for n in allowed):
            raise UnsafeBuild("a shown supplier name reads as a person's name (CHG-TW-010); not building")
        exempt = pending_names_shown_elsewhere(inp["rows"], inp["withheld"], allowed) if extra_rows else set()
        scans = run_all(tmp_dir, withheld=inp["withheld"] - exempt, all_names=inp["all_names"], allowed=allowed)
        _replace_dir(tmp_dir, target)
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
    return {
        "build": "OK",
        "rows_total": manifest["rows_total"],
        "buyers": len(model["buyers"]),
        "group_counts": manifest["group_counts"],
        "year_counts": manifest["year_counts"],
        "content_sha256": manifest["content_sha256"],
        "input_sha256": manifest["input_sha256"],
        "lookups_loaded": len(inp["lookups"]),
        "holds_applied": inp["holds_applied"],
        "auto_holds": inp["auto_holds"],
        "names_scanned": {"withheld": len(inp["withheld"]) - len(exempt), "all": len(inp["all_names"]),
                          "shown_unmasked": len(allowed), "pending_names_shown_elsewhere": len(exempt)},
        "scans": {k: len(v) for k, v in scans.items()},
        "scan_findings": scans,
        "scans_clean": not any(scans.values()),
    }
