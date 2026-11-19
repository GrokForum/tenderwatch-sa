"""CHG-TW-007: nightly run, publish locks, live check, results log and streak. Invented names only."""
from __future__ import annotations

import csv
import functools
import http.server
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import pytest

from tw import check_live as cl
from tw import nightly, site
from tests.test_site_build import fixture_rows


# --- a local site server (plain http; TLS verification is the only part not exercised here) ---

class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            body = (Path(self.directory) / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().send_error(code, message, explain)


@pytest.fixture()
def served(tmp_path: Path):
    root = tmp_path / "www"
    manifest = site.build_site(fixture_rows(), root, etenders_retrieved="2026-10-19")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Handler, directory=str(root)))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    yield url, root, manifest
    srv.shutdown()


def _fetch(url):
    return cl.make_fetch(url, retries=0, timeout=5, verify_tls=False)


def test_check_live_passes_on_a_good_site(served):
    url, _root, manifest = served
    res = cl.check_live(url, expected=manifest, fetch=_fetch(url))
    assert cl.overall(res) == cl.PASS, res
    assert {c for c, _, _ in res} >= {"tls_home", "page:/", "page:/method/", "page:/privacy/", "not_found", "robots",
                                       "privacy_page", "manifest", "files"}


def test_check_live_fails_when_live_differs_from_tonight(served):
    url, _root, manifest = served
    res = dict((c, s) for c, s, _ in cl.check_live(url, expected={**manifest, "content_sha256": "0" * 64}, fetch=_fetch(url)))
    assert res["manifest"] == cl.FAIL


