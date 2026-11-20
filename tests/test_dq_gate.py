"""CHG-TW-012: the data-quality gate on the committed synthetic fixtures (what CI runs)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tw import dq, site_build
from tw.fetch_log import FetchLog

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests" / "fixtures" / "synthetic"
CFG = json.loads((ROOT / "config" / "dq.json").read_text(encoding="utf-8"))["fixtures"]
N = CFG["rows"][1]


@pytest.fixture()
def built(tmp_path):
    out = tmp_path / "site"
    with dq.synthetic_inputs(FX, rows_expected=N) as sb:
        result = sb.run_build(out)
    return result, out


def _gate(result, out, **kw):
    return dq.gate(result, out, bounds=tuple(CFG["rows"]), groups=CFG["groups"], **kw)


def test_fixture_build_passes_the_gate(built):
    result, out = built
    rep = _gate(result, out)
    assert rep["status"] == dq.PASS, [c for c in rep["checks"] if c["status"] != dq.PASS]
    assert result["holds_applied"] == 3


def test_synthetic_inputs_restore_the_real_paths():
    before = (site_build.CLASSIFIED, site_build.HOLDS, site_build.EXPECTED_ROWS)
    with dq.synthetic_inputs(FX, rows_expected=N):
        assert site_build.HOLDS == FX / "popia_holds.synthetic.json"
    assert (site_build.CLASSIFIED, site_build.HOLDS, site_build.EXPECTED_ROWS) == before


def test_gate_fails_on_an_unmasked_held_name(built):
    result, out = built
    csv_path = out / "register.csv"
    text = csv_path.read_text(encoding="utf-8")
    masked = next(line for line in text.splitlines() if "Masked row (POPIA)" in line)
    cells = masked.split(",")
    cells[4] = "Testcorp Logistics (Pty) Ltd"  # a held fixture name written over its mask
    csv_path.write_text(text.replace(masked, ",".join(cells)), encoding="utf-8")
    rep = _gate(result, out)
    failed = {c["check"] for c in rep["checks"] if c["status"] == dq.FAIL}
    assert rep["status"] == dq.FAIL and "masked_rows_masked" in failed


def test_gate_fails_on_scan_findings_bounds_and_schema(built):
    result, out = built
    bad = dict(result, scans=dict(result["scans"], names_withheld=1))
    assert _gate(bad, out)["status"] == dq.FAIL
    assert dq.gate(result, out, bounds=(N + 1, N + 5))["status"] == dq.FAIL
    p = out / "register.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("right_of_reply,sources", "right_of_reply,src", 1), encoding="utf-8")
    assert {c["check"] for c in _gate(result, out)["checks"] if c["status"] == dq.FAIL} >= {"csv_schema"}


def test_gate_fails_without_noindex_or_robots(built):
    result, out = built
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    page = out / "404.html"
    page.write_text(page.read_text(encoding="utf-8").replace("noindex, nofollow", "index"), encoding="utf-8")
    failed = {c["check"] for c in _gate(result, out)["checks"] if c["status"] == dq.FAIL}
    assert {"robots_disallow_all", "pages_noindex_and_draft"} <= failed


def test_fetch_errors_warn_but_do_not_fail(built):
    result, out = built
    log = FetchLog("src", now=lambda: "T")
    log.error("https://x.example/", ConnectionError("TLS certificate verification failed"))
    rep = _gate(result, out, fetch=dq.fetch_section(log))
    assert rep["status"] == dq.WARN
    c = next(c for c in rep["checks"] if c["check"] == "source_fetch_errors")
    assert c["status"] == dq.WARN and "tls_certificate" in c["detail"]


def test_build_stops_when_the_fixture_holds_file_is_missing(tmp_path):
    fx = tmp_path / "fx"
    shutil.copytree(FX, fx)
    (fx / "popia_holds.synthetic.json").unlink()
    with dq.synthetic_inputs(fx, rows_expected=N) as sb, pytest.raises(Exception, match="holds file missing"):
        sb.run_build(tmp_path / "out")


def test_dq_gate_script_fixtures_mode(tmp_path):
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "dq_gate.py"), "--fixtures", "--out", str(tmp_path / "o")],
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    assert json.loads(p.stdout)["status"] == "PASS"


def test_fixtures_are_synthetic_and_not_the_real_holds_file():
    holds = json.loads((FX / "popia_holds.synthetic.json").read_text(encoding="utf-8"))
    assert "SYNTHETIC" in holds["note"]
    assert all(h["ocid"].startswith("ocds-synth-") for h in holds["holds"])
    rows = [json.loads(line) for line in (FX / "classified.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == N and all(r["ocid"].startswith("ocds-synth-") for r in rows)


WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_workflow_is_read_only_pinned_and_publishes_nothing():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text
    for line in text.splitlines():
        if "uses:" in line:
            ref = line.split("@", 1)[1].split()[0]
            assert len(ref) == 40 and all(ch in "0123456789abcdef" for ch in ref), line
    for word in ("secrets.", "pull_request_target", "git push", "upload-artifact", "publish_enabled", "--publish",
                 "write-all", "popia_holds.json"):
        assert word not in text, word
    assert "--fixtures" in text
