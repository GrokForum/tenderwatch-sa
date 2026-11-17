"""City of Cape Town monthly award-register ingest (read-only, light fetch, provenance kept)."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from tw.config import DEFAULT_BUYER, RIGHT_OF_REPLY, ROOT
from tw.normalise import extract_cipc, extract_csd, norm_name, parse_mdy, registration_year_from_cipc
from tw.supplier_type import classify_supplier_type

SAST = timezone(timedelta(hours=2), name="SAST")
USER_AGENT = "TenderWatchSA-DEV/0.1 (research; local box; read-only award register)"
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


def parse_register_pdf(pdf_path: Path, *, source_url: str, retrieved_at: str, period: str | None = None) -> list[dict]:
    """Parse a City monthly award PDF via pdftotext -layout."""
    proc = subprocess.run(
        ["pdftotext", "-layout", "-nopgbrk", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = proc.stdout
    rows: list[dict] = []
    # Rows typically start with a TTS reference like 016S/2026/27 or 293C/2024/25.
    tts_re = re.compile(r"^\s*(\d{2,4}[A-Z]/\d{4}/\d{2})\s+(\S+(?:\s+\S+)*?)\s{2,}(.+?)\s{2,}(.+?)\s+(\d{1,2}/\d{1,2}/\d{4})\s*$")
    # Fallback: looser split when layout is ragged
    loose_re = re.compile(
        r"(\d{2,4}[A-Z]/\d{4}/\d{2})\s+(SCMB\s+\S+|C\d+\s+\S+|\S+)\s+(.+?)\s{2,}(.+?)\s+(\d{1,2}/\d{1,2}/\d{4})"
    )
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        m = tts_re.match(line) or loose_re.search(line)
        if not m:
            continue
        tts, decision, desc, vendor, dt = m.groups()
        vendor = re.sub(r"\s+", " ", vendor).strip(" .")
        desc = re.sub(r"\s+", " ", desc).strip()
        rows.append(
            row_from_register(
                tts_reference=tts,
                decision_reference=re.sub(r"\s+", " ", decision).strip(),
                description=desc,
                vendor=vendor,
                date_published=dt,
                source_url=source_url,
                source_file=str(pdf_path),
                retrieved_at=retrieved_at,
                period=period,
            )
        )
    return rows


def light_fetch(raw_dir: Path, cfg: dict) -> dict:
    """Fetch robots.txt, the official index, and allowed monthly PDFs. No login."""
    city = cfg["city_register"]
    robots_url = city["robots_url"]
    index_url = city["index_url"]
    known_pdf = city.get("known_pdf")
    result = {
        "robots_allowed": {},
        "fetched": [],
        "skipped": [],
        "errors": [],
        "rows": [],
        "provenance_written": [],
    }
    try:
        robots_txt = _http_get(robots_url, dest=raw_dir / "robots.txt").decode("utf-8", errors="replace")
        result["fetched"].append(robots_url)
    except Exception as exc:  # noqa: BLE001 — record and fall back
        result["errors"].append(f"robots.txt: {type(exc).__name__}: {exc}")
        robots_txt = "User-agent: *\nAllow: /\n"
        result["skipped"].append("robots fetch failed; will not guess Allow")
        return result

    targets = [index_url]
    if known_pdf:
        targets.append(known_pdf)
    for url in targets:
        result["robots_allowed"][url] = robots_allows(robots_txt, url)
        if not result["robots_allowed"][url]:
            result["skipped"].append(f"robots disallows {url}")
            continue
        if url == index_url:
            try:
                body = _http_get(url, dest=raw_dir / "tenders-awarded.html")
                result["fetched"].append(url)
                html = body.decode("utf-8", errors="replace")
                pdfs = sorted(set(re.findall(r'href="([^"]*tenders-awarded-[^"]+\.pdf)"', html, flags=re.I)))
                # also SharePoint-style media paths without the phrase
                if not pdfs:
                    pdfs = sorted(set(re.findall(r'href="([^"]+\.pdf)"', html, flags=re.I)))
                    pdfs = [u for u in pdfs if re.search(r"tenders-awarded|award", u, re.I)]
                for href in pdfs:
                    abs_url = urljoin(url, href)
                    if not robots_allows(robots_txt, abs_url):
                        result["skipped"].append(f"robots disallows {abs_url}")
                        continue
                    if abs_url not in targets:
                        targets.append(abs_url)
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"index: {type(exc).__name__}: {exc}")
            continue
        # PDF
        name = Path(urlparse(url).path).name or "register.pdf"
        dest = raw_dir / name
        try:
            _http_get(url, dest=dest)
            result["fetched"].append(url)
            retrieved_at = _now_sast_label()
            period = None
            pm = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)[-_ ]?(20\d{2})", name, re.I)
            if pm:
                months = {m: i for i, m in enumerate(["january","february","march","april","may","june","july","august","september","october","november","december"], 1)}
                period = f"{pm.group(2)}-{months[pm.group(1).lower()]:02d}"
            rows = parse_register_pdf(dest, source_url=url, retrieved_at=retrieved_at, period=period)
            result["rows"].extend(rows)
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"pdf {url}: {type(exc).__name__}: {exc}")
    return result
