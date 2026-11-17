# STATUS

## Current (17 Nov 2026, Africa/Johannesburg)

- Repo: `GrokForum/tenderwatch-sa` (private data repo).
- [PR #1](https://github.com/GrokForum/tenderwatch-sa/pull/1) was merged to `main` on the owner's GO at 17 Nov 2026 15:44:49 SAST (PR `mergedAt` 2026-11-17T13:44:49Z). Merge commit `fb5a4bcc` (full `fb5a4bcc3ca25724a8c5ebdf0cf1fe0caf6ad17c`). Merged head was `10862ba5` (full `10862ba565fbf3ac70bc3993d19f7ab1fe28ef3d`). Rollback tag `snapshot-2026-11-17-pre-tw-pr1` points at `b812102eb8d5eea0c6a486e8a332a1bf62e08d76`.
- CAB recorded a GO for the CHG-TW-001 **build, DEV only** (relayed by Cavus, 17 Nov 2026). That is not a GO to push, merge further work, publish, or open TEST/PROD.
- Branch `dev/CHG-TW-001-build` starts from `origin/main` (`fb5a4bcc`) and holds the DEV pilot implementation. This work tree does not push. Owner standing GO, given in Cavus's chat on 17 Nov 2026 and relayed by Cavus: "You can push review branches without asking". Merges and publishing still need the owner's GO on the exact head.
- PublicFunds pin (read-only, no edits): `de37f666c12d1d6b7a815860894af0372514ba7f`. OCDS file SHA-256 `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225`.
- Public site repo `GrokForum/tenderwatch-site` exists (public, noindex placeholder). Not touched.
- Rollback for this DEV branch: `fb5a4bcc3ca25724a8c5ebdf0cf1fe0caf6ad17c` (pre-build `main`). Pre-PR #1 snapshot: tag `snapshot-2026-11-17-pre-tw-pr1` (`b812102`).

| Date | RFC | Env | Result | Rollback SHA |
|---|---|---|---|---|
| 2026-11-17 | CHG-TW-001 | DEV (docs, samples, classifier tests) | Draft PR #1 raised at `c75e5ef` 11:48 SAST; later heads pushed by Cavus under the standing GO; merged 15:44:49 SAST as `fb5a4bcc` on the owner's GO. | b812102eb8d5eea0c6a486e8a332a1bf62e08d76 |
| 2026-11-17 | CHG-TW-001 | DEV (pilot ingest, local export) | SUCCEEDED on this box. 291 Cape Town award–supplier rows from the pinned PublicFunds OCDS dump; City 2026 monthly registers (Feb–Oct) ingested after a robots-allowed light fetch; all live indicators `unknown` (no sourced CIPC year); public export withholds non-juristic names. See `docs/dev/CHG-TW-001-run-report.md`. Pushed for review as draft PR #2 (`dev/CHG-TW-001-build`). | fb5a4bcc3ca25724a8c5ebdf0cf1fe0caf6ad17c |
