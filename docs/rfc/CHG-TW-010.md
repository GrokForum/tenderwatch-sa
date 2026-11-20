# CHG-TW-010 — Mask one-person business names automatically (POPIA)

| Field | Value |
|---|---|
| Change | CHG-TW-010 |
| Type | Code change (site build input, a build gate, tests) in this repository only. |
| Environment | DEV: local build into `data/local/site-build/` (git-ignored). TEST: the test suite in a clean export and the public-file scans. PROD: none in this change; the site repository is not touched. The next publish would carry two more masked rows and needs the owner's GO naming its head. |
| Branch | `dev/CHG-TW-010-one-person-names` from `main` at `4f9dab45214c9621e46c5247b3725e6f4deb0647`. |
| Rollback reference | `4f9dab45214c9621e46c5247b3725e6f4deb0647`. Revert the merge; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Project lead's direction of 20 Nov 2026, 20:21 SAST (owner direction relayed): "Mask one-person business names (POPIA)." Extends CHG-TW-008. |
| Status | DEV and TEST done; draft PR for review. Merges only on the owner's GO naming the head. |

## 1. Goal

A registered firm whose name is a person's name ("<given name> <surname> Transport CC", "<initials><surname> Electrical CC") identifies that person. Such rows are masked like the other held rows, by an automatic detector, so that national data (CHG-TW-011) can be added without a hand-made hold for every one. The owner's fail-closed holds file (CHG-TW-008, git-ignored) stays in force for anything the detector misses.

## 2. Rule (tw/popia_names.py)

* Split any `"t/a"` / `"T/A"` / `"t.a."` / `"trading as"` marker into legal-name and trading-name parts, drop outer brackets, trailing legal-form suffixes (stacked "(RF) (Pty) Ltd" included) and a leading "the" on each part, and hold the row if **either** part reads as a person's name.
* The **head** is the run of words before the first trade, place or legal word, or the first word with a digit. The word list is the classifier's business words plus a detector-only list of place and trade words (north, south, western, truck, financial, and similar). The classifier's own list is not changed, because it also decides which bare names are held in the check queue, and adding words there would hold fewer of them.
* **`personal_stem`**: a head of two to four alphabetic words (name particles such as "van", "der", "du" not counted) → the row is held (`popia_hold`, reason `auto:personal_stem`). Initials written together ("JQ") count as a word.
* **`single_word_stem`**: a stem of a single word (a surname alone or a coined brand cannot be told apart) → not held; listed for a person to review.
* Only `confirmed_juristic` rows are looked at; every other row is already masked, pending or withheld. Both the source name and the linked legal name are checked; either one matching holds the row.
* Over-holding is the safe side: a firm named after its founders is masked too, even a well-known one. The owner can decide later whether a reviewed "not a person" list should unmask such firms (open question, §7).

## 3. What changes (exact files)

* `tw/popia_names.py` (new): `name_stem`, `name_head`, `one_person_reason`, `apply_auto_holds` (counts only) and `write_review_candidates` (a git-ignored local CSV, `data/local/popia_review_candidates.csv`, mode 600, with the auto-held and single-word names for a person to review; never committed, never published).
* `tw/site_build.py`: after the owner's holds and **before** the withheld-name list is made (so the scans also search for auto-held names), `apply_auto_holds` runs and the review list is written. `run_build()` writes into a temporary directory alongside the target and atomically replaces the target only after the **build gate** (`UnsafeBuild` if any shown, unmasked name reads as a person's name) and the scans complete; a gate failure leaves any previous output untouched. The result reports `auto_holds`.
* `tests/test_popia_names.py` (new, 25 tests, invented names only), including the gate with the detector switched off. `tests/test_site_build.py`: DEV counts updated (below).
* This RFC and one `STATUS.md` row.

## 4. What stays

* The mask, year-cell and citation rules (CHG-TW-004 §13.2, §13.8), the holds file and its checks (CHG-TW-008), the CHG-TW-002 classifier and its word list.
* `publish_enabled` and `push_log` stay `false`; the site repository is not touched.

## 5. Results (DEV and TEST)

* DEV build (291 rows): groups **56 named, 10 held**, 27 personal-looking masked, 192 name-pending, 6 withheld (was 58 / 8). Auto holds: 2 new rows; the detector also finds, by itself, all 3 owner holds and the 5 classifier holds (`already_held` 8); 7 single-word stems listed for review (not held).
* Names scanned: 207 withheld (was 203), 718 in all; all five scans clean. `content_sha256` `581ed60be042de50a0db41e219597bb8e34f67d67927c0721e7a63de941bd866` (was `c1d2e3d9…`).
* Tests: 329 collected (304 + 25). In this checkout with the DEV data: 329 passed. In a fresh virtual environment from a clean export: 326 passed, 3 skipped (DEV-data and git-checkout tests skip by design).

## 6. Rollback

Revert the merge of this change on `main` (`git revert -m 1 <merge>`). The published site is not changed by this RFC.

## 7. Open questions for the owner

* Q-010-1: Should a person-reviewed, git-ignored "not a person" list (name keys) be able to unmask a firm the detector holds (for example a well-known firm named after its founders)? Default until decided: no; the row stays masked.
* Q-010-2: The 7 single-word names listed for review stay shown unless the owner adds holds for any of them (the CHG-TW-008 holds file).

Result: SUCCEEDED in DEV and TEST (awaiting review).
