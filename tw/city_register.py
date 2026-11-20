"""City of Cape Town monthly award-register ingest (read-only, light fetch, provenance kept)."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

from tw.config import DEFAULT_BUYER, RIGHT_OF_REPLY, ROOT
from tw.fetch_log import FetchLog, classify_error, scrub_text, scrub_url
from tw.normalise import extract_cipc, extract_csd, norm_name, parse_mdy, registration_year_from_cipc
from tw.supplier_type import classify_supplier_type

SAST = timezone(timedelta(hours=2), name="SAST")
USER_AGENT = "TenderWatchSA-DEV/0.1 (research; local box; read-only award register)"
DEFAULT_REQUEST_PAUSE_S = 1.5
SOURCE_ID = "city_of_cape_town_register"
SAMPLE_CSV = ROOT / "data/samples/city-of-cape-town/tenders-awarded-october-2026-samples.csv"

# Conservative robots: we only request paths under the official City site.


def _now_sast_label() -> str:
    return datetime.now(SAST).strftime("%Y-%m-%d %H:%M SAST (Africa/Johannesburg)")


def row_from_register(
    *,
    tts_reference: str | None,
    decision_reference: str | None,
    description: str | None,
    vendor: str | None,
    date_published: str | None,
    date_interpreted: str | None = None,
    source_url: str,
    source_file: str,
    retrieved_at: str,
    period: str | None = None,
) -> dict:
    vendor = (vendor or "").strip() or None
    typ = classify_supplier_type(vendor)
    cipc = extract_cipc(" ".join(x for x in (vendor, tts_reference, decision_reference, description) if x))
    csd = extract_csd(" ".join(x for x in (vendor, tts_reference, decision_reference, description) if x))
    if typ != "juristic":
        cipc = None
    decided = parse_mdy(date_interpreted) or parse_mdy(date_published)
    return {
        "source": "city_of_cape_town_award_register",
        "period": period,
        "tts_reference": (tts_reference or "").strip() or None,
        "decision_reference": (decision_reference or "").strip() or None,
        "description": (description or "").strip() or None,
        "supplier_name": vendor,
        "vendor": vendor,
        "name_key": norm_name(vendor),
        "supplier_type": typ,
        "buyer_name": DEFAULT_BUYER,
        "jurisdiction": DEFAULT_BUYER,
        "date_of_decision_as_published": date_published,
        "award_date": decided.isoformat() if decided else None,
        "cipc_reg_no": cipc,
        "csd_no": csd,
        "registration_year": registration_year_from_cipc(cipc) if typ == "juristic" else None,
        "fact_label": "Confirmed",
        "right_of_reply": RIGHT_OF_REPLY,
        "source_url": source_url,
        "source_file": source_file,
        "retrieved_at": retrieved_at,
    }


def load_sample_csv(path: Path | None = None) -> list[dict]:
    path = path or SAMPLE_CSV
    provenance = path.parent / "PROVENANCE.md"
    source_url = "https://www.capetown.gov.za/media/nb1fgwta/tenders-awarded-october-2026.pdf"
    retrieved_at = "2026-11-17 10:57 SAST (Africa/Johannesburg)"
    if provenance.is_file():
        text = provenance.read_text(encoding="utf-8")
        m = re.search(r"File URL fetched:\s*(\S+)", text)
        if m:
            source_url = m.group(1)
        m = re.search(r"Fetched:\s*(.+)", text)
        if m:
            retrieved_at = m.group(1).strip()
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            rows.append(
                row_from_register(
                    tts_reference=rec.get("tts_reference"),
                    decision_reference=rec.get("decision_reference"),
                    description=rec.get("description"),
                    vendor=rec.get("vendor"),
                    date_published=rec.get("date_of_decision_as_published"),
                    date_interpreted=rec.get("date_of_decision_interpreted_sast"),
                    source_url=source_url,
                    source_file=str(path),
                    retrieved_at=retrieved_at,
                    period="2026-10",
                )
            )
    return rows


def robots_allows(robots_txt: str, url: str, user_agent: str = USER_AGENT) -> bool:
    rp = RobotFileParser()
    rp.parse(robots_txt.splitlines())
    return rp.can_fetch(user_agent, url) or rp.can_fetch("*", url)


def _http_get(url: str, dest: Path | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        final = resp.geturl()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        meta = dest.with_suffix(dest.suffix + ".provenance.json")
        meta.write_text(
            json.dumps(
                {
                    "url": url,
                    "final_url": final,
                    "fetched_at": _now_sast_label(),
                    "bytes": len(data),
                    "user_agent": USER_AGENT,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return data



_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}


def period_from_filename(name: str) -> str | None:
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)[-_ ]?(20\d{2})", name, re.I)
    if not m:
        return None
    return f"{m.group(2)}-{_MONTHS[m.group(1).lower()]:02d}"


def is_plausible_vendor(name: str | None) -> bool:
    """Drop PDF-wrap fragments so a stray date or punctuation is not stored as a vendor."""
    if not name:
        return False
    s = name.strip()
    if len(s) < 4:
        return False
    letters = sum(ch.isalpha() for ch in s)
    if letters < 3:
        return False
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}", s):
        return False
    return True


TTS_RE = re.compile(r"(\d{2,4}[A-Z]/\d{4}/\d{2})")
DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")
MEDIA_2026_RE = re.compile(r"tenders-awarded-[a-z]+-2026\.pdf", re.I)


def parse_layout_text(
    text: str,
    *,
    source_url: str,
    source_file: str,
    retrieved_at: str,
    period: str | None = None,
) -> list[dict]:
    """Column-aware parse of pdftotext -layout output.

    Vendor-only lines (no TTS reference) are held and attached to the *next*
    TTS row, which is how the City layout lists multiple vendors on one award.
    """
    lines = text.splitlines()
    header = next((ln for ln in lines if "TTS Reference" in ln and "Vendor" in ln), None)
    vcol = header.find("Vendor") if header else 198
    dcol = header.find("Date of decision") if header and "Date of decision" in header else 273
    ccol = header.find("Decision Reference") if header else 16
    ecol = header.find("Description") if header else 37

    def _slice(line: str, start: int, end: int | None) -> str:
        if end is None:
            return line[start:].strip() if len(line) > start else ""
        return line[start:end].strip() if len(line) > start else ""

    pending_vendors: list[str] = []
    raw_awards: list[dict] = []
    for line in lines:
        if not line.strip() or "TTS Reference" in line:
            continue
        tts_m = TTS_RE.search(line[: max(ccol, 16) + 8] if len(line) > 8 else line)
        # A TTS at the start of the line opens an award; a TTS later is ignored (descriptions).
        tts = None
        if tts_m and tts_m.start() <= 4:
            tts = tts_m.group(1)
        vendor = re.sub(r"\s+", " ", _slice(line, vcol, dcol)).strip(" .")
        date_s = _slice(line, dcol, None)
        date_m = DATE_RE.search(date_s) or (DATE_RE.search(line) if tts else None)
        dt = date_m.group(1) if date_m else None
        if tts:
            decision = re.sub(r"\s+", " ", _slice(line, ccol, ecol))
            desc = re.sub(r"\s+", " ", _slice(line, ecol, vcol))
            vendors = [v for v in pending_vendors if is_plausible_vendor(v)]
            if is_plausible_vendor(vendor):
                vendors.append(vendor)
            pending_vendors = []
            raw_awards.append({
                "tts": tts,
                "decision": decision,
                "desc": desc,
                "vendors": vendors,
                "date": dt,
            })
        elif is_plausible_vendor(vendor):
            pending_vendors.append(vendor)
        elif date_s and raw_awards and not raw_awards[-1]["date"]:
            raw_awards[-1]["date"] = dt

    rows: list[dict] = []
    for award in raw_awards:
        vendors = award["vendors"] or [None]
        for vendor in vendors:
            rows.append(
                row_from_register(
                    tts_reference=award["tts"],
                    decision_reference=award["decision"] or None,
                    description=award["desc"] or None,
                    vendor=vendor,
                    date_published=award["date"],
                    source_url=source_url,
                    source_file=source_file,
                    retrieved_at=retrieved_at,
                    period=period,
                )
            )
    return rows


def parse_register_pdf(pdf_path: Path, *, source_url: str, retrieved_at: str, period: str | None = None) -> list[dict]:
    """Parse a City monthly award PDF via pdftotext -layout."""
    proc = subprocess.run(
        ["pdftotext", "-layout", "-nopgbrk", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_layout_text(
        proc.stdout,
        source_url=source_url,
        source_file=str(pdf_path),
        retrieved_at=retrieved_at,
        period=period,
    )


def _absolute_pdf_url(base: str, href: str) -> str | None:
    """Resolve an href to an absolute PDF URL. Light fetch keeps to 2026 media-path monthlies."""
    if not MEDIA_2026_RE.search(href):
        return None
    if href.startswith("//"):
        abs_url = "https:" + href
    elif href.startswith("http://") or href.startswith("https://"):
        abs_url = href
    else:
        abs_url = urljoin(base, href)
    parts = urlparse(abs_url)
    path = quote(parts.path, safe="/%")
    return urlunparse((parts.scheme, parts.netloc, path, parts.params, parts.query, parts.fragment))


def light_fetch(
    raw_dir: Path,
    cfg: dict,
    *,
    sleep: Callable[[float], None] = time.sleep,
    request_pause_s: float | None = None,
    http_get: Callable[..., bytes] = _http_get,
) -> dict:
    """Fetch robots.txt, the official index, and allowed monthly PDFs. No login.

    If robots.txt cannot be read, the fetch fails closed: no further City
    requests are made. A pause (default 1.5 s, configurable) is injected
    between successive HTTP requests. ``sleep`` and ``http_get`` are
    injectable so tests can run offline.
    """
    city = cfg["city_register"]
    robots_url = city["robots_url"]
    index_url = city["index_url"]
    known_pdf = city.get("known_pdf")
    pause = DEFAULT_REQUEST_PAUSE_S if request_pause_s is None else request_pause_s
    if request_pause_s is None and city.get("request_pause_s") is not None:
        pause = float(city["request_pause_s"])
    requests_made = 0
    log = FetchLog(SOURCE_ID)  # CHG-TW-009: every request is recorded; errors are classified, never silent

    def polite_get(url: str, dest: Path | None = None) -> bytes:
        nonlocal requests_made
        if requests_made:
            sleep(pause)
        requests_made += 1
        return log.call(url, lambda: http_get(url, dest=dest))

    def err(prefix: str, exc: Exception) -> None:
        kind, detail = classify_error(exc)
        result["errors"].append(f"{scrub_text(prefix)}: {kind}: {detail}")

    result = {
        "robots_allowed": {},
        "fetched": [],
        "skipped": [],
        "errors": [],
        "rows": [],
        "provenance_written": [],
        "fetch_log": log,
    }
    try:
        robots_txt = polite_get(robots_url, dest=raw_dir / "robots.txt").decode("utf-8", errors="replace")
        result["fetched"].append(scrub_url(robots_url))
    except Exception as exc:  # noqa: BLE001 — fail closed, do not fetch further
        err("robots.txt", exc)
        result["skipped"].append("robots.txt unavailable; fail closed, no fetch")
        log.skipped(index_url, "robots.txt unavailable; fail closed, no fetch")
        result["fetch_log"] = log.as_dict()
        return result

    targets = [index_url]
    if known_pdf:
        targets.append(known_pdf)
    for url in targets:
        result["robots_allowed"][url] = robots_allows(robots_txt, url)
        if not result["robots_allowed"][url]:
            result["skipped"].append(f"robots disallows {scrub_url(url)}")
            log.skipped(url, "robots disallows")
            continue
        if url == index_url:
            try:
                body = polite_get(url, dest=raw_dir / "tenders-awarded.html")
                result["fetched"].append(scrub_url(url))
                html = body.decode("utf-8", errors="replace")
                hrefs = sorted(set(re.findall(r'href="([^"]+\.pdf)"', html, flags=re.I)))
                for href in hrefs:
                    abs_url = _absolute_pdf_url(url, href)
                    if not abs_url:
                        continue
                    if not robots_allows(robots_txt, abs_url):
                        result["skipped"].append(f"robots disallows {scrub_url(abs_url)}")
                        log.skipped(abs_url, "robots disallows")
                        continue
                    if abs_url not in targets:
                        targets.append(abs_url)
            except Exception as exc:  # noqa: BLE001
                err("index", exc)
            continue
        # PDF
        name = Path(urlparse(url).path).name or "register.pdf"
        dest = raw_dir / name
        try:
            if dest.is_file() and dest.stat().st_size > 0:
                result["fetched"].append(scrub_url(url) + " (cached)")
                log.ok(url, note="cached")
                prov = dest.with_suffix(dest.suffix + ".provenance.json")
                retrieved_at = _now_sast_label()
                if prov.is_file():
                    import json as _json
                    retrieved_at = _json.loads(prov.read_text()).get("fetched_at") or retrieved_at
            else:
                polite_get(url, dest=dest)
                result["fetched"].append(scrub_url(url))
                retrieved_at = _now_sast_label()
            period = None
            period = period_from_filename(name)
            rows = parse_register_pdf(dest, source_url=url, retrieved_at=retrieved_at, period=period)
            result["rows"].extend(rows)
        except Exception as exc:  # noqa: BLE001
            err(f"pdf {scrub_url(url)}", exc)
    result["fetch_log"] = log.as_dict()
    return result
