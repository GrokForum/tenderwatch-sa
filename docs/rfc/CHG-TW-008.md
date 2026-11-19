# CHG-TW-008 — Local POPIA holds: mask three Confirmed firms whose names are personal names

| Field | Value |
|---|---|
| Change | CHG-TW-008 |
| Type | Build change (site build input, checks, tests) in this repository, plus the regenerated static files on the public site repository. |
| Environment | DEV: local build into `data/local/site-build/` (git-ignored). TEST: tests and the public-file scans. PROD: GitHub Pages from `main` of `GrokForum/tenderwatch-site`. |
| Branches | Private repo: `dev/CHG-TW-008-tracked-holds` from `origin/main` at `df7c55d2` (PR #10), then brought forward by a merge of `main` at `5c7c09c2` (PR #11); no rebase, no force push. Public site repo: `dev/CHG-TW-008-masked-register` from `origin/main` at `33b794117075caa383a58a136b4d2cae99c1e92d` (after the owner-approved history rewrite). |
| Rollback reference | Revert the merge (see §5). Pre-change states for reference: private repo `5c7c09c2` (`main` after PR #11), public site repo `33b794117075caa383a58a136b4d2cae99c1e92d`. |
| Author | the author (TenderWatch) |
| Reviewers | the project lead and the critic |
| Basis | Owner decision of 19 Nov 2026, relayed by the project lead: the public site can publish only after the three Confirmed firms whose names are personal names are masked the same way as the other masked rows. Owner decision of 19 Nov 2026, 13:31 SAST, on the critic's review point: the holds file is fixed before this change merges. |
| Status | Site files published on the owner's GO (site `main` at `14270cf5`, 19 Nov 2026). The private-repo change is for CAB and merges only after review of this revision. |

## 1. Goal

Mask three Confirmed award rows whose supplier names are personal names, using the existing "held" group (CHG-TW-004 §13.2), so that every build applies the decision, the nightly's clone included, without putting the decision in git.

## 2. Why the holds file is local (critic's review point, owner decision)

The first revision kept the holds in a tracked `config/popia_holds.json`, keyed by `ocid` and `award_id`. The critic noted that once the repository is open-sourced, a public record id next to the hold basis would let anyone look the names up in the public eTenders data. Of the two fixes offered, this revision takes the simpler one: **the holds file is git-ignored and never committed** (option b). An HMAC key with an uncommitted salt (option a) would still need a local secret on every checkout, so it adds a secret without removing the local file; option b has no key to manage or leak.

The first revision's commit (`902dac4f`) is in this branch's history. The pull request is squash-merged so `main` never carries the file; the branch is deleted after the merge and is not part of any open-source release.

## 3. What changes (exact files)

* `data/local/popia_holds.json` (git-ignored, named in `.gitignore` as well as under `data/local/`): three entries keyed by award record with a `basis` line. It is seeded once into each checkout, like the other DEV inputs (CHG-TW-007 §7 seed list updated).
* `tw/site_build.py`:
  * `load_holds()` **fails closed**: a missing, unreadable or malformed file, or one with fewer holds than decided (`MIN_HOLDS = 3`), stops the build. Each entry must be an object with an `ocid` of the form `ocds-…-N`, an `award_id` that is a positive whole number (0, negative, boolean or text is refused), and a non-empty `basis`; duplicates are refused.
  * `apply_holds()` sets `popia_hold` on the listed records **before** the withheld-name list is made, so the public-file scans also search for the held names and their linked legal names. It stops the build when a listed record is missing from the input, when the record is not a Confirmed row (a hold must never move a check-queue row, withheld or not, into a shown group), or when a basis contains any supplier name, legal name, name key or linked City name from the input (case-insensitive, names of four characters or more).
  * The build result reports `holds_applied`.
* `tests/test_site_build.py`: the DEV-data counts move to 58 named and 8 held; new tests for each rule above, and that the holds file is git-ignored and not tracked.
* `tests/test_nightly.py`: a build stopped by a missing holds file fails the night and never publishes.
* `docs/rfc/CHG-TW-007.md` §7: `popia_holds.json` added to the one-time seed list.
* This RFC, `.gitignore`, and one `STATUS.md` row. `config/popia_holds.json` is removed.

## 4. What stays

* The mask, year-cell and citation rules of CHG-TW-004 rev 7 and 8 are unchanged. A held row shows its legal form, buyer, award date and usable value, with a register-level citation; no tender reference, OCDS id, registration detail, indicator or year digit. All three rows show "Year: Unknown", so the held-row Confirmed-year stop (open question Q1) is not triggered.
* Robots `Disallow: /`, `noindex, nofollow`, `CNAME` and Pages settings are not touched by this change.
* The git-ignored local `confirmed_suppliers.csv` matches (`popia_hold` yes on the three rows).

## 5. Results (DEV)

* Rows: 291. Groups: 58 named, 8 held, 27 personal-looking masked, 192 name-pending, 6 withheld. Years: 258 Unknown, 27 not shown (masked row), 6 withheld.
* Names scanned: 203 withheld (was 198: three OCDS names plus two linked legal names), 718 in all. All five scans clean; none of the three names, their tender references or OCDS ids appear in any generated file.
* `content_sha256`: `c1d2e3d9e0109920f814ba84009918e75b7ee24a49fee44bd4dd5872cd8d05c6`, unchanged from the first revision and identical to the published site files.
* With the holds file moved away, `scripts/build_site.py` exits 2 (UnsafeBuild) and writes nothing to publish.
* Tests: 297 collected in a fresh virtual environment (on `main` at `5c7c09c2` plus this change); the DEV-data test runs only where the git-ignored DEV export exists and skips on a fresh clone.

## 6. Rollback

Revert the merge of this change in the private repository (`git revert` of its merge commit on `main`; no reset, no force push). On the site repository, reverting the published commit `14270cf5` returns the "coming soon" placeholder of `33b79411`, which never carried the three names, so it would not show them; like any site change it needs the owner's GO.
