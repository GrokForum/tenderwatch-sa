"""CHG-TW-007: nightly build, gated publish and live check, with one dated PASS/FAIL record per night.

Steps (each one is recorded):
  1. preflight   repository head, branch, tracked files clean
  2. refresh     re-run the CHG-TW-002 classification from the pinned DEV inputs (local files only)
  3. build       build the DRAFT site into data/local/site-build/ and run every public-file scan (the gate)
  4. tracked     no tracked file changed (the run report goes to data/local/nightly/, not docs/dev/)
  5. publish     only if config/nightly.json has "publish_enabled": true AND the run was given --publish AND the
                 gate passed: copy the managed files into the site checkout, commit, fast-forward push to main
                 (never force). Otherwise "dry-run": nothing is copied, committed or pushed.
  6. check_live  read-only check of the live site against tonight's build (tw/check_live.py)
  7. record      append one line to results.csv and write YYYY-MM-DD.json, under data/local/nightly/ and on the
                 log branch (a git worktree at data/local/nightly-log/); the log branch is pushed to the private
                 origin only if "push_log": true

A night is PASS only if every step passed and the live site serves tonight's build. Only a scheduled run on
main counts for the streak; a manual run is recorded with trigger "manual".
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from tw import check_live as cl

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "nightly.json"
NIGHTLY_DIR = ROOT / "data" / "local" / "nightly"
LOG_WORKTREE = ROOT / "data" / "local" / "nightly-log"
STAGING = ROOT / "data" / "local" / "site-build"
SAST = timezone(timedelta(hours=2), "SAST")
CSV_FIELDS = ["date_sast", "started_sast", "finished_sast", "trigger", "branch", "repo_head", "refresh", "build",
              "gate", "tracked_clean", "publish", "check_live", "check_live_failed", "content_sha256", "result"]
SITE_KEEP = {"CNAME", "README.md", ".git"}

Runner = Callable[..., subprocess.CompletedProcess]


class PublishRefused(RuntimeError):
    pass


def load_config(path: Path = CONFIG) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("site_url", "site_repo", "publish_enabled", "push_log", "log_branch"):
        if key not in cfg:
            raise ValueError(f"config/nightly.json lacks {key}")
    if not isinstance(cfg["publish_enabled"], bool) or not isinstance(cfg["push_log"], bool):
        raise ValueError("publish_enabled and push_log must be true or false")
    return cfg


PUBLISHER_NAME = "TenderWatch publisher"
PUBLISHER_EMAIL = "noreply@grokforum.site"


def _git(args: list[str], cwd: Path, run: Runner = subprocess.run, check: bool = True) -> str:
    p = run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed ({p.returncode})")
    return (p.stdout or "").strip()


def default_site_dir(cfg: dict, root: Path = ROOT) -> Path:
    """The nightly's own clean clone of the site repository, beside this checkout; never the development site checkout."""
    return root.parent / cfg.get("site_checkout", "tenderwatch-site-nightly")


def publish_allowed(cfg: dict, publish_flag: bool) -> bool:
    """Both locks must be open: the committed config flag and the --publish argument."""
    return cfg.get("publish_enabled") is True and publish_flag is True


def origin_matches(remote: str, site_repo: str, allowed_remotes: set[str] | None = None) -> bool:
    """Exact match on the GitHub repository (https or ssh form), with an optional trailing .git or /.
    No suffix matching: a look-alike host or owner path is refused. Tests pass allowed_remotes for a local bare repo."""
    norm = remote.strip().rstrip("/").removesuffix(".git")
    allowed = allowed_remotes if allowed_remotes is not None else {
        f"https://github.com/{site_repo}", f"git@github.com:{site_repo}", f"ssh://git@github.com/{site_repo}"}
    return norm in {a.rstrip("/").removesuffix(".git") for a in allowed}


