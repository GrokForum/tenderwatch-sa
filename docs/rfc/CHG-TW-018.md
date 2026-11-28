# CHG-TW-018 — Watch-network footer link on every built page

| Field | Value |
|---|---|
| Change | CHG-TW-018 |
| Type | Site-builder chrome change in this repository only. |
| Environment | DEV: local tests and the site-build checks. TEST: the test suite in a clean export. PROD: none in this change; `GrokForum/tenderwatch-site` is not touched. The link reaches https://tenderwatch.grokforum.site only after a later, separately reviewed publish. `publish_enabled` stays false. |
| Branch | `rfc/CHG-TW-018-watch-backlink` from `main` at `45646078782f5bb3d662de9e8fe03186c601265b`. |
| Rollback reference | `45646078782f5bb3d662de9e8fe03186c601265b`. Revert the merge; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Owner GO of 28 Nov 2026 (t812u, relayed by the project lead): build the Watch-network footer link on a local branch only. No push or PR until a separate owner GO names the head. `publish_enabled` stays false. Spec: the umbrella draft RFC-WATCH-BACKLINK (footer link from every watcher site to https://watch.grokforum.site/). |
| Status | Local DEV branch only. No push or PR is authorised by t812u. |

## 1. Goal

Append a visible, plain footer link on every built HTML page back to the Watch directory at `https://watch.grokforum.site/`. This is a surgical chrome change only. It does not change existing footer wording except to append the new link, and it does not change indexing, robots, DRAFT banners, data, DNS or Pages settings.

## 2. What changes (exact files)

* `tw/site.py` function `page()`: after the existing footer paragraph, append one paragraph: `<p><a href="https://watch.grokforum.site/">Part of the Watch network — watch.grokforum.site</a></p>`. The visible text uses a Unicode em dash (U+2014). The `href` is exactly `https://watch.grokforum.site/` (https, host only, trailing slash, no path, query or fragment). Plain `<a>`: no `target`, no `rel`, no tracking parameters. Register, method, registration-numbers, privacy and 404 already go through `page()`.
* `tests/test_site_build.py` `test_every_page_has_draft_noindex_privacy_csp`: every built `*.html` page must contain that exact href and visible text, and must not contain a query-string variant of the href. Existing assertions for `noindex, nofollow`, the DRAFT banner, CSP, the privacy link and `robots.txt` `Disallow: /` stay.
* This RFC. `STATUS.md` is not edited (feature PRs do not add STATUS rows; that is a later docs PR).

## 3. What stays

* `publish_enabled` and `push_log` stay false; `GrokForum/tenderwatch-site` is not touched; `CNAME` is not touched; `robots.txt` remains `User-agent: *` / `Disallow: /`.
* Every HTML page remains DRAFT with `<meta name="robots" content="noindex, nofollow">`.
* Existing footer sentences, nav, privacy contact, CSP, referrer policy, and the absence of third-party scripts or trackers.
* The registration-numbers page body mention of `watch.grokforum.site` in prose is unchanged and is not treated as a backlink.
* Forward-only history: no rebase, no force push.

## 4. Success

* The full pytest suite passes in the work tree and in a clean `git archive` export. Counts are recorded in the commit and review notes.
* Every built HTML page contains `href="https://watch.grokforum.site/"` and the exact visible text `Part of the Watch network — watch.grokforum.site`.
* `noindex, nofollow` and `Disallow: /` remain on the built tree.
* Mutation of the new assertions: removing the footer href, or adding a query string to it, makes the test fail.

## 5. Rollback

Revert the merge of this branch into `main`. Pre-change commit: `45646078782f5bb3d662de9e8fe03186c601265b`. The published site is not changed by this RFC.

## 6. POPIA

No private person's personal information, no named firms, and no identity numbers are added. The only contact address remains `privacy@grokforum.site`. The new footer names only the public Watch directory URL.

## 7. Seen, not touched

* `STATUS.md` is left for a later docs PR.
* `GrokForum/tenderwatch-site`.
* An unpublished GoatCounter pixel RFC is already CHG-TW-017 (local head `81b7f69e`, unpublished). That draft is not in this repository and is not edited here. This change is 018.
* Indexing policy, robots, DRAFT banner copy, CSP, CNAME, DNS, Pages settings, and `publish_enabled`.
* Turning publishing on, or copying a build to the site repository, needs a later change and a GO on that head.

Result: SUCCEEDED in DEV (local branch only; awaiting a later owner GO before any push or PR).
