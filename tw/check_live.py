"""CHG-TW-007: read-only live check of the TenderWatch test site.

Fetches public URLs with TLS verification on and reports PASS or FAIL per check. Writes nothing, sends no
cookies or credentials. Standard library only. Pattern: PublicFunds scripts/check_live.py (CHG-2026-032/061).

Checks:
  tls_home        GET / over HTTPS with certificate verification returns 200
  page:<path>     /, /method/ and /privacy/ return 200 with the DRAFT banner, the noindex meta and a privacy link
  not_found       a missing path returns 404 with the DRAFT banner, the noindex meta and a privacy link
  robots          /robots.txt is exactly "User-agent: *" then "Disallow: /"
  privacy_page    the privacy page names GrokForum, the role address and the Information Regulator
  manifest        /manifest.json is JSON with status DRAFT, and (if an expected build is given) the same content hash
  files           every file the live manifest lists is served with the sha256 the manifest gives
"""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Mapping

DEFAULT_SITE = "https://tenderwatch.grokforum.site"
USER_AGENT = "tenderwatch-check/1"
PASS, FAIL = "PASS", "FAIL"
PAGES = ("/", "/method/", "/privacy/")
MISSING_PATH = "/tw-live-check-missing-page/"
NOINDEX_RE = re.compile(r'<meta name="robots" content="noindex,\s*nofollow">')
DRAFT_MARK = "<strong>DRAFT.</strong>"
PRIVACY_LINK = 'href="/privacy/"'
ROLE_EMAIL = "privacy@grokforum.site"
INFO_REGULATOR = "https://inforegulator.org.za/"
ROBOTS_RE = re.compile(r"\AUser-agent: \*\r?\nDisallow: /\r?\n?\Z")

Fetch = Callable[[str], tuple[int, bytes]]


class _NoRedirectOffHost(urllib.request.HTTPRedirectHandler):
    def __init__(self, host: str):
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        if urllib.parse.urlsplit(newurl).hostname != self.host:
            raise urllib.error.HTTPError(newurl, code, "redirect off host refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def make_fetch(site: str, *, timeout: float = 20.0, retries: int = 2, retry_delay: float = 5.0,
               verify_tls: bool = True) -> Fetch:
    host = urllib.parse.urlsplit(site).hostname
    ctx = ssl.create_default_context()
    if not verify_tls:  # tests only (plain-http local server); never used by the nightly
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx), _NoRedirectOffHost(host))

    def fetch(url: str) -> tuple[int, bytes]:
        last: Exception | None = None
        for attempt in range(retries + 1):
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
            try:
                with opener.open(req, timeout=timeout) as r:
                    return r.status, r.read(5_000_000)
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    return e.code, e.read(5_000_000) if e.fp else b""
                last = e
            except (urllib.error.URLError, OSError, ssl.SSLError) as e:
                last = e
            if attempt < retries:
                time.sleep(retry_delay)
        raise ConnectionError(_describe(last))

    return fetch


def _describe(e: Exception | None) -> str:
    if e is None:
        return "unknown error"
    reason = getattr(e, "reason", None)
    if isinstance(reason, ssl.SSLCertVerificationError) or isinstance(e, ssl.SSLCertVerificationError):
        return "TLS certificate verification failed"
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    return type(reason or e).__name__


def _page_ok(status: int, body: bytes, want: int) -> str | None:
    t = body.decode("utf-8", "replace")
    missing = [n for n, ok in (("DRAFT banner", DRAFT_MARK in t), ("noindex meta", bool(NOINDEX_RE.search(t))),
                               ("privacy link", PRIVACY_LINK in t)) if not ok]
    if status != want:
        return f"HTTP {status} (want {want})"
    if missing:
        return "missing: " + ", ".join(missing)
    return None


