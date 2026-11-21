"""CHG-TW-006: build the static DRAFT register site from the DEV export.

Input: the CHG-TW-002 classified DEV rows (``data/local/warehouse/awards_classified_chg_tw_002.jsonl``,
git-ignored) and an optional owner-lookup file (``data/local/lookups.csv``, git-ignored; absent today).
Output: a directory of static files for the public site repo. Publishes nothing.

Publication rules: CHG-TW-004 revision 7 and 8 (§13.2, §13.3, §13.5, §13.6, §13.7, §13.8).
Every row is placed in exactly one group; all rows are accounted for:

* ``unmasked``: confirmed juristic, no POPIA hold. Name shown with its fact label.
* ``held``: confirmed juristic with a POPIA hold. Fixed 7-character mask; legal form as a category.
* ``personal``: personal-looking name (POPIA hold). Fixed mask; legal form Unknown; year not shown.
* ``pending``: no legal-form suffix in any source. "Supplier name pending check"; legal form Unknown.
* ``withheld``: name mismatch between sources. No row is shown; counted only.

The build is deterministic (no clock in any file), so the same inputs give the same bytes.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from tw.supplier_type import _SUFFIX_TABLE, normalise_tokens, strip_outer_brackets

SITE_NAME = "TenderWatch SA"
SITE_URL = "https://tenderwatch.grokforum.site"
ROLE_EMAIL = "privacy@grokforum.site"
RESPONSIBLE_PARTY = "GrokForum"
INFO_REGULATOR_URL = "https://inforegulator.org.za/"
RIGHT_OF_REPLY = "Right of reply: pending"

LABEL_CONFIRMED = "Confirmed"
LABEL_REPORTED = "Reported, Unconfirmed"  # owner rule, CHG-TW-004 §13.7: one label, the comma is part of it
LABEL_UNKNOWN = "Unknown"

YEAR_PLACEHOLDER = "Year: ****, Reported, Unconfirmed"
YEAR_UNKNOWN = "Year: Unknown"
YEAR_MASKED_ROW = "Year: not shown (masked row)"
NAME_PENDING = "Supplier name pending check"
MASK_EMPTY = "*******"

GROUPS = ("unmasked", "held", "personal", "pending", "withheld")

ETENDERS_DATASET_URL = "https://data.open-contracting.org/en/publication/143"
ETENDERS_POLICY_URL = "https://data.etenders.gov.za/Home/LearnMore"
CITY_INDEX_URL = (
    "https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/"
    "tenders-rfqs-and-supply/tenders-awarded/"
)
CITY_ACK = "This information resides at and is the property of the City of Cape Town."
CITY_BUYER = "City of Cape Town"  # the one buyer with a second source (its award registers); CHG-TW-011

LEGAL_FORM_TEXT = {
    "company": "Company",
    "close_corporation": "Close corporation",
    "jv": "Joint venture",
    "other_juristic": "Other juristic person",
    "soc": "State-owned company",
    "npc": "Non-profit company",
    "trust": "Trust",
}
# Registry that issues a registration year; only these can ever show a year.
CIPC_SUB_TYPES = {"company", "close_corporation", "soc", "npc", "other_juristic"}

VALUE_NOTE_TEXT = {
    "zero_placeholder": "No usable value (the source gives 0, a placeholder)",
    "implausible_high": "No usable value (the source value is implausibly high)",
    "implausible_low": "No usable value (the source value is implausibly low)",
}

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
# frame-ancestors is ignored in a meta CSP; it is kept for when headers become possible and is harmless.

MANAGED_FILES = (
    "index.html",
    "method/index.html",
    "privacy/index.html",
    "404.html",
    "robots.txt",
    "register.csv",
    "manifest.json",
)


class UnsafeBuild(AssertionError):
    """A publication rule would be broken; nothing is written."""


# --- masking ---------------------------------------------------------------


def mask_name(name: str | None) -> str:
    """Fixed 7-character mask (CHG-TW-004 §13.2): first and last letter or digit of the name stem.

    The stem is the name with outer brackets and any trailing legal-form suffix removed, ASCII-folded.
    First character upper case, last lower case, exactly five asterisks between. Fewer than two letters
    or digits: seven asterisks.
    """
    s = strip_outer_brackets(name)
    s = re.sub(r"(?i)(?<![a-z])c\.\s*c\.?\s*$", " CC", s)  # dotted "C.C.", as in trailing_legal_form
    toks = normalise_tokens(s)
    stripped = True
    while stripped:  # "(RF) (Pty) Ltd", "(Pty) Ltd (RF)" and similar stacks
        stripped = False
        if len(toks) > 1 and toks[-1] == "rf":
            toks, stripped = toks[:-1], True
            continue
        for seq, _suffix, _sub in _SUFFIX_TABLE:
            n = len(seq)
            if len(toks) > n and tuple(toks[-n:]) == seq:
                toks, stripped = toks[:-n], True
                break
    chars = "".join(toks)
    if len(chars) < 2:
        return MASK_EMPTY
    return chars[0].upper() + "*****" + chars[-1].lower()


# --- grouping and cells ----------------------------------------------------


def row_group(row: Mapping) -> str:
    status = row.get("classification_status")
    hold = bool(row.get("popia_hold"))
    reason = row.get("queue_reason")
    if status == "confirmed_juristic":
        return "held" if hold else "unmasked"
    if status == "check_queue":
        if reason in ("looks_like_personal_name", "trust_personal_name") or hold:
            return "personal"
        if reason == "no_suffix":
            return "pending"
        # Name mismatch, ambiguous suffix or anything else unresolved: withheld (fail safe).
        return "withheld"
    raise UnsafeBuild(f"row without a known classification status: {status!r}")


def label_text(raw: str | None) -> str | None:
    """Fact label as published. The internal value 'Reported' is always written 'Reported, Unconfirmed'."""
    if raw is None:
        return None
    if raw in ("Reported", LABEL_REPORTED):
        return LABEL_REPORTED
    if raw in (LABEL_CONFIRMED, LABEL_UNKNOWN):
        return raw
    raise UnsafeBuild(f"unknown fact label {raw!r}")


def load_lookups(path: Path | None) -> dict[str, dict]:
    """Owner CIPC lookup outcomes (git-ignored local file, CHG-TW-004 §4.5). Absent file: no lookups.

    Columns: name_key, result (found / not_found / several_matches), registration_year,
    registration_year_label (Confirmed or Reported, Unconfirmed; decided under the two-detail rule, §5).
    """
    if path is None or not path.is_file():
        return {}
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for i, r in enumerate(csv.DictReader(fh), start=2):
            key = (r.get("name_key") or "").strip()
            result = (r.get("result") or "").strip()
            if not key or result not in ("found", "not_found", "several_matches"):
                raise UnsafeBuild(f"lookups file line {i}: missing name_key or unknown result")
            rec = {"result": result, "year": None, "label": None}
            if result == "found":
                y = (r.get("registration_year") or "").strip()
                lab = (r.get("registration_year_label") or "").strip()
                if not re.fullmatch(r"(19|20)[0-9]{2}", y, flags=re.ASCII):
                    raise UnsafeBuild(f"lookups file line {i}: registration_year is not a 4-digit year")
                rec["year"] = int(y)
                rec["label"] = label_text(lab)
                if rec["label"] not in (LABEL_CONFIRMED, LABEL_REPORTED):
                    raise UnsafeBuild(f"lookups file line {i}: label must be Confirmed or Reported, Unconfirmed")
            out[key] = rec
    return out


def year_cell(row: Mapping, group: str, lookup: Mapping | None) -> str | None:
    """Exact year-cell text (CHG-TW-004 §13.8). None for a withheld row (no cell)."""
    if group == "withheld":
        return None
    if group == "personal":
        return YEAR_MASKED_ROW
    if group == "pending":
        return YEAR_UNKNOWN
    if row.get("legal_sub_type") not in CIPC_SUB_TYPES:
        return YEAR_UNKNOWN  # a JV or trust has no CIPC registration year
    if not lookup or lookup.get("result") != "found":
        return YEAR_UNKNOWN
    if lookup["label"] == LABEL_REPORTED:
        return YEAR_PLACEHOLDER
    if lookup["label"] == LABEL_CONFIRMED:
        if group == "held":
            # §13.8: a held masked row never shows a year digit; which text it shows for a Confirmed
            # year is an open owner question, so the build stops rather than guess.
            raise UnsafeBuild("a held masked row has a Confirmed year; owner decision needed before building")
        return f"Year: {lookup['year']}, {LABEL_CONFIRMED}"
    raise UnsafeBuild("lookup without a usable label")


def usable_value(row: Mapping) -> tuple[float | None, str | None]:
    note = row.get("value_note")
    amt = row.get("value_amount")
    if note:
        return None, VALUE_NOTE_TEXT.get(note, "No usable value")
    if amt is None:
        return None, "No value in the source"
    return float(amt), None


def fmt_rand(amount: float) -> str:
    whole = int(round(amount))
    s = f"{whole:,}".replace(",", "\u00a0")
    return f"R\u00a0{s}"


def financial_year(d: str | None) -> str | None:
    """Municipal financial year (1 July to 30 June), e.g. '2024/25'."""
    if not d or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", d, flags=re.ASCII):
        return None
    y, m = int(d[:4]), int(d[5:7])
    start = y if m >= 7 else y - 1
    return f"{start}/{str(start + 1)[2:]}"


def _city_sources(row: Mapping, city_meta: Mapping[str, Mapping]) -> list[dict]:
    seen = set()
    out = []
    for m in row.get("city_matches") or []:
        url = m.get("source_url")
        if not url or url in seen:
            continue
        seen.add(url)
        meta = city_meta.get(url, {})
        out.append({
            "label": f"City of Cape Town award register {m.get('period') or ''} (PDF)".replace("  ", " "),
            "url": url,
            "reference": m.get("tts_reference"),
            "retrieved": meta.get("retrieved"),
        })
    return out


def build_rows(rows: Sequence[Mapping], *, lookups: Mapping[str, Mapping] | None = None,
               city_meta: Mapping[str, Mapping] | None = None, etenders_retrieved: str = "",
               municipal_buyers: set[str] | None = None) -> dict:
    """Display rows plus counts. Raises UnsafeBuild if any rule fails.

    CHG-TW-011: I1 is counted per buyer, and only for buyers in ``municipal_buyers`` (the municipal financial
    year runs 1 July to 30 June; other buyers keep other years). ``None`` means every buyer (City-only builds).
    Owner lookups and the City register citation apply only to City of Cape Town rows.
    """
    lookups = lookups or {}
    city_meta = city_meta or {}
    groups = [row_group(r) for r in rows]
    shown: list[dict] = []
    counts = Counter(groups)
    year_counts: Counter = Counter()

    # I1 (CHG-TW-004 §13.4): repeat awards per supplier per financial year, unmasked rows only.
    def i1_applies(r: Mapping) -> bool:
        return municipal_buyers is None or (r.get("buyer_name") or "") in municipal_buyers

    fy_awards: dict[tuple[str, str, str], list[Mapping]] = defaultdict(list)
    for r, g in zip(rows, groups):
        if g == "unmasked" and i1_applies(r):
            fy = financial_year(r.get("award_date"))
            if fy:
                fy_awards[(r.get("buyer_name") or "", r.get("name_key") or "", fy)].append(r)

    etenders_src = {
        "label": "eTenders OCDS (publication 143)",
        "url": ETENDERS_DATASET_URL,
        "retrieved": etenders_retrieved,
    }
    for r, g in zip(rows, groups):
        is_city = (r.get("buyer_name") or "") == CITY_BUYER
        lk = lookups.get(r.get("name_key") or "") if g in ("unmasked", "held") and is_city else None
        cell = year_cell(r, g, lk)
        if g == "withheld":
            year_counts["Row withheld (no cell)"] += 1
            continue
        year_counts[cell if not cell.startswith("Year: ") or cell in (YEAR_PLACEHOLDER, YEAR_UNKNOWN, YEAR_MASKED_ROW)
                    else "Year: YYYY, Confirmed"] += 1
        value, note = usable_value(r)
        d: dict = {
            "group": g,
            "award_date": r.get("award_date") or "",
            "buyer": r.get("buyer_name") or "",
            "year_cell": cell,
            "usable_value_zar": value,
            "value_note": note,
        }
        if g == "unmasked":
            d.update({
                "tender_reference": (r.get("tender_title") or "").strip(),
                "ocds_id": r.get("ocid") or "",
                "supplier": (r.get("supplier_name") or "").strip(),
                "supplier_label": label_text({"same_record": "Confirmed", "tender_ref": "Confirmed",
                                              "name_and_buyer_only": "Reported"}[r.get("legal_form_link") or "same_record"]),
                "legal_form": LEGAL_FORM_TEXT.get(r.get("legal_sub_type") or "", "Unknown"),
                "legal_form_label": label_text(r.get("legal_form_fact_label")),
                "right_of_reply": RIGHT_OF_REPLY,
                "sources": [etenders_src] + _city_sources(r, city_meta),
                "indicator": None,
                "indicator_highlight": False,
            })
            fy = financial_year(r.get("award_date")) if i1_applies(r) else None
            peers = fy_awards.get((r.get("buyer_name") or "", r.get("name_key") or "", fy), []) if fy else []
            if len(peers) >= 2:
                vals = [usable_value(p)[0] for p in peers]
                total = sum(v for v in vals if v is not None)
                n_usable = sum(1 for v in vals if v is not None)
                if n_usable == 0:
                    vtext = "no usable value in the source"
                else:
                    vtext = fmt_rand(total) + " usable value"
                    if n_usable < len(peers):
                        vtext += f"; {len(peers) - n_usable} of the {len(peers)} have no usable value"
                d["indicator"] = (
                    f"Indicator I1: this supplier received {len(peers)} awards ({vtext}) from "
                    f"{d['buyer']} in financial year {fy}. Source: eTenders OCDS. "
                    "This is a count from the public record, not a finding."
                )
                d["indicator_highlight"] = len(peers) >= 3
        elif g in ("held", "personal"):
            d.update({
                # §13.2: no tender reference, OCDS id, release link, registration detail or indicator next to a
                # mask. The eTenders tender title on these rows is the tender reference itself, so it is not shown.
                "tender_reference": "",
                "ocds_id": "",
                "supplier": mask_name(r.get("supplier_name")),
                "supplier_label": None,
                "legal_form": (LEGAL_FORM_TEXT.get(r.get("legal_sub_type") or "", "Unknown")
                               if g == "held" else "Unknown"),
                "legal_form_label": None if g == "held" else LABEL_UNKNOWN,
                "right_of_reply": "",
                "sources": [
                    {"label": "eTenders OCDS dataset (register-level citation)", "url": ETENDERS_DATASET_URL,
                     "retrieved": etenders_retrieved},
                ] + ([{"label": "City of Cape Town tenders awarded registers (register-level citation)",
                       "url": CITY_INDEX_URL, "retrieved": None}] if g == "held" and is_city else []),
                "indicator": None,
                "indicator_highlight": False,
                "popia_note": "Masked row (POPIA): the name is shown as its first and last character only.",
            })
        else:  # pending
            d.update({
                "tender_reference": (r.get("tender_title") or "").strip(),
                "ocds_id": r.get("ocid") or "",
                "supplier": NAME_PENDING,
                "supplier_label": None,
                "legal_form": "Unknown",
                "legal_form_label": LABEL_UNKNOWN,
                "legal_form_reason": "No legal-form suffix in any source",
                "right_of_reply": "",
                "sources": [etenders_src],
                "indicator": None,
                "indicator_highlight": False,
            })
        shown.append(d)
    total = len(rows)
    if sum(counts.values()) != total or len(shown) + counts["withheld"] != total:
        raise UnsafeBuild("rows not all accounted for")
    if sum(year_counts.values()) != total:
        raise UnsafeBuild("year-cell counts do not add up to the row count")
    _check_rules(shown)
    shown.sort(key=lambda d: (d["award_date"], d["ocds_id"], d["supplier"]), reverse=True)
    buyers = sorted({(r.get("buyer_name") or "") for r in rows})
    return {"rows": shown, "group_counts": {g: counts.get(g, 0) for g in GROUPS}, "total": total,
            "year_counts": dict(year_counts), "buyers": buyers}


def _national(model: Mapping) -> bool:
    """True when the build holds any buyer other than the City (CHG-TW-011); City-only pages are unchanged."""
    return any(b != CITY_BUYER for b in model.get("buyers") or [CITY_BUYER])


_DIGIT = re.compile(r"[0-9]")


def _check_rules(shown: Sequence[Mapping]) -> None:
    for d in shown:
        g = d["group"]
        if d["year_cell"] == YEAR_PLACEHOLDER and _DIGIT.search(d["year_cell"]):
            raise UnsafeBuild("digit in a placeholder cell")
        if g in ("held", "personal"):
            if _DIGIT.search(d["year_cell"]):
                raise UnsafeBuild("year digit on a masked row")
            if len(d["supplier"]) != 7 or d["supplier"][1:6] != "*****":
                raise UnsafeBuild("mask is not the fixed 7-character form")
            if d["tender_reference"] or d["ocds_id"] or d["indicator"]:
                raise UnsafeBuild("identifying detail next to a mask")
        if g == "personal" and d["year_cell"] != YEAR_MASKED_ROW:
            raise UnsafeBuild("personal-looking row without the fixed year text")
        if g == "pending" and d["supplier"] != NAME_PENDING:
            raise UnsafeBuild("pending row shows a name")
        if g == "unmasked" and d["supplier_label"] not in (LABEL_CONFIRMED, LABEL_REPORTED):
            raise UnsafeBuild("shown name without its fact label")


# --- HTML ------------------------------------------------------------------

E = html.escape

STYLE = """
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5;color:#14202b;background:#f6f8fa}
a{color:#0b4f8a}a:focus-visible{outline:3px solid #1b5fd1;outline-offset:2px}
.skip{position:absolute;left:-999px;top:0;background:#fff;padding:.5rem 1rem;z-index:10}.skip:focus{left:.5rem}
.draft{background:#4a1d0a;color:#fff;font-size:.95rem}.draft p{max-width:1100px;margin:0 auto;padding:.5rem 1rem}.draft a{color:#fff;text-decoration:underline}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 1rem}
main{background:#fff;padding:1rem 1rem 2rem}
h1{font-size:1.6rem;line-height:1.25}h2{font-size:1.15rem;margin-top:1.6rem}
nav a{margin-right:1rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{border-bottom:1px solid #d0d7de;padding:.35rem .4rem;text-align:left;vertical-align:top}
th{background:#eef2f6;position:sticky;top:0}
td.num{text-align:right;white-space:nowrap}
td:first-child{white-space:nowrap}td:nth-child(8){min-width:14rem}
.wrap{overflow-x:auto}
.note{color:#4a5560;font-size:.82rem}
.hl{background:#fff4d6}
footer{color:#4a5560;font-size:.88rem;padding:1rem}
@media (prefers-color-scheme:dark){body{color:#e6edf3;background:#0f161d}main{background:#16202a}a{color:#7cc0ff}th{background:#1f2a35}th,td{border-color:#2d3a46}.note,footer{color:#9aa7b4}.hl{background:#3a3212}}
""".strip()

BANNER = (
    '<div class="draft" role="note"><p><strong>DRAFT.</strong> This site is a draft. It is built only from the '
    "public record, shown as found, with each source cited. Indicators are patterns in the public record, not "
    'findings about anyone. <a href="/privacy/">Privacy and contact</a></p></div>'
)

NAV = ('<nav aria-label="Site"><a href="/">Register</a><a href="/method/">Sources and method</a>'
       '<a href="/privacy/">Privacy and contact</a></nav>')


def page(title: str, body: str) -> str:
    return (
        "<!doctype html>\n<html lang=\"en-ZA\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex, nofollow\">\n"
        f"<meta http-equiv=\"Content-Security-Policy\" content=\"{CSP}\">\n"
        "<meta name=\"referrer\" content=\"no-referrer\">\n"
        "<link rel=\"icon\" href=\"data:,\">\n"
        f"<title>DRAFT · {E(title)} · {SITE_NAME}</title>\n"
        f"<style>\n{STYLE}\n</style>\n</head>\n<body>\n"
        "<a class=\"skip\" href=\"#main\">Skip to content</a>\n"
        f"{BANNER}\n<header><p><strong>{SITE_NAME}</strong> (DRAFT)</p>{NAV}</header>\n"
        f"<main id=\"main\">\n{body}\n</main>\n"
        f"<footer><p>{SITE_NAME} · DRAFT · Responsible party: {RESPONSIBLE_PARTY} · "
        "<a href=\"/method/\">Sources and method</a> · <a href=\"/privacy/\">Privacy and contact</a></p></footer>\n"
        "</body>\n</html>\n"
    )


def _sources_html(sources: Sequence[Mapping]) -> str:
    parts = []
    for s in sources:
        bits = f'<a href="{E(s["url"])}">{E(s["label"])}</a>'
        if s.get("reference"):
            bits += f" (ref. {E(s['reference'])})"
        if s.get("retrieved"):
            bits += f", retrieved {E(s['retrieved'])}"
        parts.append(bits)
    return "<br>".join(parts)


def _label(text: str | None) -> str:
    return f' <span class="note">({E(text)})</span>' if text else ""


def _coverage(model: Mapping, etenders_retrieved: str) -> str:
    if not _national(model):
        return (f"This draft covers one buyer, the City of Cape Town, from National Treasury's eTenders data "
                f"(retrieved {E(etenders_retrieved)}), cross-referenced with the City's published award registers.")
    n = len(model.get("buyers") or [])
    return (f"This draft covers {n} buyers from National Treasury's eTenders data (retrieved {E(etenders_retrieved)}). "
            "City of Cape Town rows are cross-referenced with the City's published award registers; rows from the "
            "other buyers come from eTenders alone, and no second source has been checked for them yet.")


def render_index(model: Mapping, *, etenders_retrieved: str) -> str:
    gc = model["group_counts"]
    yc = model["year_counts"]
    total = model["total"]
    shown_n = len(model["rows"])
    rows_html = []
    for d in model["rows"]:
        supplier = E(d["supplier"]) + _label(d.get("supplier_label"))
        legal = E(d["legal_form"]) + _label(d.get("legal_form_label"))
        if d.get("legal_form_reason"):
            legal += f'<br><span class="note">{E(d["legal_form_reason"])}</span>'
        notes = []
        if d.get("indicator"):
            notes.append(E(d["indicator"]))
        if d.get("right_of_reply"):
            notes.append(E(d["right_of_reply"]))
        if d.get("popia_note"):
            notes.append(E(d["popia_note"]))
        ref = E(d["tender_reference"]) if d["tender_reference"] else '<span class="note">not shown (masked row)</span>' \
            if d["group"] in ("held", "personal") else ""
        if d["ocds_id"]:
            ref += f'<br><span class="note">OCDS id {E(d["ocds_id"])}</span>'
        value = fmt_rand(d["usable_value_zar"]) if d["usable_value_zar"] is not None else \
            f'<span class="note">{E(d["value_note"] or "")}</span>'
        cls = ' class="hl"' if d.get("indicator_highlight") else ""
        vcls = ' class="num"' if d["usable_value_zar"] is not None else ""
        rows_html.append(
            f"<tr{cls}><td>{E(d['award_date'])}</td><td>{E(d['buyer'])}</td><td>{ref}</td><td>{supplier}</td>"
            f"<td>{legal}</td><td>{E(d['year_cell'])}</td><td{vcls}>{value}</td>"
            f"<td>{_sources_html(d['sources'])}</td><td>{'<br>'.join(notes)}</td></tr>"
        )
    year_rows = "".join(
        f"<tr><td>{E(k)}</td><td class=\"num\">{yc.get(k, 0)}</td></tr>"
        for k in ("Year: YYYY, Confirmed", YEAR_PLACEHOLDER, YEAR_UNKNOWN, YEAR_MASKED_ROW, "Row withheld (no cell)")
    )
    body = f"""
<h1>Register of tender awards (DRAFT)</h1>
<p>A neutral, sourced register of South African government tender awards and how established each winning supplier is. {_coverage(model, etenders_retrieved)} Facts are shown as found, each with its source and a fact label: <strong>Confirmed</strong>; <strong>Reported, Unconfirmed</strong>; or <strong>Unknown</strong>. See <a href="/method/">Sources and method</a>.</p>
<h2>Every row accounted for</h2>
<div class="wrap"><table>
<caption class="note">{total} award rows in the source extract</caption>
<thead><tr><th scope="col">Group</th><th scope="col">Rows</th></tr></thead>
<tbody>
<tr><td>Supplier named, legal form from a source</td><td class="num">{gc['unmasked']}</td></tr>
<tr><td>Company name masked (POPIA hold)</td><td class="num">{gc['held']}</td></tr>
<tr><td>Personal-looking name masked (POPIA)</td><td class="num">{gc['personal']}</td></tr>
<tr><td>{NAME_PENDING} (no legal-form suffix in any source)</td><td class="num">{gc['pending']}</td></tr>
<tr><td>Row withheld: the sources disagree on the name, pending a two-person check</td><td class="num">{gc['withheld']}</td></tr>
<tr><th scope="row">Total</th><th class="num">{total}</th></tr>
</tbody></table></div>
<h2>Registration year cells</h2>
<p class="note">Only Confirmed registration years are published. A year that is Reported, Unconfirmed is tracked but not shown (<code>{E(YEAR_PLACEHOLDER)}</code>). Masked personal-looking rows never show a year.</p>
<div class="wrap"><table><thead><tr><th scope="col">Year cell</th><th scope="col">Rows</th></tr></thead><tbody>{year_rows}</tbody></table></div>
<h2>Awards ({shown_n} rows shown)</h2>
<p class="note">Newest first. Values are as published in the source; a value the source marks as 0 or that is implausible is not used. A highlighted row is a supplier with 3 or more awards from one buyer in one financial year (indicator I1). Download: <a href="/register.csv">register.csv</a> (the same rows and cells as this table).</p>
<div class="wrap"><table>
<thead><tr><th scope="col">Award date</th><th scope="col">Buyer</th><th scope="col">Tender reference</th><th scope="col">Supplier</th><th scope="col">Legal form</th><th scope="col">Registration year</th><th scope="col">Usable value</th><th scope="col">Sources</th><th scope="col">Notes</th></tr></thead>
<tbody>
{chr(10).join(rows_html)}
</tbody></table></div>
""".strip()
    return page("Register", body)


def render_method(model: Mapping, *, etenders_retrieved: str) -> str:
    body = f"""
<h1>Sources and method (DRAFT)</h1>
<p>{SITE_NAME} is a DRAFT built only from the public record and presented as found. Award data comes from the National Treasury eTenders portal and from the City of Cape Town's published award registers, each cited to its document. A company's legal form comes from its name, which the Companies Act requires to end with an expression such as "(Pty) Ltd" (s11(3)(c)), and every company must print its name and registration number on its notices and publications (s32(4)). The Companies and Intellectual Property Commission must make the information in its registers efficiently and effectively available to the public (Companies Act s187(4)(c); Companies Regulations, 2011, reg 174(1)(b)). Indicators are patterns in the public record, not findings about anyone. Private individuals are not identified.</p>
<h2>Sources</h2>
<ul>
<li><a href="{ETENDERS_DATASET_URL}">National Treasury eTenders OCDS data, via the Open Contracting data registry (publication 143)</a>, retrieved {E(etenders_retrieved)}. Attribution: National Treasury, Office of the Chief Procurement Officer. Publication policy: <a href="{ETENDERS_POLICY_URL}">eTenders "Learn more"</a> (the portal also states Creative Commons BY 4.0).</li>
<li><a href="{CITY_INDEX_URL}">City of Cape Town, tenders awarded registers</a> (monthly PDFs, each linked on the rows it supports). {CITY_ACK}</li>
</ul>
<h2>Fact labels</h2>
<ul>
<li><strong>Confirmed</strong>: from the award record itself, or from a City register row that shares the tender reference.</li>
<li><strong>Reported, Unconfirmed</strong>: stated by a source, or linked by name and buyer only, and not confirmed by a second independent detail.</li>
<li><strong>Unknown</strong>: no source gives it.</li>
</ul>
<h2>What each row shows</h2>
<ul>
<li>A supplier is named only when a source gives its legal form (for example "(Pty) Ltd" or "CC"). The name carries its fact label.</li>
<li>A name with no legal-form suffix in any source shows "{NAME_PENDING}" until a two-person check finds it is not a personal name.</li>
<li>A personal-looking name, and a company name held for privacy, is masked to a fixed 7 characters: its first character, five asterisks and its last character. A masked row shows only the buyer, award date and usable value, cites the source at register level, and shows no tender reference, identifier, registration detail or indicator.</li>
<li>A row where the sources disagree on the name is withheld and counted until it is checked.</li>
<li>Registration year: <code>Year: YYYY, Confirmed</code> when a registration year is confirmed by two independent details; <code>{E(YEAR_PLACEHOLDER)}</code> when a year is tracked but not confirmed (no digit is shown); <code>{E(YEAR_UNKNOWN)}</code> otherwise; <code>{E(YEAR_MASKED_ROW)}</code> on masked personal-looking rows.</li>
</ul>
<h2>Indicators</h2>
<p>An indicator is a pattern in the public record that may merit a closer look. It is not a finding that anyone did anything wrong. Every indicator links to its sources, and each supplier named has a right of reply ("{RIGHT_OF_REPLY}").</p>
<ul>
<li><strong>I1, repeat awards to one supplier</strong>: the number of awards and the total usable value to the same supplier from one buyer in one municipal financial year (1 July to 30 June). Shown for 2 or more awards; highlighted at 3 or more. Shown only on rows where the supplier is named.</li>
<li>Indicators I2 to I7 are defined but not yet shown: each needs a source this draft does not hold.</li>
</ul>
{_national_method(model)}""".strip()
    return page("Sources and method", body)


def _national_method(model: Mapping) -> str:
    if not _national(model):
        return ""
    return ("<h2>Buyers beyond the City of Cape Town</h2>\n<ul>\n"
            "<li>Rows from buyers other than the City of Cape Town come from the eTenders data alone. eTenders carries "
            "no company registration numbers, so their registration year is <code>Year: Unknown</code> until a second "
            "free public source gives a detail that matches.</li>\n"
            "<li>Indicator I1 is counted per buyer, and only for municipal buyers, whose financial year runs from "
            "1 July to 30 June.</li>\n"
            "<li>Names are masked by the same rules, including a firm whose name reads as a person's name.</li>\n</ul>")


def render_privacy() -> str:
    m = f'<a href="mailto:{ROLE_EMAIL}">{ROLE_EMAIL}</a>'
    body = f"""
<h1>Privacy and contact</h1>
<section id="what"><h2>1. What this site is</h2>
<p>{SITE_NAME} is a draft register of South African government tender awards. It shows indicators, not findings. It is built only from official public records.</p></section>
<section id="data"><h2>2. What data it shows</h2>
<ul>
<li>Tender award records as National Treasury's eTenders portal and the City of Cape Town publish them, each with a link to its source (see <a href="/method/">Sources and method</a>).</li>
<li>A supplier is named only when a source shows it is a company or another juristic person.</li>
<li>A personal-looking name is masked: its first character, five asterisks, then its last character. Some company names are masked the same way.</li>
<li>The site never shows ID numbers, home addresses, personal phone numbers or personal e-mail addresses.</li>
</ul></section>
<section id="purpose"><h2>3. Purpose and basis</h2>
<p>The purpose is public accountability: to help people follow how public money is awarded.</p>
<p>The site processes only information that public bodies have already published in official public records, and shows it as found, with its source.</p>
<p>The lawful basis is the processing of information in public records that the data subject or a public body made public, for this accountability purpose <strong>[legal wording unverified]</strong>.</p></section>
<section id="not"><h2>4. What the site does not do</h2>
<p>The site uses no cookies, no analytics, no trackers and no scripts. It has no forms and no accounts.</p></section>
<section id="corrections"><h2>5. Corrections, removal and right of reply</h2>
<p>To ask for a correction or a removal, or to reply about a record, send an e-mail to {m}.</p>
<p>Identify the record by its award date and its tender reference or, where no reference is shown (masked rows), its buyer and usable value. Do not send ID numbers, phone numbers or addresses.</p></section>
<section id="retention"><h2>6. How long data stays</h2>
<p>Each build replaces the published files. Earlier versions stay in the site's version history.</p></section>
<section id="responsible"><h2>7. Who is responsible</h2>
<p>The responsible party is {RESPONSIBLE_PARTY}. Contact: {m}.</p></section>
<section id="rights"><h2>8. Your rights</h2>
<p>You can ask whether we hold information about you, and ask for a copy of it, by e-mail to {m}.</p>
<p>You can ask for a correction of your information, or object to its processing, by e-mail to {m}.</p>
<p>You can also complain to the <a href="{INFO_REGULATOR_URL}">Information Regulator (South Africa)</a>.</p></section>
""".strip()
    return page("Privacy and contact", body)


def render_404() -> str:
    body = """
<h1>Page not found</h1>
<p>There is no page at this address.</p>
<ul><li><a href="/">Open the register</a></li><li><a href="/privacy/">Privacy and contact</a></li></ul>
""".strip()
    return page("Page not found", body)


ROBOTS = "User-agent: *\nDisallow: /\n"

CSV_FIELDS = ["award_date", "buyer", "tender_reference", "ocds_id", "supplier", "supplier_label", "legal_form",
              "legal_form_label", "year_cell", "usable_value_zar", "value_note", "indicator", "right_of_reply",
              "sources"]


def render_csv(model: Mapping) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    w.writeheader()
    for d in model["rows"]:
        rec = {k: d.get(k) for k in CSV_FIELDS}
        rec["usable_value_zar"] = "" if d["usable_value_zar"] is None else f"{d['usable_value_zar']:.2f}"
        rec["sources"] = " | ".join(
            f"{s['label']}: {s['url']}" + (f" (retrieved {s['retrieved']})" if s.get("retrieved") else "")
            for s in d["sources"])
        if d.get("popia_note"):
            rec["indicator"] = d["popia_note"]
        w.writerow({k: ("" if v is None else v) for k, v in rec.items()})
    return buf.getvalue()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_site(rows: Sequence[Mapping], out_dir: Path, *, lookups: Mapping[str, Mapping] | None = None,
               city_meta: Mapping[str, Mapping] | None = None, etenders_retrieved: str = "",
               input_sha256: str = "", municipal_buyers: set[str] | None = None) -> dict:
    """Write the managed site files into out_dir and return the manifest. Deterministic."""
    model = build_rows(rows, lookups=lookups, city_meta=city_meta, etenders_retrieved=etenders_retrieved,
                       municipal_buyers=municipal_buyers)
    files = {
        "index.html": render_index(model, etenders_retrieved=etenders_retrieved),
        "method/index.html": render_method(model, etenders_retrieved=etenders_retrieved),
        "privacy/index.html": render_privacy(),
        "404.html": render_404(),
        "robots.txt": ROBOTS,
        "register.csv": render_csv(model),
    }
    hashes = {k: sha256_bytes(v.encode("utf-8")) for k, v in files.items()}
    content = sha256_bytes(json.dumps(hashes, sort_keys=True).encode("utf-8"))
    manifest = {
        "site": SITE_NAME,
        "status": "DRAFT",
        "responsible_party": RESPONSIBLE_PARTY,
        "contact": ROLE_EMAIL,
        "rules": "CHG-TW-004 revision 7 and 8; built by CHG-TW-006",
        "input_sha256": input_sha256,
        "etenders_retrieved": etenders_retrieved,
        "rows_total": model["total"],
        "group_counts": model["group_counts"],
        "year_counts": model["year_counts"],
        "files": hashes,
        "content_sha256": content,
    }
    files["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    return manifest


def shown_names(model_or_rows: Iterable[Mapping]) -> set[str]:
    """Names the register shows unmasked (the only supplier names allowed in public files)."""
    return {d["supplier"] for d in model_or_rows if d.get("group") == "unmasked" and d.get("supplier")}
