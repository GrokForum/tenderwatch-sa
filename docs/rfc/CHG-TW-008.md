# CHG-TW-008 — Tracked POPIA holds: mask three Confirmed firms whose names are personal names

| Field | Value |
|---|---|
| Change | CHG-TW-008 |
| Type | Build change (site build input, tests) in this repository, plus the regenerated static files on the public site repository. |
| Environment | DEV: local build into `data/local/site-build/` (git-ignored). TEST: tests and the public-file scans. PROD: GitHub Pages from `main` of `GrokForum/tenderwatch-site`. **Nothing is deployed under this record without the owner's GO.** |
| Branches | Private repo: `dev/CHG-TW-008-tracked-holds` from `origin/main` at `df7c55d2` (PR #10). Public site repo: `dev/CHG-TW-008-masked-register` from `origin/main` at `33b794117075caa383a58a136b4d2cae99c1e92d` (after the owner-approved history rewrite). |
| Rollback reference | Revert the merge (see §5). Pre-change states for reference: private repo `5c7c09c2` (`main` after PR #11), public site repo `33b794117075caa383a58a136b4d2cae99c1e92d`. |
| Author | the author (TenderWatch) |
| Reviewers | the project lead and the critic |
| Basis | Owner decision of 19 Nov 2026, relayed by the project lead: the public site can publish only after the three Confirmed firms whose names are personal names are masked the same way as the other masked rows. |
| Status | Draft for CAB. Not merged, not deployed. Open review point (critic): the holds file pairs public OCDS record ids with the hold basis, which would let a reader of an open-sourced repository look the names up in public eTenders data; the fix (an HMAC key with an uncommitted salt, or keeping the file out of the public repository) waits for the owner's decision and must land before open-sourcing. |

## 1. Goal

Mask three Confirmed award rows whose supplier names are personal names, using the existing "held" group (CHG-TW-004 §13.2), and keep that decision in git so every build applies it, the nightly's fresh clone included.

## 2. What changes (exact files)

* New `config/popia_holds.json`: three entries keyed by award record (`ocid` and `award_id`) with a `basis` line. **No supplier name is in the file**, because the repository is to be open-sourced (same rule as `tests/test_no_names_in_committed_files.py`).
* `tw/site_build.py`: `load_holds()` checks the file (each entry needs `ocid`, `award_id` and `basis`; no duplicates); `apply_holds()` sets `popia_hold` on the listed records **before** the withheld-name list is made, so the public-file scans also search for the held names (and their linked legal names). A listed record that is not in the input stops the build. The build result reports `tracked_holds_applied`.
* `tests/test_site_build.py`: the DEV-data counts move to 58 named and 8 held; 6 new tests collected (a tracked hold masks a Confirmed row and its reference and name leave every generated file; a missing record stops the build; three malformed-file cases; the committed file has three records and only the allowed keys).
* This RFC and one `STATUS.md` row.

## 3. What stays

* The mask, year-cell and citation rules of CHG-TW-004 rev 7 and 8 are unchanged. A held row shows its legal form, buyer, award date and usable value, with a register-level citation; no tender reference, OCDS id, registration detail, indicator or year digit. All three rows show "Year: Unknown" today, so the held-row Confirmed-year stop (open question Q1) is not triggered.
* Robots `Disallow: /`, `noindex, nofollow`, `CNAME` and Pages settings are not touched.
* The git-ignored local `confirmed_suppliers.csv` was updated to match (`popia_hold` yes on the three rows); the tracked file is what the build relies on.

## 4. Results (DEV)

* Rows: 291. Groups: 58 named, 8 held, 27 personal-looking masked, 192 name-pending, 6 withheld. Years: 258 Unknown, 27 not shown (masked row), 6 withheld.
* Names scanned: 203 withheld (was 198: three OCDS names plus two linked legal names), 718 in all. All five scans clean; none of the three names, their tender references or OCDS ids appear in any generated file.
* `content_sha256`: `c1d2e3d9e0109920f814ba84009918e75b7ee24a49fee44bd4dd5872cd8d05c6`.
* Tests: 278 collected in a fresh virtual environment (on `main` at `5c7c09c2` plus this change); the DEV-data test runs only where the git-ignored DEV export exists and skips on a fresh clone.

## 5. Rollback

Revert the merge of this change in the private repository (`git revert` of its merge commit on `main`; no reset, no force push) and revert the site commit on the site repository the same way. Reverting the site would show the three names again, so a revert needs the owner's GO like any publish.
