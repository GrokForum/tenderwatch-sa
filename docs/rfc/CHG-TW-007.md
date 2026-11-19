# CHG-TW-007 — Nightly build, gated publish and live check, with a dated PASS/FAIL record per night

| Field | Value |
|---|---|
| Change | CHG-TW-007 |
| Type | Build and operations change in this repository (nightly runner, live check, results log, tests, config). Phase 0 ask (1). |
| Environment | DEV and TEST on the box (dry-run). PROD = the nightly routine on the box, created by the owner after GO. The publish step is **off** (two locks, §5) until a later owner GO. |
| Branch | `dev/CHG-TW-007-nightly-live-check`, **stacked on** `dev/CHG-TW-006-draft-register` (it runs CHG-TW-006's site build), which is on `origin/main` at `05a0a9577bb16de13669997f7ee7a8248e194a30`. Local commits; not pushed. After CHG-TW-006 is squash-merged this branch is rebased onto the new `main`, keeping every STATUS row. |
| Rollback reference | `05a0a9577bb16de13669997f7ee7a8248e194a30` (pre-change `main`); or, once CHG-TW-006 is merged, that merge commit. |
| Author | the author (TenderWatch) |
| Reviewers | the project lead and the critic |
| Basis | Phase 0 audit of 19 Nov 2026 (finding B2; TenderWatch row 5; streak table: 0 nights, no job; H4 for the per-night evidence lesson from PublicFunds), relayed by the project lead under the owner's rule that all four test sites must be rock-solid. Pattern: PublicFunds `scripts/check_live.py` and `scripts/nightly_check_live.py` (CHG-2026-061), read-only. |
| Status | Draft for CAB on its own pull request. Not pushed, not merged; no routine exists yet. |

## 1. Goal

A nightly job that rebuilds the DRAFT register, gates it with every public-file scan, can publish it (only after the owner's GO), checks the live site, and saves one dated PASS or FAIL per night in a durable log, so that a 14-night green streak can be counted for Phase 0.

## 2. Where the job runs: a box routine, not GitHub Actions

* The build reads git-ignored DEV inputs on the box (the CHG-TW-001/002 warehouse under `data/local/` and the pinned eTenders OCDS file held by the PublicFunds checkout on the box). Neither is in any repository, and committing them would put per-name data in git, against CHG-TW-002. A GitHub Actions schedule cannot see them.
* PublicFunds runs its nightly the same way (a box routine, about 03:20 SAST).
* Routines can only be created by the owner. The exact prompt and schedule are in §7, for the owner to create after GO.

## 3. What changes (exact files)

* New `tw/check_live.py`: read-only live check (§4.2).
* New `tw/nightly.py`: the nightly steps, the publish locks, the results log and the streak rule.
* New `scripts/nightly.py` (the routine runs this) and `scripts/nightly_streak.py` (read-only streak count).
* New `config/nightly.json`: `site_url` https://tenderwatch.grokforum.site, `site_repo` GrokForum/tenderwatch-site, `publish_enabled: false`, `push_log: false`, `log_branch: ops/nightly-log`, `pages_wait_seconds: 600`.
* New `tests/test_nightly.py`: 27 tests (a local HTTP server for the live check; a fake git runner for the locks; real temporary git repositories for the fast-forward publish and the log branch; the streak rule).
* This RFC and one `STATUS.md` row.

## 3a. What stays

* Pages settings, the custom domain and HTTPS: not touched (audit B1 waits for the owner's GO).
* The public site is not changed by this record. With the committed config the nightly cannot copy, commit or push anything to the site (§5).
* The DEV pipeline code is unchanged. The nightly calls the CHG-TW-002 classification with its run report redirected to `data/local/nightly/`, so `docs/dev/` and every other tracked file stay unchanged (checked every night, step 4).
* The OCDS input stays the pinned file of 19 Oct 2026. Fetching newer eTenders data is a later change; until then the nightly rebuild is byte-identical night to night, which is itself checked (the live site must serve tonight's `content_sha256`).

## 4. The nightly

### 4.1 Steps (each recorded)

1. **preflight**: repository head and branch; tracked files clean.
2. **refresh**: re-run the CHG-TW-002 classification from the pinned DEV inputs (local files only, no network).
3. **build and gate**: CHG-TW-006 build into `data/local/site-build/`, then the 198- and 718-name scans, the PII scan, the path and bot-name scan and the wording grep; the gate passes only with 0 findings and all rows accounted for.
4. **tracked**: no tracked file changed during the run.
5. **publish**: see §5. With the committed config this is always `dry-run (publish not enabled)`.
6. **check_live** (always runs, even after a failed build, so the live state is recorded): HTTPS with certificate verification; `/`, `/method/` and `/privacy/` return 200 with the DRAFT banner, the noindex meta and a privacy link; a missing path returns 404 with the same three; `robots.txt` is exactly `User-agent: *` / `Disallow: /`; the privacy page names GrokForum, the role address and the Information Regulator; `/manifest.json` has status DRAFT and tonight's `content_sha256`; every file the live manifest lists is served with its sha256. After a real publish it re-checks every 30 s for up to 600 s while Pages deploys.
7. **record** (§6).

### 4.2 PASS rule

A night is **PASS** only if every step passed **and** the live site serves tonight's build (every live check PASS). Anything else is **FAIL**, recorded as FAIL with the failed checks. Only the **first scheduled run on `main`** per date counts for the streak; a manual re-run (`--manual`) is recorded with trigger `manual` and never repairs a night (the audit counted PublicFunds' off-schedule re-run of 13 Nov as a manual fix). A missing date ends the streak. `scripts/nightly_streak.py` counts it.

## 5. Publish locks (the nightly cannot push to the public site before the owner's GO)

1. **Committed config**: `config/nightly.json` has `"publish_enabled": false`. Changing it needs a reviewed change merged on the owner's GO on its exact head.
2. **Command line**: publishing also needs `--publish`. The routine prompt in §7 never passes it.
3. **Gate**: even with both locks open, a failed scan, a count mismatch, a dirty tree or any earlier failure refuses the publish.
4. **Target**: the site checkout's `origin` must be exactly `https://github.com/GrokForum/tenderwatch-site` (or its `git@github.com:` form, optional `.git`), with no suffix matching, so a look-alike host or path is refused; the push URL (`git remote get-url --push origin`) must match the same way, and the push goes to that verified URL; the site checkout's `main` must have no commits beyond `origin/main` (`origin/main..main` empty); any publish, manual runs included, needs the private repository on `main`; the site checkout is the nightly's own clean clone `tenderwatch-site-nightly` (`site_checkout` in `config/nightly.json`), never the development site checkout; the push is a plain fast-forward of `main` (`git push origin main`, never `--force`); `CNAME` and `README.md` are never touched; only the managed files are copied. Each publish commit carries the neutral role identity `TenderWatch publisher <noreply@grokforum.site>` as author and committer, never the box's git identity (project lead's answer to CHG-TW-006 Q2, 19 Nov 2026, relayed).

Tests pin all four: with `publish_enabled` false and `--publish` given, no git command reaches the site and no push is attempted; a gate failure with both locks open refuses; a foreign origin refuses; an enabled publish fast-forwards a temporary bare repository and a second identical build reports `unchanged`; the publish commit's author and committer are the role identity.

## 6. The results log (durable and dated)

* Every run appends one line to `results.csv` (date in SAST, start and finish, trigger, branch, repository head, each step, the live-check result and failed checks, `content_sha256`, PASS or FAIL) and writes `YYYY-MM-DD.json` with the full detail (counts, scan totals, every live check). Counts and check results only; no names.
* Written twice: `data/local/nightly/` (git-ignored, on the box) and the orphan branch `ops/nightly-log` of this repository (a git worktree at `data/local/nightly-log/`), one commit per night, so the history cannot be rewritten silently.
* The log branch is pushed to the private origin only when `push_log` is true (owner GO; recommended, so the log survives loss of the box).

## 7. Routine for the owner to create after GO

**Schedule:** every day at 04:10 Africa/Johannesburg (SAST), after the PublicFunds nightly (about 03:20).

**Prompt (dry-run; publish stays off):**

> TenderWatch nightly (CHG-TW-007). Work only in the dedicated nightly checkout of the private repository GrokForum/tenderwatch-sa (the clean clone of `main` named `tenderwatch-sa-nightly`), never in the development checkout.
> 1. Run `git fetch origin`, `git checkout main`, `git merge --ff-only origin/main`. If any of these fails, report `ACTION: checkout update failed` and stop.
> 2. Run `python3 scripts/nightly.py` with no arguments (never add `--publish` or `--manual`). Allow up to 20 minutes.
> 3. Report every line it prints (RESULT, each step, the failed live checks, the scan totals, where the record was written). Then run `python3 scripts/nightly_streak.py` and report the streak.
> 4. If RESULT is FAIL, begin the report with `ACTION: nightly FAIL` and the failed steps. If the run crashed (exit code 2), report `ACTION: nightly crashed` and stop.
> 5. Report a FAIL as a FAIL, never as success. Do not re-run, fix, edit, commit, push, publish or merge anything, and do not touch GitHub Pages settings or the custom domain.

**One-time setup before the routine is created (after GO):** clone `GrokForum/tenderwatch-sa` into its own directory `tenderwatch-sa-nightly`, beside the development checkout, and stay on `main`. Also clone `GrokForum/tenderwatch-site` into its own directory `tenderwatch-site-nightly` beside it, on `main`, with no other remotes, no `pushurl` override and no local commits; nothing else uses that clone. Seed the private clone's git-ignored `data/local/` once with the DEV inputs only (`raw/`, `check_queue.csv`, `confirmed_suppliers.csv`, `public_scan_extra_terms.txt`, and `popia_holds.json` from CHG-TW-008, without which the build stops), copied from the development checkout; outputs (`export/`, `warehouse/`, `site-build/`, `nightly/`) are regenerated. The nightly never reads or writes the development checkout. A scheduled run that is not on `main` fails preflight (`a scheduled run must be on main in the nightly checkout`); only manual runs may run on a branch, and they never count.

**After a later GO to publish** (a reviewed change sets `publish_enabled: true`): step 2 becomes `python3 scripts/nightly.py --publish`, and the report adds the publish line (`published <sha>` or `unchanged`).

## 8. How success is proven

| Check | Result (19 Nov 2026) |
|---|---|
| Fresh venv (Python 3.13, `pip install -e ".[test]"`): existing suite + CHG-TW-006 + new | 272 passed (215 + 30 + 27) on the head with the critic's review points |
| Real dry run on the box (manual trigger, this branch at the CHG-TW-006 code `6fb5fcd1`; log commit off for the trial) | refresh PASS, build PASS, gate PASS (every scan 0), tracked files clean, publish `dry-run (publish not enabled)`, `content_sha256` `55d6b6f5f254d6cb8a1c749d3623aac605daf588bb3db9a07f2154aefe1cd070` (identical to the CHG-TW-006 build after the classification re-run), **check_live FAIL: TLS certificate verification failed** (audit B1). Result **FAIL**, correctly recorded in `data/local/nightly/results.csv` and `2026-11-19-manual-080211.json`. |
| Live check against the placeholder with verification off (information only, not a nightly mode) | home 200 and robots PASS; DRAFT, noindex-form, privacy page, `/method/`, 404 page and manifest FAIL, as expected before CHG-TW-006 is deployed |

### Critic's review points (19 Nov 2026, relayed by the project lead)

* The dry-run `content_sha256` above is written in full; it is the build of the CHG-TW-006 code at `6fb5fcd1`. The later CHG-TW-006 privacy-page wording changes the site content hash; the dry run is not re-claimed for it.
* The publish target check is an exact match on the GitHub repository (`origin_matches`), not a suffix match; a test pins accepted and refused forms.
* The routine runs in its own clean checkout of `main` (§7 setup); a scheduled run on any other branch fails preflight, and a test pins it.
* Project lead's points on the next head: the push URL is verified and pushed to exactly; `origin/main..main` must be empty in the site checkout; any publish needs `main`, manual runs included; the site checkout is a dedicated clean clone (§7 setup). Tests pin each (a differing push URL, a stray local commit, a manual publish off `main`, the default site checkout).

## 9. When the streak can start

The first green night needs all of: the HTTPS fix (owner GO, audit B1), the CHG-TW-006 site on `main` of the site repository (owner GO on its exact head), this change merged, and the routine created. Day 14 is 13 days after the first green night; the earliest is 3 Dec 2026 only if everything is live and green from 20 Nov.

## 10. Seen, not touched

* Audit B1 (HTTPS on the custom domain): owner GO.
* Freshness of the eTenders input (pinned 19 Oct 2026): a later change, with its own source refresh and DQ checks.
* Alerting beyond the routine's report (for example a message on FAIL): not added.
* PublicFunds' review-app health check and backup steps have no TenderWatch counterpart; not added.

## 11. Rollback

Git: drop the branch, or after a squash merge `git revert <merge commit>` through the same review and GO path. Operationally: the owner pauses or deletes the routine; the log branch is kept as evidence. With publish off, no site rollback is ever needed for this change.

## 12. Owner-GO gate

* Merge: the standing GO (both reviewers give a plain PASS on the same head); it deploys nothing.
* Creating the routine: the owner (§7).
* Pushing the `ops/nightly-log` branch (`push_log: true`): owner GO.
* Turning publishing on (`publish_enabled: true` plus `--publish` in the routine): owner GO on the exact head of that change. Every nightly publish after that pushes to the public site repository under that GO; whether that GO is a standing one for nightly data publishes (like PublicFunds' data-refresh exemption) is an owner question (Q1).

## 13. Open questions

1. When publishing is turned on, is the owner's GO a standing GO for nightly publishes of the same build code (only data and build output change), or a GO per head?
2. Push the log branch to the private origin (recommended), or keep it on the box only?
3. 04:10 SAST, or another time?

---
*POPIA check: PASS. No supplier or personal names; the log holds counts and check results only; test names invented.*