def publish_to_site(staging: Path, site_dir: Path, cfg: dict, publish_flag: bool, date_sast: str,
                    run: Runner = subprocess.run, allowed_remotes: set[str] | None = None) -> str:
    """Copy the managed files into the site checkout, commit and fast-forward push main. Returns a status text."""
    if not publish_allowed(cfg, publish_flag):
        raise PublishRefused("publish is not enabled (config publish_enabled and --publish are both required)")
    remote = _git(["remote", "get-url", "origin"], site_dir, run)
    if not origin_matches(remote, cfg["site_repo"], allowed_remotes):
        raise PublishRefused("site checkout origin is not the configured site repository")
    # The push URL can differ from the fetch URL (remote.origin.pushurl): verify it too, then push to that exact URL.
    push_url = _git(["remote", "get-url", "--push", "origin"], site_dir, run)
    if not origin_matches(push_url, cfg["site_repo"], allowed_remotes):
        raise PublishRefused("site checkout push URL is not the configured site repository")
    _git(["fetch", "origin", "main"], site_dir, run)
    _git(["checkout", "main"], site_dir, run)
    _git(["merge", "--ff-only", "origin/main"], site_dir, run)
    if _git(["status", "--porcelain"], site_dir, run):
        raise PublishRefused("site checkout has local changes")
    if _git(["rev-list", "origin/main..main"], site_dir, run):
        raise PublishRefused("site checkout main has commits not on origin/main")
    from tw.site import MANAGED_FILES
    for rel in MANAGED_FILES:
        dst = site_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staging / rel, dst)
    _git(["add", "--", *MANAGED_FILES], site_dir, run)
    if not _git(["status", "--porcelain"], site_dir, run):
        return "unchanged"
    # Public commits carry the neutral role identity only, never the box's git identity (no bot or personal name).
    _git(["-c", f"user.name={PUBLISHER_NAME}", "-c", f"user.email={PUBLISHER_EMAIL}",
          "commit", "-q", f"--author={PUBLISHER_NAME} <{PUBLISHER_EMAIL}>",
          "-m", f"data: nightly build {date_sast} (CHG-TW-007)"], site_dir, run)
    sha = _git(["rev-parse", "HEAD"], site_dir, run)
    _git(["push", push_url, "main:main"], site_dir, run)  # the verified URL; fast-forward only: no --force, ever
    return f"published {sha[:12]}"


def ensure_log_worktree(branch: str, run: Runner = subprocess.run, root: Path = ROOT,
                        worktree: Path = LOG_WORKTREE) -> Path:
    if (worktree / ".git").exists():
        return worktree
    exists = run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root,
                 capture_output=True, text=True).returncode == 0
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if exists:
        _git(["worktree", "add", str(worktree), branch], root, run)
    else:
        _git(["worktree", "add", "--detach", str(worktree)], root, run)
        _git(["checkout", "-q", "--orphan", branch], worktree, run)
        _git(["rm", "-rq", "--cached", "."], worktree, run, check=False)
        for p in worktree.iterdir():
            if p.name != ".git":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        (worktree / "README.md").write_text(
            "# TenderWatch nightly log (CHG-TW-007)\n\nOne line per night in `nightly/results.csv` and one JSON "
            "file per night. Counts and check results only; no names.\n", encoding="utf-8")
    return worktree


