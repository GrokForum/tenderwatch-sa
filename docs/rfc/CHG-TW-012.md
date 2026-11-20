# CHG-TW-012 — GitHub Actions nightly: tests and a data-quality gate on synthetic fixtures

| Field | Value |
|---|---|
| Change | CHG-TW-012 |
| Type | CI workflow, data-quality gate, synthetic fixtures and tests in this repository only. |
| Environment | TEST: GitHub Actions on the private repository `GrokForum/tenderwatch-sa` (tests and the gate on committed synthetic fixtures) and the box (the gate on the real DEV build). No PROD: nothing is published, deployed or pushed by the workflow. |
| Branch | `dev/CHG-TW-012-actions-ci`, stacked on `dev/CHG-TW-009-fetch-errors` (the gate reports the fetch-error section CHG-TW-009 adds to the data-quality report). Base of the stack: `main` at `4f9dab45214c9621e46c5247b3725e6f4deb0647`. |
| Rollback reference | `4f9dab45214c9621e46c5247b3725e6f4deb0647` (and the CHG-TW-009 head below this change). Revert the merge, or disable the workflow in the repository settings; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Project lead's direction of 20 Nov 2026, 20:21 SAST (owner direction relayed): "add an Actions nightly with tests and a data-quality gate". |
| Status | DEV and TEST done on the box; the workflow runs on the draft PR. Merges only on the owner's GO naming the head. |

## 1. Goal

A light nightly check in GitHub Actions: the full test suite plus a data-quality gate, with no secrets and no personal data in CI, and no publish path.

## 2. Design: CI sees synthetic data only

The real build needs the git-ignored holds file (CHG-TW-008) and DEV data, which must never reach CI or a secret. So CI builds **committed synthetic fixtures** (`tests/fixtures/synthetic/`: 14 invented award rows, `ocds-synth-N` ids, and a 3-entry synthetic holds file marked SYNTHETIC) through the same `tw/site_build.py` code path, holds checks and public-file scans as the real build. **The real build and its gate stay on the box** (`python3 scripts/dq_gate.py`), where the data and holds file live.

## 3. What changes (exact files)

* `.github/workflows/ci.yml` (new): one job, `ubuntu-latest`, 10-minute timeout; triggers: pull requests, pushes to `main`, nightly at 01:30 UTC (03:30 SAST), manual. `permissions: contents: read` at workflow level; `actions/checkout` and `actions/setup-python` pinned to 40-hex commit SHAs (v7.0.1 and v7.1.0); `persist-credentials: false`; no secrets, no artifacts upload, no push, no `pull_request_target`; `concurrency` cancels superseded runs. Steps: install pytest 9.2.0, run the tests, run the gate on the fixtures.
* `tw/dq.py`: `check_site()` and `gate()`. Checks: build OK; every public-file scan has 0 findings (withheld and held names, all names except shown, PII shapes, paths and bot names, wording); row count within bounds; groups add up to the total (and equal the expected groups for fixtures); manifest keys and `DRAFT` status; CSV header equal to a frozen copy of the schema, every CSV row the right width, CSV rows = total minus withheld; every masked row has the fixed mask and no tender reference, OCDS id or year digit; no mask-shaped name outside a masked row; every page has `noindex, nofollow` and the DRAFT marker; `robots.txt` disallows all. The source fetch-error summary from CHG-TW-009 is reported as `WARN` (a source being down does not fail the gate, but it is never silent). `synthetic_inputs()` points the build at the fixtures and restores the module afterwards.
* `scripts/dq_gate.py` (new): `--fixtures` (CI) or the real DEV build (box; writes the `gate` section into `data/local/warehouse/dq-report.json`, git-ignored). Exit 0 PASS or WARN, 1 FAIL, 2 error. Prints counts and check names only.
* `config/dq.json` (new): bounds (DEV 291 rows; fixtures 14 rows and expected groups).
* `tests/fixtures/synthetic/classified.jsonl`, `tests/fixtures/synthetic/popia_holds.synthetic.json` (new, invented).
* `tests/test_dq_gate.py` (new, 10 tests): the fixture build passes; the gate fails on an unmasked held name, a scan finding, out-of-bounds rows, a schema change, a missing noindex or an open robots.txt; fetch errors warn; a missing fixture holds file stops the build; the workflow is read-only, pinned, and publishes nothing.
* This RFC and one `STATUS.md` row.

## 4. What stays

* The box nightly (CHG-TW-007), its publish guards and `publish_enabled` / `push_log` (`false`). The site repository is not touched.
* The real holds file and DEV data never leave the box.

## 5. Results (DEV and TEST)

* Tests: 330 collected (320 + 10). In this checkout with the DEV data: 330 passed. In a fresh virtual environment from a clean export: 327 passed, 3 skipped. In GitHub Actions (a git checkout without DEV data) only the DEV-data tests skip.
* Gate, fixtures: PASS (19 checks), 14 rows, groups 6 / 3 / 2 / 2 / 1.
* Gate, real DEV build on the box: PASS, 291 rows, `content_sha256` `c1d2e3d9e0109920f814ba84009918e75b7ee24a49fee44bd4dd5872cd8d05c6` (unchanged).
* Actions minutes: one job of about one minute per run (nightly, plus pull requests and pushes to `main`).

## 6. Rollback

Revert the merge of this change on `main` (`git revert -m 1 <merge>`), or disable the workflow; nothing depends on it.

## 7. Seen, not touched

* The box nightly could also run `scripts/dq_gate.py` after its build; left for a later change so CHG-TW-007's record format stays as reviewed.

Result: SUCCEEDED in DEV and TEST (awaiting review and the first Actions run).
