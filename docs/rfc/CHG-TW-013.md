# CHG-TW-013 — POPIA scan of this repository (tree and full history) before any visibility change

| Field | Value |
|---|---|
| Change | CHG-TW-013 |
| Type | Records only (this finding). No code, no data, no repository setting changes. |
| Environment | DEV: a read-only mirror clone on the box (all refs, pull-request refs included). |
| Branch | `dev/CHG-TW-013-popia-repo-scan` from `main` at `4f9dab45214c9621e46c5247b3725e6f4deb0647`. |
| Rollback reference | `4f9dab45214c9621e46c5247b3725e6f4deb0647`. Revert the merge. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Project lead's direction of 20 Nov 2026, 20:21 SAST (owner direction relayed): "Repos are public by default now: if tenderwatch-sa is clean after a POPIA scan, propose making it public." |
| Status | Finding recorded. **Verdict: BLOCK** for making this repository public. Visibility is not changed. |

## 1. What was scanned

* A mirror clone of `GrokForum/tenderwatch-sa` taken 20 Nov 2026 (SAST): 96 commits reachable from 38 refs (`main`, 12 other branches, 11 tags, 14 pull-request refs including `refs/pull/13/merge`). Every text blob reachable from any ref was read.
* **Recount (20 Nov 2026, 21:15 SAST, after PR #13 and PR #16 landed on `main`):** a fresh mirror clone of `GrokForum/tenderwatch-sa` has **133 commits reachable from 52 refs** (`main`, 15 other branches, 12 tags, and 24 pull-request refs: 19 `/head` and 5 `/merge`). (Before PR #13 and PR #16 were closed/merged and their branches and `/merge` refs dropped, the open-PR snapshot had 55 refs.)
* Terms (kept outside the repository, mode 600, never printed): 713 supplier and vendor names of six characters or more from the DEV warehouse (eTenders and City register), the 195 queued or withheld names (CHG-TW-002), the 5 names tied to the owner's three holds (CHG-TW-008), and the 3 held record ids. Patterns: SA ID-number shape (13 digits), SA phone shape, email addresses, box paths, the review kit's agent-name list. Commit author and committer identities.
* The review kit with `--scan-tree` and the same terms on the tree at `main` (gitleaks over the last three merges: 0 findings).

Findings below give counts, paths and refs only.

## 2. Tree at `main` (`4f9dab45`)

| # | Finding | Where | Weight |
|---|---|---|---|
| T1 | 4 distinct real supplier names (all are rows the register shows by name, or vendor lines in the City's published PDFs); 2 more kit hits are fragments that also match invented test names | `data/samples/city-of-cape-town/…csv`, `data/samples/etenders-ocds/…json`, `SOURCES.md`, `tests/test_match.py`, `tests/test_samples_and_city.py` | Breaks the rule "never commit supplier names" for an open-source repository; not a private person. |
| T2 | No queued, withheld or held name, and no held record id | — | Clean. |
| T3 | Absolute box paths in 8 files | `config/chg-tw-001-dev.json`, `SOURCES.md`, `data/samples/etenders-ocds/…json`, `docs/dev/CHG-TW-001-run-report.md`, `docs/rfc/CHG-TW-001.md`, `scripts/count_identifiers.out.json`, `scripts/count_identifiers.py`, `tests/test_site_build.py` (the last as a scan test value) | Infrastructure detail; remove before publishing. |
| T4 | Email addresses: only the allowlisted role addresses, a `github.com` SSH remote form, and reserved example domains in tests | `docs/rfc/CHG-TW-007.md`, `tw/nightly.py`, tests | Clean. |
| T5 | 13-digit (ID-shaped) runs: commit-hash fragments in `STATUS.md` and RFCs, and deliberate synthetic values in tests; phone shapes only in tests | — | Clean (no real ID or phone number). |
| T6 | No agent name from the kit's list in the tree; the kit flags product names in the "Author" line of CHG-TW-006, -007 and -008 (6 lines) | `docs/rfc/CHG-TW-006.md` … `-008.md` | Docs hygiene; role words in a fresh repository. |
| T7 | No secrets (gitleaks 0, kit secrets check 0) | — | Clean. |

## 3. History and refs

| # | Finding | Refs | Weight |
|---|---|---|---|
| H1 | **Commit identities**: the owner's personal-name address is the author of 11 commits on `main` (the GitHub web squash merges; 22 across all refs at the initial 38-ref scan, **28** across all refs at the 55-ref review snapshot, and **26** across all refs in the 52-ref recount after PR #13 and PR #16 landed), and a `localhost` bot identity is on 25 `main` commits (60 across all refs). At the 52-ref recount snapshot (`main` then `72d6bee`, not current `main`), only 7 commits reachable from `main` used a neutral `grokforum.site` noreply identity (5 on the `grokforum.site` domain, 2 on its `tenderwatch` subdomain; current `main` `91f8dfbc` has 6 first-parent (1 domain, 5 subdomain) and 10 reachable; 47 across all refs at the 52-ref recount: 38 publisher, 9 noreply bot). Measure: commits whose **author** address is a neutral noreply address, split by author name. The critic's figure for the same 52-ref snapshot is 54, by a noreply-email metric that this record does not reproduce, because the snapshot's refs have since changed. A fresh mirror on 21 Nov 2026 (50 refs, 141 commits) gives 59 by the author measure. The count is also 59 when a commit counts if either its author or its committer address is a neutral noreply address, so the two fields do not diverge there. | `main`, all branches and tags | **Blocking**: the owner must stay anonymous in a public repository. |
| H2 | A per-name classification report with the held names and held record ids | `refs/pull/3/head` (PR #3, closed unmerged) | **Blocking**: held names are exactly what CHG-TW-008 masks. |
| H3 | The first CHG-TW-008 revision's tracked holds file (`config/popia_holds.json`, `902dac4f`) with the three held record ids | `refs/pull/12/head` | **Blocking** (known; CHG-TW-008 §2). |
| H4 | Queued or withheld names (9 blobs over 4 paths: `SOURCES.md`, the eTenders sample, the classification report, a test) | `refs/pull/1/head` to `refs/pull/5/head` | **Blocking**: these names are withheld from the public site. |
| H5 | An agent name in 6 commit messages | history | Docs hygiene. |

Repository users cannot delete `refs/pull/*`; only GitHub Support can remove them, and branch deletion or a history rewrite of `main` does not reach them.

## 4. Verdict

**BLOCK** for changing the visibility of `GrokForum/tenderwatch-sa`. Items removed: none (records only). The tree at `main` has no private person's details, but its history and pull-request refs carry held and withheld names (H2–H4) and the owner's identity (H1).

## 5. Recommendation

1. Do not change this repository's visibility. It stays private (owner's decision on deleting it later, as in the owner's repo plan).
2. Open-source through the agreed **fresh repository** with **one clean root commit** under `TenderWatch publisher <noreply@tenderwatch.grokforum.site>`, built from a clean export of `main` after the open changes merge, with:
   * `data/samples/` replaced by invented fixtures, and the tests that use real names (T1) moved to invented names;
   * `scripts/*.out.json` removed and box paths taken out of `config/chg-tw-001-dev.json`, `SOURCES.md`, the run report and RFC-001 (input paths move to a git-ignored local config);
   * role words in every RFC header (T6); no `data/local/`, no holds file, no names file, no old history, no PR records;
   * the full test suite, the public-file scans and the review kit (names file of all DEV supplier names, `--scan-tree`) clean on the seed tree, reviewed by both reviewers on the exact head, then the owner's GO to push.
3. After the fresh repository exists, squash merges there must keep the neutral identity (GitHub web merges carry the merger's address; merge from the box under the publisher identity, or check each merge).

## 6. Rollback

Records only: revert the merge of this change.

Result: SUCCEEDED (finding recorded; visibility unchanged).
