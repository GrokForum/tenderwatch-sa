# TenderWatch SA

A neutral, sourced public register of South African government tender awards and how established each winning supplier is.

This repository is private and empty of product code on `main` until the first change (CHG-TW-001) is reviewed and the owner gives a GO.

## Current draft

Raised as draft [PR #1](https://github.com/GrokForum/tenderwatch-sa/pull/1) at `c75e5ef` on 17 Nov 2026 11:48 SAST. `009ea171` was pushed to that PR on 17 Nov 2026 11:59 SAST. Both pushes were by Cavus. Owner standing GO, given in Cavus's chat on 17 Nov 2026 and relayed by Cavus: "You can push review branches without asking". Merges and publishing still need the owner's GO on the exact head. The branch is `rfc/CHG-TW-001`. It has not been merged to `main`.

The PR is not docs-only. At `c75e5ef` it added:

- documentation: this README, [`SOURCES.md`](SOURCES.md), [`STATUS.md`](STATUS.md), the parked idea note [`IDEA-tenderwatch.md`](IDEA-tenderwatch.md), and the RFC [`docs/rfc/CHG-TW-001.md`](docs/rfc/CHG-TW-001.md);
- sanitized award excerpts under [`data/samples/`](data/samples/) (eTenders OCDS JSON samples, a City of Cape Town register excerpt and provenance);
- a [`.gitignore`](.gitignore) update.

Later commits on the same review branch address CAB comments (classifier, tests, identifier counts). A GO to implement, merge to `main`, or publish is still required and must name the exact head.

