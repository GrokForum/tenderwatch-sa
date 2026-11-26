# CHG-TW-015 — BAU item 7: non-hex boundary for the public SA-ID scan

| Field | Value |
|---|---|
| Change | CHG-TW-015 |
| Type | BAU code change in this repository only. |
| Environment | DEV: local tests. TEST: the test suite in a clean export. PROD: none in this change; the site repository is not touched. |
| Branch | `dev/BAU-7-sa-id-hex-boundary` from `main` at `f9ec88acc3491209a01e54446505b46457e83d4c`. |
| Rollback reference | `f9ec88acc3491209a01e54446505b46457e83d4c`. Revert the merge; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Project lead's direction of 25 Nov 2026 (owner GO relayed): BAU item 7, fix the flaky public SA-ID scan with a non-hex boundary, not by exempting hash fields. |
| Status | Squash-merged to `main` as [PR #23](https://github.com/GrokForum/tenderwatch-sa/pull/23) at `1f234a2455c254d7b3c43c551b758b5a85c86cd3`. |

## 1. Goal

Stop the public-file SA-ID scan from treating a 13-digit decimal run inside a hex token (for example a `sha256` in `manifest.json`) as an SA ID, which made `tests/test_national.py::test_synthetic_personal_national_rows_are_held_and_masked` fail when a content hash happened to contain such a run. Standalone 13-digit SA-ID shapes must still be flagged.

## 2. What changes (exact files)

* `tw/public_scan.py`: `SA_ID_RE` requires that a 13-digit run is not preceded or followed by a hex character `[0-9a-fA-F]`. A 13-digit run embedded in a sha256-like token is no longer a match. Hash fields are not exempted.
* `tests/test_site_build.py`: a sha256-like 64-character hex token with an embedded, clearly fake 13-digit run (middle, start, end, and uppercase) must not match, including when it appears in a `manifest.json`. The same fake digits must still match in prose, after `ID:`, in a CSV field, and in a JSON string. Digits are built at run time so the tree has no new 13-digit literal.
* This RFC. `STATUS.md` is not edited (feature PRs do not add STATUS rows; that is a later docs PR).

## 3. What stays

* `tw/normalise.py` keeps its digit-only-boundary `SA_ID_RE` (used to redact source data). Source IDs next to the letters A-F are still redacted.
* `publish_enabled` and `push_log` stay off; the site repository is not touched.
* Forward-only history: no rebase, no force push.

## 4. Success

* The full pytest suite passes: 397 passed, 3 skipped in the work tree.
* Mutation check: restoring the old digit-only boundary makes the new negative test fail; the positive standalone-ID test still passes.
* The formerly flaky national personal-row test passed on 15 extra reruns after the suite.

## 5. Rollback

Revert the merge of this branch into `main`. Pre-change commit: `f9ec88acc3491209a01e54446505b46457e83d4c`.

## 6. Seen, not touched

* A 13-digit run immediately adjacent to a letter A-F with no separator (for example `ID` written against the digits with no colon or space) is not flagged. The requested contexts with separators still match.
* `STATUS.md` is left for a later docs PR.

Result: SUCCEEDED in DEV and TEST (awaiting review).
