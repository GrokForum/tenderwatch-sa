# TenderWatch SA

A neutral, sourced public register of South African government tender awards and how established each winning supplier is.

[PR #1](https://github.com/GrokForum/tenderwatch-sa/pull/1) (RFC CHG-TW-001) was merged to `main` on 17 Nov 2026 15:44:49 SAST as `fb5a4bcc`, on the owner's GO. The pre-merge rollback tag is `snapshot-2026-11-17-pre-tw-pr1` on `b812102`.

## Current work (DEV only)

The DEV pilot build lives on local branch `dev/CHG-TW-001-build` (not pushed). CAB gave a GO for that build, DEV only. Owner standing GO, given in Cavus's chat on 17 Nov 2026 and relayed by Cavus: "You can push review branches without asking". Merges and publishing still need the owner's GO on the exact head.

It was first raised as draft PR #1 at `c75e5ef` on 17 Nov 2026 11:48 SAST. `009ea171` was pushed to that PR on 17 Nov 2026 11:59 SAST. Both of those review-branch pushes were by Cavus.

The PR is not docs-only. At `c75e5ef` it added:

- documentation: this README, [`SOURCES.md`](SOURCES.md), [`STATUS.md`](STATUS.md), the parked idea note [`IDEA-tenderwatch.md`](IDEA-tenderwatch.md), and the RFC [`docs/rfc/CHG-TW-001.md`](docs/rfc/CHG-TW-001.md);
- sanitized award excerpts under [`data/samples/`](data/samples/) (eTenders OCDS JSON samples, a City of Cape Town register excerpt and provenance);
- a [`.gitignore`](.gitignore) update.

Later commits on that review branch addressed CAB comments (classifier, tests, identifier counts) before the merge. The DEV implementation and local run report are on `dev/CHG-TW-001-build`; see [`docs/dev/CHG-TW-001-run-report.md`](docs/dev/CHG-TW-001-run-report.md) and [`STATUS.md`](STATUS.md).

