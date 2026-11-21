"""CHG-TW-009: every collector fetch is recorded; a failed fetch is never silent.

A collector wraps each HTTP request with ``FetchLog.call`` (or records it with ``ok``/``error``/``skipped``).
Errors are classified so the run record and the data-quality report can say *why* a source was not read:

* ``tls_certificate``  the server's certificate did not verify (for example an incomplete chain). TLS
  verification is never switched off to get past this; the source is reported as not read.
* ``tls_other``        any other TLS failure (handshake, protocol).
* ``http_error``       the server answered with an HTTP error status (4xx or 5xx).
* ``timeout``          no answer in time.
* ``dns``              the host name did not resolve.
* ``connection``       refused, reset or unreachable.
* ``other``            anything else (the exception class is kept).

Details are short and carry no local file paths, no file: (or other non-http(s) scheme) URLs, and no URL
userinfo or query strings: only the scrubbed http(s) URL, the kind and a one-line reason.
"""
from __future__ import annotations

import re
import socket
import ssl
import urllib.error
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

SAST = timezone(timedelta(hours=2), "SAST")
KINDS = ("tls_certificate", "tls_other", "http_error", "timeout", "dns", "connection", "other")
MAX_DETAIL = 160

_SCHEME_URL_RE = re.compile(
    r'(?i)(?<![a-z0-9+.-])(?:[a-z][a-z0-9+.-]*:)*'
    r'(?:file:/*|[a-z][a-z0-9+.-]*://|[a-z][a-z0-9+.-]*:(?![\d\s/\\]))'
    r'[^\s<>"\'\])\}]+'
)
# Any leading RFC 3986 scheme (data:, javascript:, mailto:, vbscript:, about:, ...) is matched; only
# http(s) URLs are kept (host and path). "host:443" (digit after the colon) and "Error: x" (space) are
# not schemes; Windows drive paths ("C:\\") are left to _WIN_PATH_RE.
_QUOTED_PATH_RE = re.compile(r"""(['"])(?:~?[\\/]|[A-Za-z]:[\\/])[^'"]+\1""")
_WIN_PATH_RE = re.compile(r"""(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s'"\])}>,;]+""")
_HOME_PATH_RE = re.compile(r"""(?<![A-Za-z0-9_.:/-])~[\\/][^\s'"\])}>,;]+""")
_UNIX_MULTI_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.:/-])/(?:[A-Za-z0-9._~@-]+/)+[A-Za-z0-9._~@-]*")
_UNIX_TOP_PATH_RE = re.compile(
    r"""(?<![A-Za-z0-9_.:/-])/(?:tmp|home|workspace|var|etc|usr|opt|root|Users|cursor|mnt|srv|proc|sys|dev|run|boot|lib|bin|sbin)(?:/[^\s'"\])}>,;]*)?"""
)


def _now() -> str:
    return datetime.now(SAST).isoformat(timespec="seconds")


def _leading_schemes(url: str) -> list[str]:
    """Scheme names at the start of a URL, including nested schemes such as jar:file:."""
    m = re.match(r"(?i)^((?:[a-z][a-z0-9+.-]*:)+)", str(url or "").strip())
    if not m:
        return []
    return re.findall(r"(?i)([a-z][a-z0-9+.-]*):", m.group(1))


def _is_http_url(url: str) -> bool:
    schemes = _leading_schemes(url)
    return bool(schemes) and all(s.lower() in {"http", "https"} for s in schemes)


def scrub_url(url: str) -> str:
    """Strip userinfo (user:pass@), query strings and fragments from an http(s) URL.

    file: and any other non-http(s) scheme (ftp:, jar:file:, …) are treated as a local
    path and replaced with ``<path>``.
    """
    s = str(url or "").strip()
    if not s:
        return s
    if _leading_schemes(s) and not _is_http_url(s):
        return "<path>"
    try:
        parts = urlsplit(s)
    except ValueError:
        s = re.sub(r"(^[a-zA-Z][a-zA-Z0-9+.-]*://)[^/@]+@", r"\1", s)
        return s.split("?", 1)[0].split("#", 1)[0]
    if parts.scheme and parts.netloc:
        try:
            host = parts.hostname or ""
            port = parts.port
        except ValueError:
            host = parts.netloc.rsplit("@", 1)[-1]
            port = None
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = f"{host}:{port}" if port is not None else host
        return urlunsplit((parts.scheme, netloc, parts.path, "", ""))
    return s.split("?", 1)[0].split("#", 1)[0]


