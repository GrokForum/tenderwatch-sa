# STATUS

## Current (17 Nov 2026, Africa/Johannesburg)

- Repo: local clone of private `GrokForum/tenderwatch-sa`. Push URL on `origin` is disabled (`DISABLE_DO_NOT_PUSH`). Nothing has been pushed.
- `main` remains at `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` (initial README / .gitignore only), as the README requires, until CHG-TW-001 is reviewed and the owner gives a GO to implement.
- Branch `rfc/CHG-TW-001`: source survey (`SOURCES.md`), RFC (`docs/rfc/CHG-TW-001.md`), sanitized samples under `data/samples/`, and the parked idea note. **Result: DRAFT, awaiting CAB review (Cavus, Cassian).** No scaffold, ingest, TEST, PROD, publish or send.
- **Owner decision 17 Nov 2026 (relayed by Cavus):** TenderWatch goes ahead as a PublicFunds extension, kept on its own separate track (separate repo and `CHG-TW-*` series; PublicFunds `etenders_ocds` reused as a read-only upstream or pinned dependency; no PublicFunds changes without a PublicFunds RFC; separate public site). Recorded in `docs/rfc/CHG-TW-001.md` §16. This is not a GO to implement, merge, push or publish.
- Public site repo `GrokForum/tenderwatch-site` exists (public, noindex placeholder). Not touched.
- Rollback SHA if this branch is abandoned: `b812102eb8d5eea0c6a486e8a332a1bf62e08d76`.

| Date | RFC | Env | Result | Rollback SHA |
|---|---|---|---|---|
| 2026-11-17 | CHG-TW-001 | DEV (docs and samples only) | DRAFT, awaiting CAB. Owner decision (relayed by Cavus): proceed as a PublicFunds extension on a separate track. Identifier options added as an open question. | b812102eb8d5eea0c6a486e8a332a1bf62e08d76 |