def write_record(rec: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "results.csv"
    new = not csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow({k: rec.get(k, "") for k in CSV_FIELDS})
    suffix = "" if rec["trigger"] == "scheduled" else "-manual-" + rec["started_sast"][11:19].replace(":", "")
    (directory / f"{rec['date_sast']}{suffix}.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n",
                                                                encoding="utf-8")


def commit_log(rec: dict, cfg: dict, run: Runner = subprocess.run, root: Path = ROOT,
               worktree: Path = LOG_WORKTREE) -> str:
    wt = ensure_log_worktree(cfg["log_branch"], run, root, worktree)
    write_record(rec, wt / "nightly")
    _git(["add", "-A"], wt, run)
    _git(["commit", "-q", "-m", f"nightly {rec['date_sast']} {rec['trigger']}: {rec['result']} (CHG-TW-007)"], wt, run)
    if cfg.get("push_log") is True:
        _git(["push", "origin", cfg["log_branch"]], wt, run)
        return "committed and pushed"
    return "committed (not pushed)"


def run_nightly(*, publish_flag: bool = False, manual: bool = False, site_dir: Path | None = None,
                cfg: dict | None = None, run: Runner = subprocess.run, live: Callable = cl.check_live,
                refresh: Callable | None = None, build: Callable | None = None, now: Callable = None,
                log_commit: bool = True, nightly_dir: Path = NIGHTLY_DIR, staging: Path = STAGING,
                sleep: Callable = time.sleep) -> dict:
    now = now or (lambda: datetime.now(SAST))
    cfg = cfg or load_config()
    started = now()
    rec: dict = {"date_sast": started.strftime("%Y-%m-%d"), "started_sast": started.isoformat(timespec="seconds"),
                 "trigger": "manual" if manual else "scheduled", "refresh": "not run", "build": "not run",
                 "gate": "not run", "tracked_clean": "not run", "publish": "not run", "check_live": "not run",
                 "check_live_failed": "", "content_sha256": "", "steps": {}}
    ok = True
    try:
        rec["repo_head"] = _git(["rev-parse", "HEAD"], ROOT, run)
        rec["branch"] = _git(["rev-parse", "--abbrev-ref", "HEAD"], ROOT, run)
        if _git(["status", "--porcelain", "--untracked-files=no"], ROOT, run):
            raise RuntimeError("tracked files have local changes before the run")
        if not manual and rec["branch"] != "main":
            # The routine runs in its own clean checkout of main, never in a development worktree.
            raise RuntimeError("a scheduled run must be on main in the nightly checkout")
    except Exception as e:  # noqa: BLE001
        rec["steps"]["preflight"] = f"FAIL: {e}"
        ok = False
    manifest = None
    if ok:
        try:
            if refresh is None:
                from tw.classification_report import run as classify
                from tw.config import load_config as load_dev, ocds_input_path
                try:
                    ocds = ocds_input_path(load_dev())
                except FileNotFoundError:
                    ocds = None
                nightly_dir.mkdir(parents=True, exist_ok=True)
                classify(report_path=nightly_dir / "classification-report.md", ocds_path=ocds)
            else:
                refresh()
            rec["refresh"] = "PASS"
        except Exception as e:  # noqa: BLE001
            rec["refresh"] = f"FAIL: {type(e).__name__}"
            ok = False
    if ok:
        try:
            if build is None:
                from tw.site_build import run_build
                result = run_build(staging)
            else:
                result = build(staging)
            rec["build"] = "PASS"
            rec["content_sha256"] = result["content_sha256"]
            rec["steps"]["counts"] = {"rows_total": result["rows_total"], "group_counts": result["group_counts"],
                                      "year_counts": result["year_counts"]}
            rec["steps"]["scans"] = result["scans"]
            rec["gate"] = "PASS" if result["scans_clean"] and result["rows_total"] == sum(result["group_counts"].values()) else "FAIL"
            manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
            ok = rec["gate"] == "PASS"
        except Exception as e:  # noqa: BLE001
            rec["build"] = f"FAIL: {type(e).__name__}"
            ok = False
    try:
        rec["tracked_clean"] = "PASS" if not _git(["status", "--porcelain", "--untracked-files=no"], ROOT, run) else "FAIL"
    except Exception:  # noqa: BLE001
        rec["tracked_clean"] = "FAIL"
    ok = ok and rec["tracked_clean"] == "PASS"
    if not publish_allowed(cfg, publish_flag):
        rec["publish"] = "dry-run (publish not enabled)"
    elif not ok:
        rec["publish"] = "refused (an earlier step failed)"
    elif rec.get("branch") != "main":
        # Any publish, manual runs included, needs the private repository's main.
        rec["publish"] = "refused (not on main)"
        ok = False
    else:
        try:
            rec["publish"] = publish_to_site(staging, site_dir or default_site_dir(cfg), cfg,
                                             publish_flag, rec["date_sast"], run)
        except Exception as e:  # noqa: BLE001
            rec["publish"] = f"FAIL: {e}"
            ok = False
    # Live check: always run, so a night with a broken build still records the state of the live site.
    results = live(cfg["site_url"], expected=manifest)
    if rec["publish"].startswith("published"):
        deadline = time.monotonic() + float(cfg.get("pages_wait_seconds", 600))
        while cl.overall(results) != cl.PASS and time.monotonic() < deadline:
            sleep(30)
            results = live(cfg["site_url"], expected=manifest)
    rec["check_live"] = cl.overall(results)
    rec["check_live_failed"] = ";".join(f"{c}: {d}" for c, s, d in results if s != cl.PASS)
    rec["steps"]["check_live"] = [list(r) for r in results]
    ok = ok and rec["check_live"] == cl.PASS and manifest is not None
    rec["result"] = "PASS" if ok else "FAIL"
    rec["finished_sast"] = now().isoformat(timespec="seconds")
    write_record(rec, nightly_dir)
    if log_commit:
        try:
            rec["log"] = commit_log(rec, cfg, run)
        except Exception as e:  # noqa: BLE001
            rec["log"] = f"FAIL: {e}"
    return rec


def streak(rows: list[dict], today: str) -> dict:
    """Green nights in a row, ending today or yesterday (a night not run yet today does not break it).

    Only the first scheduled run on main per date counts; a missing date, or a FAIL, ends the streak.
    """
    first: dict[str, dict] = {}
    for r in rows:
        if r.get("trigger") == "scheduled" and r.get("branch") == "main" and r["date_sast"] not in first:
            first[r["date_sast"]] = r
    day = datetime.strptime(today, "%Y-%m-%d").date()
    if today not in first:
        day -= timedelta(days=1)
    n, nights = 0, []
    while True:
        r = first.get(day.isoformat())
        if not r or r.get("result") != "PASS":
            break
        n += 1
        nights.append(day.isoformat())
        day -= timedelta(days=1)
    return {"streak": n, "nights": sorted(nights), "reaches_14": n >= 14}
