"""CHG-TW-009: collectors record every fetch error, TLS certificate errors by name; nothing fails silently."""
from __future__ import annotations

import http.server
import json
import shutil
import socket
import ssl
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tw import check_live as cl
from tw import dq
from tw.fetch_log import FetchLog, classify_error, merge, summarise
from tw.nightly import live_fetch_errors


def _cert_error() -> urllib.error.URLError:
    e = ssl.SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
    e.verify_message = "unable to get local issuer certificate"
    return urllib.error.URLError(e)


@pytest.mark.parametrize("exc, kind", [
    (_cert_error(), "tls_certificate"),
    (ssl.SSLError(1, "[SSL: WRONG_VERSION_NUMBER] wrong version number"), "tls_other"),
    (urllib.error.HTTPError("https://x.example/", 500, "Server Error", {}, None), "http_error"),
    (urllib.error.URLError(socket.timeout("timed out")), "timeout"),
    (urllib.error.URLError(socket.gaierror(-2, "Name or service not known")), "dns"),
    (urllib.error.URLError(ConnectionRefusedError(111, "Connection refused")), "connection"),
    (ConnectionError("TLS certificate verification failed"), "tls_certificate"),
    (RuntimeError("boom"), "other"),
])
def test_classify_error_kinds(exc, kind) -> None:
    got, detail = classify_error(exc)
    assert got == kind
    assert detail and len(detail) <= 160
    if kind == "tls_certificate":
        assert detail.startswith("TLS certificate verification failed")


def test_classify_follows_cause_chain() -> None:
    try:
        try:
            raise _cert_error()
        except urllib.error.URLError as inner:
            raise ConnectionError("wrapped") from inner
    except ConnectionError as outer:
        assert classify_error(outer)[0] == "tls_certificate"


def test_fetch_log_records_ok_error_and_skip_and_reraises() -> None:
    log = FetchLog("src", now=lambda: "T")
    assert log.call("https://a.example/1", lambda: b"abc") == b"abc"
    with pytest.raises(urllib.error.URLError):
        log.call("https://b.example/2", lambda: (_ for _ in ()).throw(_cert_error()))
    log.skipped("https://a.example/3", "robots disallows")
    s = log.summary()
    assert s == {"attempts": 2, "ok": 1, "errors": 1, "skipped": 1,
                 "errors_by_kind": {"tls_certificate": 1}, "tls_error_hosts": ["b.example"]}
    m = merge(log, None, {"source": "other", "events": []})
    assert m["summary"]["errors"] == 1 and set(m["by_source"]) == {"src", "other"}
    assert m["errors"][0]["kind"] == "tls_certificate"


def _cfg(pdf: str | None = "https://city.example/a/tenders-awarded-october-2026.pdf") -> dict:
    return {"city_register": {"robots_url": "https://city.example/robots.txt",
                              "index_url": "https://city.example/tenders-awarded/", "known_pdf": pdf,
                              "request_pause_s": 0}}


def test_light_fetch_records_tls_error_on_a_pdf(tmp_path: Path) -> None:
    from tw.city_register import light_fetch

    def fake_get(url, dest=None, timeout=60):
        if url.endswith(".pdf"):
            raise _cert_error()
        return b"User-agent: *\nAllow: /\n" if "robots" in url else b"<html></html>"

    r = light_fetch(tmp_path, _cfg(), sleep=lambda s: None, http_get=fake_get)
    assert r["rows"] == []
    assert any("tls_certificate" in e for e in r["errors"]), r["errors"]
    s = r["fetch_log"]["summary"]
    assert s["errors_by_kind"] == {"tls_certificate": 1} and s["tls_error_hosts"] == ["city.example"]
    assert s["ok"] == 2  # robots.txt and the index page are recorded as well
    json.dumps(r["fetch_log"])  # serialisable for the run record


def test_light_fetch_robots_tls_error_fails_closed_and_is_recorded(tmp_path: Path) -> None:
    from tw.city_register import light_fetch

    calls = []

    def fake_get(url, dest=None, timeout=60):
        calls.append(url)
        raise _cert_error()

    r = light_fetch(tmp_path, _cfg(), sleep=lambda s: None, http_get=fake_get)
    assert calls == ["https://city.example/robots.txt"]
    assert r["errors"] and "tls_certificate" in r["errors"][0]
    assert r["fetch_log"]["summary"]["errors"] == 1 and r["fetch_log"]["summary"]["skipped"] == 1


def test_dq_report_warns_on_fetch_errors_and_fallbacks(tmp_path: Path) -> None:
    log = FetchLog("src", now=lambda: "T")
    log.error("https://b.example/x", _cert_error())
    rep = dq.build_report(rfc="CHG-TW-009", run_at="T", fetch=dq.fetch_section(log), fallbacks=["sample used"])
    assert rep["status"] == "WARN"
    assert "1 fetch error(s) of kind tls_certificate" in rep["notes"]
    clean = dq.build_report(rfc="CHG-TW-009", run_at="T", fetch=dq.fetch_section(FetchLog("s")))
    assert clean["status"] == "OK"
    p = dq.write_report(tmp_path / "dq.json", rep)
    text = p.read_text(encoding="utf-8")
    assert "/workspace" not in text and "/home/" not in text and "/tmp" not in text


def test_nightly_counts_live_fetch_errors() -> None:
    results = [("tls_home", cl.FAIL, "TLS certificate verification failed [fetch error: tls_certificate]"),
               ("page /", cl.PASS, "ok"), ("robots", cl.FAIL, "HTTP 502 [fetch error: http_error]")]
    assert live_fetch_errors(results) == {"count": 2, "by_kind": {"http_error": 1, "tls_certificate": 1}}
    assert live_fetch_errors([]) == {"count": 0, "by_kind": {}}


# --- a real TLS failure: a local HTTPS server with a self-signed certificate ------------------------


@pytest.fixture()
def self_signed_server(tmp_path: Path):
    if not shutil.which("openssl"):
        pytest.skip("openssl not installed")
    key, crt = tmp_path / "k.pem", tmp_path / "c.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(crt),
                    "-days", "1", "-subj", "/CN=localhost"], check=True, capture_output=True)
    srv = http.server.HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(crt, key)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"https://localhost:{srv.server_address[1]}"
    srv.shutdown()


def test_real_self_signed_certificate_is_classified(self_signed_server: str) -> None:
    from tw.city_register import _http_get

    with pytest.raises(Exception) as ei:
        _http_get(self_signed_server + "/robots.txt", timeout=5)
    assert classify_error(ei.value)[0] == "tls_certificate"


def test_check_live_names_a_real_certificate_error(self_signed_server: str) -> None:
    fetch = cl.make_fetch(self_signed_server, timeout=5, retries=0)
    res = cl.check_live(self_signed_server, fetch=fetch)
    assert res[0][0] == "tls_home" and res[0][1] == cl.FAIL
    assert res[0][2].startswith("TLS certificate verification failed")
    assert res[0][2].endswith("[fetch error: tls_certificate]")
    assert live_fetch_errors(res)["by_kind"] == {"tls_certificate": 1}