def test_check_live_catches_missing_draft_noindex_robots_and_tampering(served):
    url, root, manifest = served
    p = root / "method" / "index.html"
    p.write_text(p.read_text().replace("<strong>DRAFT.</strong>", "").replace("noindex, nofollow", "index"))
    (root / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    (root / "register.csv").write_text("tampered\n")
    res = dict((c, s) for c, s, _ in cl.check_live(url, expected=manifest, fetch=_fetch(url)))
    assert res["page:/method/"] == res["robots"] == res["files"] == cl.FAIL
    assert res["page:/"] == cl.PASS


def test_check_live_placeholder_fails(served):
    url, root, _ = served
    (root / "index.html").write_text("<html><meta name=\"robots\" content=\"noindex,nofollow\">Coming soon</html>")
    (root / "manifest.json").unlink()
    res = dict((c, s) for c, s, _ in cl.check_live(url, fetch=_fetch(url)))
    assert res["page:/"] == res["manifest"] == res["files"] == cl.FAIL


def test_check_live_tls_failure_is_a_fail():
    def bad(_url):
        raise ConnectionError("TLS certificate verification failed")
    res = cl.check_live("https://example.invalid", fetch=bad)
    assert res == [("tls_home", cl.FAIL, "TLS certificate verification failed")]
    assert cl.overall(res) == cl.FAIL
    assert cl.overall([]) == cl.FAIL


# --- fake git runner ------------------------------------------------------------

class FakeRun:
    def __init__(self, *, dirty: bool = False):
        self.calls: list[list[str]] = []
        self.dirty = dirty

    def __call__(self, cmd, cwd=None, capture_output=True, text=True, timeout=None):
        self.calls.append(list(cmd))
        out = ""
        if cmd[:3] == ["git", "rev-parse", "HEAD"]:
            out = "a" * 40
        elif cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            out = "main"
        elif cmd[:3] == ["git", "status", "--porcelain"] and self.dirty:
            out = " M README.md"
        return subprocess.CompletedProcess(cmd, 0, out, "")

    def pushed(self) -> bool:
        return any(c[:2] == ["git", "push"] for c in self.calls)


CFG = {"site_url": "https://tenderwatch.example", "site_repo": "GrokForum/tenderwatch-site", "publish_enabled": False,
       "push_log": False, "log_branch": "ops/nightly-log", "pages_wait_seconds": 0}


def _build_ok(staging: Path):
    m = site.build_site(fixture_rows(), staging)
    return {"content_sha256": m["content_sha256"], "rows_total": 9, "group_counts": m["group_counts"],
            "year_counts": m["year_counts"], "scans": {"pii": 0}, "scans_clean": True}


def _live_pass(url, expected=None):
    return [("tls_home", cl.PASS, "HTTP 200"), ("manifest", cl.PASS, "DRAFT")]


def _live_tls_fail(url, expected=None):
    return [("tls_home", cl.FAIL, "TLS certificate verification failed")]


def _now():
    return datetime(2026, 11, 20, 4, 10, tzinfo=nightly.SAST)


@pytest.mark.parametrize("enabled,flag,allowed", [(False, False, False), (False, True, False), (True, False, False), (True, True, True)])
def test_publish_needs_both_locks(enabled, flag, allowed):
    assert nightly.publish_allowed({**CFG, "publish_enabled": enabled}, flag) is allowed


def test_committed_config_keeps_publish_and_log_push_off():
    cfg = nightly.load_config()
    assert cfg["publish_enabled"] is False and cfg["push_log"] is False
    assert cfg["site_url"] == "https://tenderwatch.grokforum.site"


def test_publish_to_site_refuses_when_disabled(tmp_path: Path):
    run = FakeRun()
    with pytest.raises(nightly.PublishRefused):
        nightly.publish_to_site(tmp_path, tmp_path, CFG, True, "2026-11-20", run)
    assert run.calls == []


def test_dry_run_never_pushes_even_with_publish_flag(tmp_path: Path):
    run = FakeRun()
    rec = nightly.run_nightly(publish_flag=True, cfg=CFG, run=run, live=_live_pass, refresh=lambda: None,
                              build=_build_ok, now=_now, log_commit=False, nightly_dir=tmp_path / "n",
                              staging=tmp_path / "s")
    assert rec["publish"] == "dry-run (publish not enabled)"
    assert not run.pushed()
    assert rec["result"] == "PASS"  # live serves tonight's build (stubbed)


def test_night_fails_on_tls_failure_and_is_recorded(tmp_path: Path):
    rec = nightly.run_nightly(cfg=CFG, run=FakeRun(), live=_live_tls_fail, refresh=lambda: None, build=_build_ok,
                              now=_now, log_commit=False, nightly_dir=tmp_path / "n", staging=tmp_path / "s")
    assert rec["result"] == "FAIL" and rec["check_live"] == "FAIL"
    rows = list(csv.DictReader((tmp_path / "n" / "results.csv").open()))
    assert rows[0]["date_sast"] == "2026-11-20" and rows[0]["result"] == "FAIL"
    assert "TLS certificate" in rows[0]["check_live_failed"]
    assert json.loads((tmp_path / "n" / "2026-11-20.json").read_text())["result"] == "FAIL"


def test_gate_failure_refuses_publish_and_fails_the_night(tmp_path: Path):
    def build_bad(staging):
        r = _build_ok(staging)
        return {**r, "scans": {"pii": 1}, "scans_clean": False}
    run = FakeRun()
    rec = nightly.run_nightly(publish_flag=True, cfg={**CFG, "publish_enabled": True}, run=run, live=_live_pass,
                              refresh=lambda: None, build=build_bad, now=_now, log_commit=False,
                              nightly_dir=tmp_path / "n", staging=tmp_path / "s")
    assert rec["gate"] == "FAIL" and rec["publish"].startswith("refused") and rec["result"] == "FAIL"
    assert not run.pushed()


def test_dirty_tree_fails_preflight(tmp_path: Path):
    rec = nightly.run_nightly(cfg=CFG, run=FakeRun(dirty=True), live=_live_pass, refresh=lambda: None,
                              build=_build_ok, now=_now, log_commit=False, nightly_dir=tmp_path / "n",
                              staging=tmp_path / "s")
    assert rec["result"] == "FAIL" and rec["refresh"] == "not run"


def test_manual_run_recorded_separately(tmp_path: Path):
    rec = nightly.run_nightly(manual=True, cfg=CFG, run=FakeRun(), live=_live_pass, refresh=lambda: None,
                              build=_build_ok, now=_now, log_commit=False, nightly_dir=tmp_path / "n",
                              staging=tmp_path / "s")
    assert rec["trigger"] == "manual"
    assert (tmp_path / "n" / "2026-11-20-manual-041000.json").is_file()


# --- real git: publish fast-forward and the log branch ---------------------------

def _g(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_identity(repo: Path):
    _g("config", "user.name", "Test Author", cwd=repo)
    _g("config", "user.email", "test@example.invalid", cwd=repo)


def test_publish_fast_forwards_the_site_when_enabled(tmp_path: Path):
    origin = tmp_path / "GrokForum" / "tenderwatch-site.git"
    origin.parent.mkdir(parents=True)
    _g("init", "-q", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    seed = tmp_path / "seed"
    _g("clone", "-q", str(origin), str(seed), cwd=tmp_path)
    _init_identity(seed)
    (seed / "CNAME").write_text("tenderwatch.example\n")
    _g("add", "CNAME", cwd=seed)
    _g("commit", "-q", "-m", "init", cwd=seed)
    _g("push", "-q", "origin", "HEAD:main", cwd=seed)
    site_dir = tmp_path / "site"
    _g("clone", "-q", str(origin), str(site_dir), cwd=tmp_path)
    _init_identity(site_dir)
    staging = tmp_path / "staging"
    site.build_site(fixture_rows(), staging)
    cfg = {**CFG, "publish_enabled": True}
    status = nightly.publish_to_site(staging, site_dir, cfg, True, "2026-11-20")
    assert status.startswith("published")
    log = subprocess.run(["git", "log", "--oneline", "main"], cwd=origin, capture_output=True, text=True).stdout
    assert "data: nightly build 2026-11-20 (CHG-TW-007)" in log
    assert nightly.publish_to_site(staging, site_dir, cfg, True, "2026-11-21") == "unchanged"
    assert (site_dir / "CNAME").read_text() == "tenderwatch.example\n"  # never touched


def test_publish_refuses_a_foreign_origin(tmp_path: Path):
    origin = tmp_path / "Someone" / "other.git"
    origin.parent.mkdir(parents=True)
    _g("init", "-q", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    site_dir = tmp_path / "site"
    _g("clone", "-q", str(origin), str(site_dir), cwd=tmp_path)
    with pytest.raises(nightly.PublishRefused):
        nightly.publish_to_site(tmp_path, site_dir, {**CFG, "publish_enabled": True}, True, "2026-11-20")


def test_log_branch_gets_one_commit_per_night_and_is_not_pushed(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _g("init", "-q", "-b", "main", cwd=repo)
    _init_identity(repo)
    (repo / "a.txt").write_text("x")
    _g("add", "a.txt", cwd=repo)
    _g("commit", "-q", "-m", "init", cwd=repo)
    wt = repo / "data" / "local" / "nightly-log"
    base = {"trigger": "scheduled", "branch": "main", "result": "PASS", "started_sast": "2026-11-20T04:10:00+02:00"}
    assert nightly.commit_log({**base, "date_sast": "2026-11-20"}, CFG, root=repo, worktree=wt) == "committed (not pushed)"
    assert nightly.commit_log({**base, "date_sast": "2026-11-21", "result": "FAIL"}, CFG, root=repo, worktree=wt) == "committed (not pushed)"
    log = subprocess.run(["git", "log", "--format=%s", "ops/nightly-log"], cwd=repo, capture_output=True, text=True).stdout
    assert log.splitlines() == ["nightly 2026-11-21 scheduled: FAIL (CHG-TW-007)", "nightly 2026-11-20 scheduled: PASS (CHG-TW-007)"]
    rows = list(csv.DictReader((wt / "nightly" / "results.csv").open()))
    assert [r["result"] for r in rows] == ["PASS", "FAIL"]
    files = subprocess.run(["git", "ls-tree", "-r", "--name-only", "ops/nightly-log"], cwd=repo, capture_output=True, text=True).stdout.split()
    assert "a.txt" not in files  # orphan branch: the log only


# --- streak ---------------------------------------------------------------------

def _r(d, result="PASS", trigger="scheduled", branch="main"):
    return {"date_sast": d, "result": result, "trigger": trigger, "branch": branch}


def test_streak_counts_first_scheduled_run_on_main():
    rows = [_r(f"2026-11-{d:02d}") for d in range(20, 31)] + [_r(f"2026-12-0{d}") for d in range(1, 4)]
    s = nightly.streak(rows, "2026-12-03")
    assert s["streak"] == 14 and s["reaches_14"] and s["nights"][0] == "2026-11-20"


def test_streak_breaks_on_fail_gap_or_manual_fix():
    rows = [_r("2026-11-20"), _r("2026-11-21", "FAIL"), _r("2026-11-21", "PASS", trigger="manual"),
            _r("2026-11-22"), _r("2026-11-23")]
    assert nightly.streak(rows, "2026-11-23")["streak"] == 2
    assert nightly.streak([_r("2026-11-20"), _r("2026-11-22")], "2026-11-22")["streak"] == 1
    assert nightly.streak([_r("2026-11-22")], "2026-11-23")["streak"] == 1  # tonight not run yet
    assert nightly.streak([_r("2026-11-22", branch="dev/x")], "2026-11-22")["streak"] == 0
