# STATUS

## Current (17 Nov 2026, Africa/Johannesburg)

- Repo: local clone of private `GrokForum/tenderwatch-sa`.
- Raised as draft [PR #1](https://github.com/GrokForum/tenderwatch-sa/pull/1) at `c75e5ef` on 17 Nov 2026 11:48 SAST. `009ea171` was pushed to that PR on 17 Nov 2026 11:59 SAST (PR `updatedAt` 2026-11-17T09:59:08Z). Both pushes were by Cavus. Owner standing GO, given in Cavus's chat on 17 Nov 2026 and relayed by Cavus: "You can push review branches without asking". Merges and publishing still need the owner's GO on the exact head. The PR is not docs-only: at `c75e5ef` it added the source survey, the RFC, STATUS, the parked idea note, a `.gitignore` update, and sanitized award excerpts under `data/samples/` (eTenders OCDS JSON samples and a City of Cape Town register excerpt with provenance); later commits on the same branch add the classifier, tests and identifier-count script.
- `main` remains at `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` (initial README / .gitignore only) until CHG-TW-001 is reviewed and the owner gives a GO to implement and merge on the exact head.
- Branch `rfc/CHG-TW-001` carries the survey, RFC, samples, a supplier-type classifier with tests, and the identifier-count script. **Result: DRAFT.** Cavus recorded PASS_WITH_CONCERNS on `c75e5ef` and again on `009ea171`. No TEST, PROD, publish or send. This work tree does not push; Cavus pushes review branches under the standing GO above.
- **Owner decision 17 Nov 2026 (relayed by Cavus):** TenderWatch goes ahead as a PublicFunds extension, kept on its own separate track (separate repo and `CHG-TW-*` series; PublicFunds `etenders_ocds` reused as a read-only upstream or pinned dependency; no PublicFunds changes without a PublicFunds RFC; separate public site). Recorded in `docs/rfc/CHG-TW-001.md` §16. This is not a GO to implement, merge, or publish.
- PublicFunds pin named in the RFC: `main` `de37f666` (full `de37f666c12d1d6b7a815860894af0372514ba7f`), verified in `/workspace/publicfunds` on 17 Nov 2026 as the tip of `origin/main` (local checkout was behind, at `7cb9faf`).
- Public site repo `GrokForum/tenderwatch-site` exists (public, noindex placeholder). Not touched.
- Rollback SHA if this branch is abandoned: `b812102eb8d5eea0c6a486e8a332a1bf62e08d76`.

| Date | RFC | Env | Result | Rollback SHA |
|---|---|---|---|---|
| 2026-11-17 | CHG-TW-001 | DEV (docs, samples, classifier tests) | DRAFT. Draft PR #1 raised at `c75e5ef` 11:48 SAST; `009ea171` pushed 11:59 SAST, both by Cavus under the standing GO cited above. Owner decision: proceed as a PublicFunds extension on a separate track. Q7 accepted; Q3 implied resolved. Cavus PASS_WITH_CONCERNS on `c75e5ef` and on `009ea171`. | b812102eb8d5eea0c6a486e8a332a1bf62e08d76 |
- 17 Nov 2026 12:09 SAST: owner resolved Q4 (indicator = same year or year before; age bands same / -1 / -2 recorded for trending) and Q5 (RoR drafts allowed, owner sends). Q6 (licence) open. RFC §5-6 wording on Trust tightened (Cavus nit).