def scrub_text(text: str) -> str:
    """Remove local filesystem paths and scrub userinfo/query strings from URLs in error text.

    file: and any other non-http(s) scheme URL are redacted like a bare path (``<path>``);
    http(s) URLs keep the scheme, host and path, with userinfo, query and fragment removed.
    """
    s = str(text or "")
    saved_urls: list[str] = []

    def _hold_or_redact(m: re.Match[str]) -> str:
        raw = m.group(0)
        trail = ""
        while raw and raw[-1] in ".,;:":
            trail = raw[-1] + trail
            raw = raw[:-1]
        if raw and not _is_http_url(raw):
            return "<path>" + trail
        token = f"__TW_URL_{len(saved_urls)}__"
        saved_urls.append(scrub_url(raw))
        return token + trail

    s = _SCHEME_URL_RE.sub(_hold_or_redact, s)
    s = _QUOTED_PATH_RE.sub("'<path>'", s)
    s = _WIN_PATH_RE.sub("<path>", s)
    s = _HOME_PATH_RE.sub("<path>", s)
    s = _UNIX_MULTI_PATH_RE.sub("<path>", s)
    s = _UNIX_TOP_PATH_RE.sub("<path>", s)
    for i, url in enumerate(saved_urls):
        s = s.replace(f"__TW_URL_{i}__", url)
    return s


def _exc_text(e: BaseException) -> str:
    if isinstance(e, OSError) and (getattr(e, "filename", None) is not None or getattr(e, "filename2", None) is not None):
        msg = e.strerror or "OS error"
        base = f"[Errno {e.errno}] {msg}" if e.errno is not None else msg
        return scrub_text(base)
    return scrub_text(str(e))


def _short(text: str) -> str:
    text = " ".join(scrub_text(str(text)).split())
    return text if len(text) <= MAX_DETAIL else text[: MAX_DETAIL - 1] + "…"


