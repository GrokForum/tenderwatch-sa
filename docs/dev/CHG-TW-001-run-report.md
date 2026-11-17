# CHG-TW-001 DEV run report

Environment: **DEV** (local box only). No push, no Pages, no TEST/PROD, no PublicFunds edits.

- Run: 2026-11-17 15:55 SAST (Africa/Johannesburg) to 2026-11-17 15:55 SAST (Africa/Johannesburg)
- PublicFunds pin: `de37f666c12d1d6b7a815860894af0372514ba7f` (read-only)
- OCDS input: `/workspace/publicfunds/data/raw/etenders_ocds/2026-10-19/full.jsonl.gz`
- SHA-256: `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225` (matches the RFC / survey file)

## Counts (not invented)

| Measure | Count |
|---|---|
| Award–supplier rows loaded (City of Cape Town) | 291 |
| Distinct award OCIDs | 278 |
| `supplier_type` juristic | 2 |
| `supplier_type` natural_person | 0 |
| `supplier_type` unknown | 289 |
| Indicator `yes` | 0 |
| Indicator `no` | 0 |
| Indicator `unknown` | 291 |
| Age band `same` | 0 |
| Age band `-1` | 0 |
| Age band `-2` | 0 |
| Age band `older` | 0 |
| Age band `unknown` | 291 |
| City register rows ingested (vendor-award lines) | 508 |
| City register unique TTS references | 171 |
| City register rows with a vendor name | 507 |
| Awards with at least one two-detail City link | 71 |
| City link pairs (two-detail rule) | 135 |
| Public export rows | 291 |
| Named suppliers in the public export (juristic only) | 2 |

City register source: live_fetch. Light fetch was limited to the official 2026 monthly `tenders-awarded` PDFs linked from the City index, after checking robots.txt (Allow: /). Files already on disk were reused.

Match breakdown (agreeing details): {'name_key,buyer': 107, 'name_key,buyer,tender_ref': 5, 'buyer,tender_ref': 23}. Links on `name_key,buyer` only mean the same normalised name in the same jurisdiction, not necessarily the same tender. Links that also share a tender/TTS reference are the tighter comparison.

Light fetch log: fetched=11 URLs; skipped=[]; errors=[]; parsed_rows=508.

All award rows are fact-labelled **Confirmed** as published by the source. Registration year and the young-supplier indicator are **Unknown** unless a sourced CIPC number in a free public document supplied a year (labelled Confirmed, with a link). `Right of reply: pending` is stored on every row. Nothing was sent or published.

Attribution: National Treasury / OCPO eTenders OCDS; source https://data.open-contracting.org/en/publication/143 and policy https://data.etenders.gov.za/Home/LearnMore. City of Cape Town monthly award register where fetched or sampled, with provenance next to the local file.
