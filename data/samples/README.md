# data/samples

Sanitized extracts from the 17 Nov 2026 source survey. Each file records its source URL and fetch date. These are evidence for `SOURCES.md` and `docs/rfc/CHG-TW-001.md`, not a warehouse.

| Path | What | Fetched |
|---|---|---|
| `etenders-ocds/ocp-mirror-cape-town-award-samples.json` | 3 City of Cape Town award rows from the OCP `full.jsonl.gz` held by PublicFunds | PublicFunds copy 19 Oct 2026 09:38 SAST; sample extracted 17 Nov 2026. OCP last retrieved 20 Sep 2026 |
| `etenders-ocds/monthly-2026-07-award-samples.json` | 3 award rows from the official July 2026 monthly OCDS JSON | 17 Nov 2026 10:58 SAST |
| `city-of-cape-town/tenders-awarded-october-2026-samples.csv` | 3 juristic-vendor rows from the City's October 2026 register | 17 Nov 2026 10:57 SAST |
| `city-of-cape-town/PROVENANCE.md` | URL, robots, date-format and POPIA notes for the City extract | — |

No director IDs, addresses or contacts are stored. Contact and address keys from OCDS were dropped. Sole-trader personal names were not copied from City registers.

CHG-TW-002 (reviewer A, PR #3): supplier names that are in the two-person check queue or under a POPIA hold are replaced in these samples by `[withheld: in the CHG-TW-002 two-person check queue]`. The OCID still locates the source record.
