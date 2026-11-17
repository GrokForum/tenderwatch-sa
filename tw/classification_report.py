"""CHG-TW-002 DEV classification run over the CHG-TW-001 warehouse rows.

Reads the local (git-ignored) DEV warehouse written by the CHG-TW-001 pilot,
classifies every award supplier exactly once, writes a local classified
warehouse and a local public export, and renders the private-repo DEV report.
No network access. No PublicFunds writes.
"""
from __future__ import annotations

import gzip
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tw.config import EXPECTED_OCDS_SHA256, PUBLICFUNDS_PIN, ROOT
from tw.export import build_public_export, write_public_export
from tw.pilot import apply_classification
from tw.supplier_type import QUEUE_REASONS, SUB_TYPES, assert_no_silent_hide, has_inner_legal_token, trailing_legal_form
from tw.warehouse import write_checked_jsonl

SAST = timezone(timedelta(hours=2), name="SAST")
HOLD_TEXT = "[POPIA hold: name withheld until checked]"
REPORT_PATH = ROOT / "docs" / "dev" / "CHG-TW-002-classification-report.md"
EXPECTED_ROWS = 291


def _now() -> str:
    return datetime.now(SAST).strftime("%Y-%m-%d %H:%M SAST (Africa/Johannesburg)")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def row_id(award: dict, index: int) -> str:
    return f"R{index:03d} {award.get('ocid')}/award {award.get('award_id')}"


def source_field_check(awards: list[dict], city_rows: list[dict], ocds_path: Path | None) -> dict:
    """Counts only: where the supplier name lives and whether suffixes appear there."""
    out: dict = {}
    out["ocds_award_rows"] = len(awards)
    out["ocds_supplier_name_trailing_suffix"] = sum(1 for a in awards if trailing_legal_form(a.get("supplier_name")))
    out["ocds_supplier_name_any_legal_word"] = sum(1 for a in awards if has_inner_legal_token(a.get("supplier_name")))
    out["ocds_supplier_name_all_caps"] = sum(1 for a in awards if (a.get("supplier_name") or "") == (a.get("supplier_name") or "").upper())
    out["ocds_award_years"] = dict(sorted(Counter(a.get("award_year") for a in awards).items()))
    city_named = [c for c in city_rows if c.get("supplier_name")]
    out["city_rows"] = len(city_rows)
    out["city_rows_named"] = len(city_named)
    out["city_trailing_suffix"] = sum(1 for c in city_named if trailing_legal_form(c["supplier_name"]))
    out["city_any_legal_word"] = sum(1 for c in city_named if has_inner_legal_token(c["supplier_name"]))
    out["city_periods"] = sorted({c.get("period") for c in city_rows if c.get("period")})
    out["ocds_raw_checked"] = False
    if ocds_path and ocds_path.is_file():
        locs = {int(str(a["source_locator"]).rsplit("line ", 1)[1]) for a in awards}
        parties = same = legal_suffix = 0
        with gzip.open(ocds_path, "rt", encoding="utf-8") as fh:
            for i, line in enumerate(fh, start=1):
                if i not in locs:
                    continue
                rel = json.loads(line)
                for p in rel.get("parties") or []:
                    if "supplier" not in (p.get("roles") or []):
                        continue
                    parties += 1
                    legal = ((p.get("identifier") or {}).get("legalName") or "").strip()
                    if legal.casefold() == (p.get("name") or "").strip().casefold():
                        same += 1
                    if trailing_legal_form(legal):
                        legal_suffix += 1
        out.update(
            ocds_raw_checked=True,
            ocds_supplier_parties=parties,
            ocds_legalname_equals_name=same,
            ocds_legalname_trailing_suffix=legal_suffix,
        )
    return out


