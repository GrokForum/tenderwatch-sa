# CHG-TW-011 — Buyers beyond the City of Cape Town (DEV staging from eTenders OCDS, publication 143)

| Field | Value |
|---|---|
| Change | CHG-TW-011 |
| Type | Code change (national ingest, site build input and copy, tests, config) in this repository only. |
| Environment | DEV only: local builds into `data/local/site-build-national-<stage>/` (git-ignored). TEST: the test suite in a clean export and the public-file scans. No PROD: the nightly, the site repository and the published site are not touched. |
| Branch | `dev/CHG-TW-011-national-staging`, stacked on `dev/CHG-TW-010-one-person-names` (the one-person-name holds must apply to national rows). Base of the stack: `main` at `4f9dab45214c9621e46c5247b3725e6f4deb0647`. |
| Rollback reference | `4f9dab45214c9621e46c5247b3725e6f4deb0647` (and the CHG-TW-010 head below this change). Revert the merge; no reset, no force push. |
| Author | the author bot |
| Reviewers | Reviewer A and the critic |
| Basis | Project lead's direction of 20 Nov 2026, 20:21 SAST (owner direction relayed): go beyond the City of Cape Town using the source pack of 20 Nov 2026; stage eThekwini and Mangaung first, then all buyers if clean. |
| Status | Stage 1 DEV and TEST done and clean; stage "all" built in DEV and **not clean** (§6), so it stays off. Draft PR for review. Merges only on the owner's GO naming the head. |

## 1. Goal

Add buyers beyond the City of Cape Town from the pinned eTenders OCDS file, under the same rules: legal form from the name, POPIA masking (CHG-TW-004, -008, -010), every row accounted for, scans before anything could be published. Stage 1 is eThekwini and Mangaung; "all" is every buyer with an award.

## 2. Source, licence and terms (checked 20 Nov 2026)

* OCP Data Registry, publication 143 (National Treasury eTenders OCDS), `full.jsonl.gz`. The pinned file in `config/chg-tw-001-dev.json` (SHA-256 `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225`, 11,676,874 bytes) is the publication's current file: the live download has the same size (ETag size field `b22cca` = 11,676,874) and `Last-Modified: Sun, 20 Sep 2026 06:35:04 GMT` (20 Sep 2026, 08:35 SAST), before the local copy was taken (19 Oct 2026). No new download was needed.
* Licence: Open Data Commons PDDL (publication page). National Treasury's publication policy ("Learn more") allows reuse and republishing with a link to the original source; the site's method page already cites both. `robots.txt` on data.open-contracting.org allows all paths.
* The file has 9,551 award-supplier rows across 488 buyers with awards (731 buyer strings in all releases), no duplicate award-supplier keys and no duplicate release ids. eTenders carries **no CIPC registration numbers** (0 of 9,551), so no registration year or age band is derived for national rows: they show `Year: Unknown`. A year needs a matching second detail from a free public source (later change).

## 3. What changes (exact files)

* `config/national.json` (new): stages (`stage1` = "Ethekwini Metropolitan Municipality", "Mangaung Metropolitan Municipality"; `all` = every buyer), row bounds per stage (stage1 100–200, all 9,000–9,400), the municipal-buyer pattern, and the City excluded (its rows come from the CHG-TW-002 export with the City register as second source).
* `tw/ocds.py`: `award_rows_from_release` takes an optional `buyer_filter` (default: City of Cape Town only, unchanged); new `iter_awards` (same pin check; `source_file` is the file name, not a box path).
* `tw/national.py` (new): `ingest(stage)` reads the pinned file, blanks a tender title or id shaped like an SA ID number or email (`redact_id_like`, counted), runs the POPIA checks, the CHG-TW-002 classifier with no City rows, and the no-silent-hide check; stops if the row count is outside the stage's bounds or a key repeats. `summary()` gives counts only.
* `tw/site.py`: I1 is counted **per buyer** (it was per supplier and year, which was only right while there was one buyer) and only for municipal buyers when a municipal list is given (the municipal financial year is 1 July to 30 June); owner lookups and the City register citation apply only to City rows; the home and method pages describe more than one buyer when there is more than one. **City-only builds are byte-identical** (content hash unchanged from CHG-TW-010).
* `tw/site_build.py`: `run_build(out, extra_rows=…, municipal_buyers=…)`; a national row that repeats a City row stops the build; the input hash covers the national rows; `pending_names_shown_elsewhere()` (below); the result reports `buyers`.
* `scripts/build_national.py` (new): DEV build of a stage; exit 0 only if every scan is clean.
* `tests/test_national.py` (new, 9 tests, invented names; one DEV-data test that skips on a fresh clone).
* This RFC and one `STATUS.md` row.