def check_live(site: str = DEFAULT_SITE, *, expected: Mapping | None = None, fetch: Fetch | None = None) -> list[tuple[str, str, str]]:
    """Run every check; never raises. Returns (check, PASS|FAIL, detail) tuples."""
    site = site.rstrip("/")
    fetch = fetch or make_fetch(site)
    out: list[tuple[str, str, str]] = []

    def get(path: str) -> tuple[int, bytes] | str:
        try:
            return fetch(site + path)
        except Exception as e:  # noqa: BLE001
            return str(e) or type(e).__name__

    home = get("/")
    if isinstance(home, str):
        out.append(("tls_home", FAIL, home))
        return out  # nothing else can pass
    out.append(("tls_home", PASS if home[0] == 200 else FAIL, f"HTTP {home[0]}"))
    pages = {"/": home}
    for path in PAGES[1:]:
        pages[path] = get(path)
    for path, res in pages.items():
        if isinstance(res, str):
            out.append((f"page:{path}", FAIL, res))
            continue
        bad = _page_ok(res[0], res[1], 200)
        out.append((f"page:{path}", FAIL if bad else PASS, bad or "DRAFT, noindex, privacy link"))
    nf = get(MISSING_PATH)
    if isinstance(nf, str):
        out.append(("not_found", FAIL, nf))
    else:
        bad = _page_ok(nf[0], nf[1], 404)
        out.append(("not_found", FAIL if bad else PASS, bad or "404 with DRAFT, noindex, privacy link"))
    rb = get("/robots.txt")
    if isinstance(rb, str):
        out.append(("robots", FAIL, rb))
    else:
        ok = rb[0] == 200 and bool(ROBOTS_RE.match(rb[1].decode("utf-8", "replace")))
        out.append(("robots", PASS if ok else FAIL, "Disallow: /" if ok else f"HTTP {rb[0]} or content changed"))
    priv = pages.get("/privacy/")
    if isinstance(priv, tuple):
        t = priv[1].decode("utf-8", "replace")
        miss = [s for s in ("GrokForum", f"mailto:{ROLE_EMAIL}", INFO_REGULATOR) if s not in t]
        out.append(("privacy_page", FAIL if miss else PASS, ("missing: " + ", ".join(miss)) if miss else "responsible party, role address, regulator"))
    else:
        out.append(("privacy_page", FAIL, "privacy page not fetched"))
    mf = get("/manifest.json")
    manifest = None
    if isinstance(mf, str):
        out.append(("manifest", FAIL, mf))
    elif mf[0] != 200:
        out.append(("manifest", FAIL, f"HTTP {mf[0]}"))
    else:
        try:
            manifest = json.loads(mf[1].decode("utf-8"))
        except ValueError:
            out.append(("manifest", FAIL, "not JSON"))
        if manifest is not None:
            if manifest.get("status") != "DRAFT":
                out.append(("manifest", FAIL, "status is not DRAFT"))
            elif expected is not None and manifest.get("content_sha256") != expected.get("content_sha256"):
                out.append(("manifest", FAIL, "live content differs from tonight's build"))
            else:
                out.append(("manifest", PASS, "DRAFT" + (", matches tonight's build" if expected is not None else "")))
    if isinstance(manifest, dict) and isinstance(manifest.get("files"), dict):
        bad_files = []
        for rel, digest in sorted(manifest["files"].items()):
            path = "/" + ("" if rel == "index.html" else rel.removesuffix("index.html"))
            if rel == "404.html":
                path = "/404.html"
            res = get(path)
            if isinstance(res, str) or res[0] != 200 or hashlib.sha256(res[1]).hexdigest() != digest:
                bad_files.append(rel)
        out.append(("files", FAIL if bad_files else PASS,
                    ("sha256 differs or not served: " + ", ".join(bad_files)) if bad_files else f"{len(manifest['files'])} files match"))
    else:
        out.append(("files", FAIL, "no file list in the live manifest"))
    return out


def overall(results: list[tuple[str, str, str]]) -> str:
    return PASS if results and all(s == PASS for _, s, _ in results) else FAIL