def classify_error(exc: BaseException) -> tuple[str, str]:
    """Return (kind, one-line detail) for a fetch exception. Never raises."""
    seen: set[int] = set()
    e: BaseException | None = exc
    chain: list[BaseException] = []
    while e is not None and id(e) not in seen:  # walk reason / cause / context once
        seen.add(id(e))
        chain.append(e)
        nxt = getattr(e, "reason", None)
        if not isinstance(nxt, BaseException):
            nxt = e.__cause__ or e.__context__
        e = nxt
    for e in chain:
        if isinstance(e, ssl.SSLCertVerificationError):
            msg = getattr(e, "verify_message", None) or _exc_text(e)
            return "tls_certificate", _short(f"TLS certificate verification failed: {msg}")
    for e in chain:
        if isinstance(e, urllib.error.HTTPError):
            return "http_error", f"HTTP {e.code}"
    for e in chain:
        if isinstance(e, ssl.SSLError):
            msg = _exc_text(e)
            if "CERTIFICATE_VERIFY_FAILED" in msg:
                return "tls_certificate", _short(f"TLS certificate verification failed: {msg}")
            return "tls_other", _short(f"TLS error: {type(e).__name__}: {msg}")
    for e in chain:
        if isinstance(e, (socket.timeout, TimeoutError)):
            return "timeout", "timed out"
    for e in chain:
        if isinstance(e, socket.gaierror):
            return "dns", _short(f"name did not resolve: {_exc_text(e)}")
    # A message that names the certificate problem (for example a wrapped ConnectionError) still counts.
    for e in chain:
        msg = _exc_text(e)
        if "CERTIFICATE_VERIFY_FAILED" in msg or "certificate verification failed" in msg.lower():
            return "tls_certificate", _short(msg if msg.lower().startswith("tls certificate verification failed")
                                             else f"TLS certificate verification failed: {msg}")
    for e in chain:
        if isinstance(e, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            return "connection", _short(f"{type(e).__name__}: {_exc_text(e)}")
    for e in chain:
        if isinstance(e, urllib.error.URLError):
            reason = getattr(e, "reason", e)
            rtxt = _exc_text(reason) if isinstance(reason, BaseException) else scrub_text(str(reason))
            return "connection", _short(f"URLError: {rtxt}")
    return "other", _short(f"{type(exc).__name__}: {_exc_text(exc)}")


class FetchLog:
    """Ordered record of one collector's fetch attempts for one run."""

    def __init__(self, source: str, now: Callable[[], str] = _now):
        self.source = source
        self.events: list[dict] = []
        self._now = now

    def ok(self, url: str, *, note: str | None = None, nbytes: int | None = None) -> None:
        ev = {"source": self.source, "url": scrub_url(url), "outcome": "ok", "at": self._now()}
        if note:
            ev["note"] = note
        if nbytes is not None:
            ev["bytes"] = nbytes
        self.events.append(ev)

    def error(self, url: str, exc: BaseException) -> dict:
        clean_url = scrub_url(url)
        kind, detail = classify_error(exc)
        ev = {"source": self.source, "url": clean_url, "outcome": "error", "kind": kind, "detail": detail,
              "host": urlsplit(clean_url).hostname or "", "at": self._now()}
        self.events.append(ev)
        return ev

    def skipped(self, url: str, reason: str) -> None:
        self.events.append({"source": self.source, "url": scrub_url(url), "outcome": "skipped",
                            "detail": _short(reason), "at": self._now()})

    def call(self, url: str, fn: Callable[[], Any], *, note: str | None = None) -> Any:
        """Run fn(); record ok or the classified error, then re-raise so the caller decides what to do."""
        try:
            out = fn()
        except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
            self.error(url, exc)
            raise
        self.ok(url, note=note, nbytes=len(out) if isinstance(out, (bytes, bytearray)) else None)
        return out

    def errors(self) -> list[dict]:
        return [e for e in self.events if e["outcome"] == "error"]

    def summary(self) -> dict:
        return summarise(self.events)

    def as_dict(self) -> dict:
        return {"source": self.source, "events": list(self.events), "summary": self.summary()}


def summarise(events: list[dict]) -> dict:
    """Counts only (no bodies): attempts, ok, errors, skipped, errors by kind and the hosts with TLS errors."""
    out = Counter(e.get("outcome") for e in events)
    kinds = Counter(e.get("kind") for e in events if e.get("outcome") == "error")
    tls_hosts = sorted({e.get("host", "") for e in events
                        if e.get("outcome") == "error" and str(e.get("kind", "")).startswith("tls")} - {""})
    return {
        "attempts": out.get("ok", 0) + out.get("error", 0),
        "ok": out.get("ok", 0),
        "errors": out.get("error", 0),
        "skipped": out.get("skipped", 0),
        "errors_by_kind": {k: kinds[k] for k in KINDS if kinds.get(k)},
        "tls_error_hosts": tls_hosts,
    }


def merge(*logs: dict | FetchLog | None) -> dict:
    """One fetch section for a run record from several collectors' logs."""
    events: list[dict] = []
    sources: dict[str, dict] = {}
    for lg in logs:
        if lg is None:
            continue
        d = lg.as_dict() if isinstance(lg, FetchLog) else lg
        events.extend(d.get("events") or [])
        sources[d.get("source", "unknown")] = summarise(d.get("events") or [])
    return {"summary": summarise(events), "by_source": sources,
            "errors": [{k: e.get(k) for k in ("source", "url", "kind", "detail")} for e in events
                       if e.get("outcome") == "error"]}