**Withheld-name scan, one narrow exemption.** The same supplier string can be a shown, Confirmed company on a City row (legal form from the City register) and a name-pending row for another buyer, where eTenders prints it without a suffix. No cross-buyer link is made (two-detail rule): the other row still shows "Supplier name pending check". Because the name is already public on the City row, it is not a finding of the withheld-name scan. A name tied to any held, personal-looking or withheld row is never exempted; the count is reported (`pending_names_shown_elsewhere`; 1 in stage 1). The all-names scan is unchanged.

## 4. What stays

* The City pipeline, its 291 rows and its build (`content_sha256` `581ed60b…` unchanged), the nightly (it still builds the City register only), the holds file and every publication rule.
* `publish_enabled` and `push_log` stay `false`; nothing is published.

## 5. Results — stage 1 (DEV and TEST)

* National rows: 138 (eThekwini 80, Mangaung 58), award dates 14 Jul 2021 to 12 Jun 2026. eTenders gives these buyers' supplier names **without legal-form suffixes**: 0 Confirmed, 129 name-pending, 9 personal-looking (masked). Registration year known: 0.
* Combined DEV build: 429 rows, 3 buyers; groups 56 named, 10 held, 36 personal-looking masked, 321 name-pending, 6 withheld; years 387 Unknown, 36 not shown (masked), 6 withheld. Names scanned: 332 withheld (after 1 exemption above), 843 in all. **All five scans clean.** `content_sha256` `bb58333a9076b1dcab13c0a9ca2595a6f6a648300444c3b9b02c7e924c5c6d4e`.
* Tests: 331 collected, 331 passed in this checkout (DEV data present); in a clean export the DEV-data tests skip (see the PR).

## 6. Results — stage "all" (DEV only, not clean; stays off)

* 9,260 national rows, 487 buyers (+ the City's 291 = 9,551). 1 tender title blanked (13-digit, ID-shaped). Classification: 201 Confirmed, 7,745 name-pending, 1,261 personal-looking, 12 personal trusts, 40 ambiguous suffix, 1 empty name. Auto holds (CHG-TW-010): 81 more rows held; 33 single-word names for review.
* Combined build: 9,551 rows; groups 177 named, 90 held, 1,300 personal-looking, 7,937 name-pending, 47 withheld. **Scans not clean**: names (7 files), PII shape (2: an SA phone-number shape in tender titles), wording (2: a loaded word in a tender title). The build exits 1, so this stage is not used.
* Causes seen (counts only): eTenders supplier strings of one to four characters and placeholders (for example a literal "None") match the page template text; tender titles carry phone-shaped numbers and the word flagged by the wording scan. Fixes for a later change: treat names under five characters and placeholders as `empty_name` and scan them with word boundaries; blank phone-shaped tender titles like ID-shaped ones; decide how to show a tender title that contains a loaded word (owner question).

## 7. Municipal sources in the pack (planned, not implemented)

| Source | Format | Status from this box, 20 Nov 2026 | Plan |
|---|---|---|---|
| eThekwini awarded tenders | monthly PDFs | `www.durban.gov.za` fails TLS certificate verification (CHG-TW-009 probe: "unable to get local issuer certificate") | Blocked: TLS is never switched off. Retry when the chain verifies, or the owner decides on a pinned intermediate certificate. Then a PDF parser like the City's, second source for the 80 eTenders rows. |
| Mangaung awarded bids | monthly PDFs (`File/download.aspx`) | TLS ok; `robots.txt` returns HTTP 404 (no robots file) | Terms of use not yet read; PDF parser is a medium job. Second source for the 58 eTenders rows. |
| Ekurhuleni bids awarded | HTML tables | TLS certificate verification fails | Blocked as eThekwini. Easiest parser once readable. |
| Tshwane awarded tenders | XLSX and DOCX | TLS certificate verification fails; bare requests get HTTP 403 | Blocked as eThekwini; a browser-like user agent is not used to get past a 403. |
| Buffalo City awarded tenders | PDFs | not probed in this change | Later; 0 eTenders awards, so single-source rows (Reported, Unconfirmed). |

None of these was quick and allowed, so none is implemented here.

## 8. Rollback

Revert the merge of this change on `main` (`git revert -m 1 <merge>`). The published site is not changed by this RFC.

## 9. Open questions for the owner

* Q-011-1: Publish stage 1 (429 rows, 3 buyers) on the next site change? It adds 138 rows, none named (eTenders prints these buyers' names without suffixes). Needs the owner's GO naming a head and a site change of its own.
* Q-011-2: A tender title that contains a loaded word (for example the name of an offence in a tender for a related service): show as published by the source, or blank it?
* Q-011-3: eThekwini, Ekurhuleni and Tshwane fail certificate verification from this box. Wait for the sites, or allow a pinned intermediate certificate per host (never switching verification off)?

Result: SUCCEEDED for stage 1 in DEV and TEST (awaiting review); stage "all" NOT CLEAN, kept off.
