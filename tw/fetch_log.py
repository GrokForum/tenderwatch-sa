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

Details are short and carry no file paths: only the URL, the kind and a one-line reason.
"""
from __future__ import annotations

import socket
import ssl
import urllib.error
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlsplit

SAST = timezone(timedelta(hours=2), "SAST")
KINDS = ("tls_certificate", "tls_other", "http_error", "timeout", "dns", "connection", "other")
MAX_DETAIL = 160


def _now() -> str:
    return datetime.now(SAST).isoformat(timespec="seconds")


def _short(text: str) -> str:
    text = " ".join(str(text).split())
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
            msg = getattr(e, "verify_message", None) or str(e)
            return "tls_certificate", _short(f"TLS certificate verification failed: {msg}")
    for e in chain:
        if isinstance(e, urllib.error.HTTPError):
            return "http_error", f"HTTP {e.code}"
    for e in chain:
        if isinstance(e, ssl.SSLError):
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                return "tls_certificate", _short(f"TLS certificate verification failed: {e}")
            return "tls_other", _short(f"TLS error: {type(e).__name__}: {e}")
    for e in chain:
        if isinstance(e, (socket.timeout, TimeoutError)):
            return "timeout", "timed out"
    for e in chain:
        if isinstance(e, socket.gaierror):
            return "dns", _short(f"name did not resolve: {e}")
    # A message that names the certificate problem (for example a wrapped ConnectionError) still counts.
    for e in chain:
        msg = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in msg or "certificate verification failed" in msg.lower():
            return "tls_certificate", _short(msg if msg.lower().startswith("tls certificate verification failed")
                                             else f"TLS certificate verification failed: {msg}")
    for e in chain:
        if isinstance(e, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            return "connection", _short(f"{type(e).__name__}: {e}")
    for e in chain:
        if isinstance(e, urllib.error.URLError):
            return "connection", _short(f"URLError: {getattr(e, 'reason', e)}")
    return "other", _short(f"{type(exc).__name__}: {exc}")


class FetchLog:
    """Ordered record of one collector's fetch attempts for one run."""

    def __init__(self, source: str, now: Callable[[], str] = _now):
        self.source = source
        self.events: list[dict] = []
        self._now = now

    def ok(self, url: str, *, note: str | None = None, nbytes: int | None = None) -> None:
        ev = {"source": self.source, "url": url, "outcome": "ok", "at": self._now()}
        if note:
            ev["note"] = note
        if nbytes is not None:
            ev["bytes"] = nbytes
        self.events.append(ev)

    def error(self, url: str, exc: BaseException) -> dict:
        kind, detail = classify_error(exc)
        ev = {"source": self.source, "url": url, "outcome": "error", "kind": kind, "detail": detail,
              "host": urlsplit(url).hostname or "", "at": self._now()}
        self.events.append(ev)
        return ev

    def skipped(self, url: str, reason: str) -> None:
        self.events.append({"source": self.source, "url": url, "outcome": "skipped", "detail": _short(reason),
                            "at": self._now()})

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
