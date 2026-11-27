# CHG-TW-016 — CIPC registration-number explainer page

| Field | Value |
|---|---|
| Change | CHG-TW-016 |
| Type | Site-builder content change in this repository only. |
| Environment | DEV: local tests and the site-build checks. TEST: the test suite in a clean export. PROD: none in this change; the site repository is not touched. The page reaches https://tenderwatch.grokforum.site only after a later, separately reviewed publish to `GrokForum/tenderwatch-site` (GitHub Pages serves that repository's `main`). `publish_enabled` stays false. |
| Branch | `dev/CHG-TW-016-cipc-explainer` from `main` at `e4301ba9b4a1cf254faa21fb5dc40f7187b5fc80`. |
| Rollback reference | `e4301ba9b4a1cf254faa21fb5dc40f7187b5fc80`. Revert the merge; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Owner GO of 27 Nov 2026 (relayed by the project lead): publish the registration-number explainer that the critic plain-PASSed (sha256 `6cd63235cf7bafb199510e341425a38fb56cfdb503da018e6eea8f21b12ace2c`). |
| Status | Awaiting review. |

## 1. Goal

Add the approved explainer as a DRAFT site page (FAQ and methodology note), linked from the site navigation, the footer, and the Sources and method page, without adding a registration-number field to the register and without publishing or deploying.

## 2. What changes (exact files)

* `tw/site.py`: new page at `/method/registration-numbers/`; links in the site nav and footer; the short methodology note on Sources and method. The two 9,551/0 survey blocks share one string (aligned wording). The page uses the site's existing DRAFT chrome and `<meta name="robots" content="noindex, nofollow">`. Citations are public URLs only (no `[S#]`, no pointer to a brief). Present-tense claims about showing registration numbers stay worded as intended policy, because the register has no registration-number field.
* `tw/check_live.py` and `tw/dq.py`: the new page is included in the live-check and data-quality page lists.
* `tests/test_site_build.py` and `tests/test_nightly.py`: the expected page set, and a wording test for the intended-policy language, the shared survey text, the role address, and the absence of brief or `[S#]` citations.
* This RFC. `STATUS.md` is not edited (feature PRs do not add STATUS rows; that is a later docs PR).

## 3. What stays

* `publish_enabled` and `push_log` stay false; `GrokForum/tenderwatch-site` is not touched; `CNAME` is not touched; `robots.txt` remains `Disallow: /`.
* The register has no registration-number field or column.
* The site's indexing policy is unchanged: every HTML page is DRAFT and `noindex, nofollow`.
* Forward-only history: no rebase, no force push.

## 4. Success

* The full pytest suite passes in the work tree: 401 passed. Counts from a clean export are recorded in the PR body if they differ (DEV-data and git-checkout tests skip by design).
* The built page carries the site's DRAFT banner and noindex meta, names only `privacy@grokforum.site`, states that no site has a registration-number field today, and words the practice as intended policy.
* Mutation of the new wording test: removing the intended-policy sentence or the shared survey string makes the test fail.

## 5. Rollback

Revert the merge of this branch into `main`. Pre-change commit: `e4301ba9b4a1cf254faa21fb5dc40f7187b5fc80`. The published site is not changed by this RFC.

## 6. POPIA

No private person's personal information, no named firms, and no identity numbers are added. The only contact address is `privacy@grokforum.site`. The example number `2020/123456/07` is a stock illustration, not a real company. The 9,551/0 figure is an aggregate count over award–supplier rows. Sole traders and one-person companies are mentioned only as a reason to keep masking. The text accuses no one and is marked "not legal advice".

## 7. Seen, not touched

* `STATUS.md` is left for a later docs PR.
* An unpublished GoatCounter pixel RFC was previously drafted under the id CHG-TW-015, which `main` already used for the SA-ID scan (PR #23). This change takes the next free number, 016. That GoatCounter draft is not in this repository and is not edited here.
* The explainer's image card and social-media thread are out of scope for this change.
* Implementing the intended registration-number field, or turning publishing on, needs a later change and a GO on that head.

Result: SUCCEEDED in DEV and TEST (awaiting review).