def run(report_path: Path | None = None, ocds_path: Path | None = None) -> dict:
    started = _now()
    wh = ROOT / "data" / "local" / "warehouse"
    awards = _load_jsonl(wh / "awards.jsonl")
    city_rows = _load_jsonl(wh / "city_register.jsonl")
    if len(awards) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} award-supplier rows from the CHG-TW-001 DEV run, got {len(awards)}")
    digests = {a.get("sha256") for a in awards}
    if digests != {EXPECTED_OCDS_SHA256}:
        raise ValueError(f"warehouse rows are not from the pinned OCDS file: {digests}")
    before = Counter(a.get("supplier_type") for a in awards)
    check = source_field_check(awards, city_rows, ocds_path)

    apply_classification(awards, city_rows)
    assert_no_silent_hide(awards, EXPECTED_ROWS)
    n = write_checked_jsonl(wh / "awards_classified_chg_tw_002.jsonl", awards, context="warehouse.awards_classified")
    public = write_public_export(ROOT / "data" / "local" / "export" / "chg-tw-002", awards)
    assert len(public) == EXPECTED_ROWS == n

    # The public export must not carry any queued or held name.
    withheld = {a["supplier_name"] for a in awards if a["popia_hold"] or a["classification_status"] != "confirmed_juristic"}
    shown = {a["supplier_name"] for a in awards} - withheld
    blob = json.dumps(public, ensure_ascii=False)
    leaks = [w for w in withheld if w and w not in shown and w in blob]
    if leaks:
        raise AssertionError(f"{len(leaks)} withheld names found in the public export")

    stats = {
        "rfc": "CHG-TW-002",
        "env": "DEV",
        "run_at": started,
        "publicfunds_pin": PUBLICFUNDS_PIN,
        "ocds_sha256": EXPECTED_OCDS_SHA256,
        "rows": len(awards),
        "before_supplier_type": dict(before),
        "after_supplier_type": dict(Counter(a["supplier_type"] for a in awards)),
        "status": dict(Counter(a["classification_status"] for a in awards)),
        "method": dict(Counter(a["classification_method"] for a in awards if a["classification_method"])),
        "sub_type": dict(Counter(a["legal_sub_type"] for a in awards if a["legal_sub_type"])),
        "queue_reason": dict(Counter(a["queue_reason"] for a in awards if a["queue_reason"])),
        "legal_form_link": dict(Counter(a["legal_form_link"] for a in awards if a["legal_form_link"])),
        "legal_form_fact_label": dict(Counter(a["legal_form_fact_label"] for a in awards if a["legal_form_fact_label"])),
        "popia_hold": sum(1 for a in awards if a["popia_hold"]),
        "popia_hold_by_status": dict(Counter(a["classification_status"] for a in awards if a["popia_hold"])),
        "confirmed_with_city_spelling_note": sum(1 for a in awards if a["classification_status"] == "confirmed_juristic" and a.get("queue_notes")),
        "confirmed_with_sourced_year": sum(1 for a in awards if a["classification_status"] == "confirmed_juristic" and a.get("registration_year")),
        "indicator": dict(Counter(a["young_supplier_indicator"] for a in awards)),
        "age_band": dict(Counter(a["age_band"] for a in awards)),
        "public_rows": len(public),
        "public_named": sum(1 for r in public if r.get("supplier_name")),
        "distinct_names_queued": len({a["supplier_name"] for a in awards if a["classification_status"] == "check_queue"}),
        "source_field_check": check,
    }
    (wh / "chg-tw-002-summary.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    _write_report(report_path or REPORT_PATH, stats, awards)
    return stats


def _table(counter: dict, keys) -> str:
    return "\n".join(f"| `{k}` | {counter.get(k, 0)} |" for k in keys)


def _write_report(path: Path, s: dict, awards: list[dict]) -> None:
    c = s["source_field_check"]
    queued = [(i, a) for i, a in enumerate(awards, start=1) if a["classification_status"] == "check_queue"]
    confirmed = [(i, a) for i, a in enumerate(awards, start=1) if a["classification_status"] == "confirmed_juristic"]
    held_confirmed = sum(1 for _, a in confirmed if a["popia_hold"])
    total_confirmed = s["status"].get("confirmed_juristic", 0)
    total_queued = s["status"].get("check_queue", 0)

    def name_cell(a: dict) -> str:
        return HOLD_TEXT if a["popia_hold"] else (a.get("supplier_name") or "")

    q_lines = []
    for reason in QUEUE_REASONS:
        rows = [(i, a) for i, a in queued if a["queue_reason"] == reason]
        if not rows:
            continue
        q_lines.append(f"\n### `{reason}` ({len(rows)})\n\n| Row id | Award year | Supplier name (OCDS) | POPIA hold | Notes |\n|---|---|---|---|---|")
        for i, a in rows:
            q_lines.append(
                f"| {row_id(a, i)} | {a.get('award_year')} | {name_cell(a)} | {'yes' if a['popia_hold'] else 'no'} | {a.get('queue_notes') or ''} |"
            )
    c_lines = ["| Row id | Method | Link | Label | Sub-type | Suffix | Name shown | Notes |", "|---|---|---|---|---|---|---|---|"]
    for i, a in confirmed:
        shown = HOLD_TEXT if a["popia_hold"] else (a.get("legal_name") or "")
        c_lines.append(
            f"| {row_id(a, i)} | `{a['classification_method']}` | `{a['legal_form_link']}` | {a['legal_form_fact_label']} | `{a['legal_sub_type']}` | {a['legal_suffix']} | {shown} | {a.get('queue_notes') or ''} |"
        )

    raw = (
        f"Checked in the raw pinned file: {c['ocds_supplier_parties']} supplier `parties[]` entries; "
        f"`parties[].identifier.legalName` equals `parties[].name` (ignoring case) on {c['ocds_legalname_equals_name']} of them, "
        f"and carries a trailing legal suffix on {c['ocds_legalname_trailing_suffix']}."
        if c.get("ocds_raw_checked")
        else "Raw OCDS file not available on this run; counts below use the warehouse copy of `awards[].suppliers[].name`."
    )
    body = f"""# CHG-TW-002 DEV classification report

Environment: **DEV** (local box only). Private repository only. Nothing was pushed, sent or published.
Run: {s['run_at']}. Input: the {s['rows']} City of Cape Town award-supplier rows of the CHG-TW-001 DEV run
(OCDS SHA-256 `{s['ocds_sha256']}`, PublicFunds pin `{s['publicfunds_pin']}`, read-only) and the
{c['city_rows']} City register rows from the same run. No new network fetch.

## 1. Source-field check (done before building)

| Source | Field that carries the supplier name | Rows | Trailing legal suffix | Any legal-form word |
|---|---|---|---|---|
| eTenders OCDS (OCP mirror) | `awards[].suppliers[].name` (same string as `parties[].name` / `parties[].identifier.legalName`) | {c['ocds_award_rows']} | **{c['ocds_supplier_name_trailing_suffix']}** | {c['ocds_supplier_name_any_legal_word']} |
| City of Cape Town monthly award register (PDF) | `Vendor` column, parsed to `supplier_name` | {c['city_rows_named']} named of {c['city_rows']} | **{c['city_trailing_suffix']}** | {c['city_any_legal_word']} |

{raw}

Plain reading:

* **The OCDS supplier name almost never carries a legal suffix** ({c['ocds_supplier_name_trailing_suffix']} of {c['ocds_award_rows']}); {c['ocds_supplier_name_all_caps']} of the names are in capitals, and the raw `legalName` field is the same string, so it adds nothing. The OCDS name alone cannot confirm a legal form.
* **The City register `Vendor` column usually does carry a suffix** ({c['city_trailing_suffix']} of {c['city_rows_named']} rows end the legal name, i.e. the part before any `t/a`, with a suffix; the other rows with a legal word have it inside a multi-vendor line or on a wrapped PDF line).
* **But the two sources cover different periods.** The City register PDFs cover {', '.join(c['city_periods'])}; the OCDS Cape Town awards are from award years {c['ocds_award_years']}. A City name can be used only where the two-detail rule links it to the award *with the normalised name agreeing*, which is why method 1 reaches only a minority of suppliers.
* Result: method 1 cannot reach high coverage on this data. The two-person queue is large. This is stated, not fudged.

## 2. Counts

| Status | Rows |
|---|---|
| `confirmed_juristic` | {total_confirmed} |
| `check_queue` | {total_queued} |
| **Total classified** | **{total_confirmed + total_queued}** of {s['rows']} input rows (no row unclassified, none hidden) |

Before (CHG-TW-001 rule): {s['before_supplier_type']}. After: {s['after_supplier_type']}.

### By method

| Method | Rows |
|---|---|
{_table(s['method'], sorted(s['method']))}

`city_register_suffix`: the City register name linked on name + buyer carries the suffix. `ocds_suffix`: the OCDS name itself carries it. `*_before_trading_as`: the suffix is on the legal name before `t/a`.
How the legal form was linked to the award (CHG-TW-001 §19: only a shared tender reference is a tight link):
{_table(s['legal_form_link'], ('same_record', 'tender_ref', 'name_and_buyer_only'))}

Legal-form fact label: {s['legal_form_fact_label']}. A suffix taken from a City name linked on name + buyer only is labelled
**Reported**, not Confirmed: the City printed that suffix, but the link to the older OCDS award is a name-only match within one buyer.

Confirmed rows where some City spellings of the same name lacked a suffix (noted, not queued): {s['confirmed_with_city_spelling_note']}.

### By sub-type

| Sub-type | Rows |
|---|---|
{_table(s['sub_type'], SUB_TYPES)}

### Queue by reason

| Reason | Rows |
|---|---|
{_table(s['queue_reason'], QUEUE_REASONS)}

Distinct supplier names in the queue: {s['distinct_names_queued']}.

### POPIA hold

`popia_hold` = true on **{s['popia_hold']}** rows ({s['popia_hold_by_status']}). The rule is deliberately over-inclusive:
`t/a` without a legal suffix on the legal name, initials plus surname, a title, a trust with a family or person-style stem,
or a bare two-to-four-word name with no business word, digit or legal word. Many held names will turn out to be businesses;
the two-person check releases them. Held names are not written to this report or to any public file.
Of the confirmed rows, {held_confirmed} are held because one of their source names looks personal; their status stays `confirmed_juristic` but the name is withheld until checked.

### Age indicator

Confirmed rows with a sourced CIPC registration year: **{s['confirmed_with_sourced_year']}**. Confirming a legal form does not supply a year,
so the indicator stays Unknown. Indicator counts: {s['indicator']}; age bands: {s['age_band']}.
A trust is registered with the Master of the High Court, not CIPC: its CIPC indicator stays Unknown unless a sourced year exists.

### Local public export (DEV, git-ignored)

{s['public_rows']} rows written (= input, no silent hide); {s['public_named']} carry a name (confirmed and not held).
Queued rows keep their row, status and reason, with the name withheld until the two-person check.

## 3. Remaining list for the two-person check ({total_queued} rows)

Row ids are internal (`R<n>` is the row position in the DEV warehouse; the OCID and award id locate the source record).
The two checkers read held names from the local DEV warehouse by row id, never from this file.
{chr(10).join(q_lines)}

## 4. Confirmed rows ({total_confirmed})

{chr(10).join(c_lines)}

Fact labels: award rows **Confirmed** as published by the source. Legal form **Confirmed** where the suffix is in the OCDS record itself or in a
City row that shares the tender reference; **Reported** where the City row is linked on name + buyer only. No link uses a registry number.
Registration year: **Unknown** unless sourced. `Right of reply: pending` on every row.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
