# SOURCES — TenderWatch SA feasibility survey

**Status:** draft evidence for CHG-TW-001. Local research only. Nothing has been pushed, published or sent.
**Survey date:** Tue 17 Nov 2026, Africa/Johannesburg (SAST).
**Prepared for:** CAB review by Cavus and Cassian, then the owner's GO.
**Question:** do free, public, no-login award sources already carry a supplier CIPC registration number (`YYYY/NNNNNN/NN`, which encodes the registration year only) or a CSD number (`MAAA…`), so that a "young supplier" indicator can be built without a CIPC login?

Times below are in SAST unless a source timestamp carries its own zone, in which case it is converted.

## How this survey was done

- Light, polite fetches only. No logins, no paywalls, no bulk crawling, no CIPC or CSD account.
- `robots.txt` was checked first where it exists. Paths that robots disallow (search, login, admin, and similar) were not fetched.
- The large eTenders OCDS corpus was not re-downloaded: the Open Contracting Partnership (OCP) `full.jsonl.gz` already held by PublicFunds (`/workspace/publicfunds/src/full.jsonl.gz`, PublicFunds fetch 19 Oct 2026 09:38 SAST; OCP last retrieved 20 Sep 2026) was analysed locally. One official monthly file (July 2026 JSON, 1.1 MB) and one City of Cape Town monthly PDF were fetched on 17 Nov 2026.
- Personal information was stripped from saved samples. Director ID numbers, addresses and contacts are not stored. See [POPIA](#popia-handling-of-samples).
- Where a fact was not opened or not present, the cell is **Unknown**.

## Verdict (short)

A public **awards register** is feasible. A **young-supplier indicator that does not need a CIPC login** is not feasible from the sources sampled.

| Corpus | Awards (or award-like rows) sampled | Supplier CIPC number present | Supplier CSD number present |
|---|---:|---:|---|
| OCP eTenders OCDS full mirror (`full.jsonl.gz`, 20 Sep 2026) | 9,551 award–supplier rows | **0 (0%)** | **11 (0.12%)** and only as messy text in the name field, not a structured field |
| Official monthly OCDS JSON for July 2026 (fetched 17 Nov 2026) | 42 awards | **0 (0%)** | **0 (0%)** |
| City of Cape Town October 2026 award register PDF | 24 unique tender references | **0 (0%)** | **0 (0%)** |

The only CIPC number in the entire OCDS mirror is Transnet SOC Ltd's own number `1990/000900/30`, appearing 59 times in *tender descriptions* (the buyer, not the supplier). CSD (`MAAA…`) strings appear more often in *tenderer* lists (194 releases; about 69 winning names could be joined to such a list) but a CSD number does not encode a registration year. The official OCDS API schema publishes `Identifier.legalName` only — no `scheme` or `id`.

**Implication:** public award data already give supplier name, a value (quality varies), a buyer, and a usable date (usually the release date or, where present, `contract.dateSigned`). They do not give the registration year. Reviving TenderWatch as a young-company flagger still depends on a free registration-year source, or on buyers starting to publish CIPC numbers. PublicFunds already ingests the best award source. TenderWatch should reuse or extend that ingest, not rebuild it. Details: [PublicFunds overlap](#overlap-with-publicfunds).

## Source table

| Source | URL (opened 17 Nov 2026 unless noted) | Format | Access | Terms / robots | Cadence | Supplier name | CIPC no. | CSD no. | Award date | Award value |
|---|---|---|---|---|---|---|---|---|---|---|
| eTenders OCDS bulk + API (OCPO / National Treasury) | https://data.etenders.gov.za/ ; monthly files at `/Home/ReleasesFiles` ; API https://ocds-api.etenders.gov.za/swagger/v1/swagger.json ; OCP mirror https://data.open-contracting.org/en/publication/143 | OCDS 1.1 JSON, CSV, XLSX; JSON REST API | Public, no login for data and downloads. Official and supplier logins exist on the portal and were not used. | No `robots.txt` on `data.etenders.gov.za` or `ocds-api.etenders.gov.za` (HTTP 404). Publication policy https://data.etenders.gov.za/Home/LearnMore : use, publish, republish with a link to the source. Homepage also says CC BY 4.0; API and OCP listing say PDDL (API licence URL is typo'd). **Unknown:** which licence National Treasury intends to be controlling. Privacy Statement PDF https://www.etenders.gov.za/files/Privacy%20Statement.pdf is a 6-page scan (created 13 Jul 2026); text could not be extracted. Policy says publication is POPIA-compliant and personal information of bidders/contractors is omitted unless consented. | Monthly bulk (files on the portal: Jan 2024–Jul 2026 as of 17 Nov 2026; July 2026 package `PublishedDate` 27 Aug 2026 17:25 SAST). OCP mirror retrieved monthly, last 20 Sep 2026. API is a delta source but is unstable (HTTP 500 observed 17 Nov 2026 on `/release/{ocid}`; PublicFunds INC-2026-001). | Yes (structured) | No (0% of winners). The one CIPC string in the corpus is the buyer's. | Almost never as a field. 0.12% of winner names in the mirror contain a `MAAA…` token; not usable as a year signal. | Release date usually; `award.date` typically empty; `contract.dateSigned` on a minority (1,691 contracts vs 9,551 awards in the mirror). | Usually present. 0 is a placeholder (PublicFunds). Some amounts look implausible; treat as untrusted. |
| eTenders portal "Awarded" tab | https://www.etenders.gov.za/Home/opportunities?id=2 (POST `/Home/AwardedTenders`) | HTML DataTable (JavaScript) | Public to view. Login is required only to bookmark or subscribe; not used. | No `robots.txt` (HTTP 404). Same privacy statement as above. | **Unknown** (UI claims a live awarded list; a 30 s POST for the table body timed out with 0 bytes on 17 Nov 2026). | **Unknown** (table body not retrieved) | **Unknown** | The UI has a "search by MAAA number" control. Whether awarded rows *display* a CSD number is **Unknown**. | **Unknown** | **Unknown** |
| Transparency Portal supplier / contract browsers | https://data.etenders.gov.za/Supplier ; `/Contract` ; `/Buyer` | HTML (rows appear to be loaded in the page; homepage counters on 17 Nov 2026: 73,785 awards*, 8,482 contracts*, 1,481,764 suppliers* — starred as a subset) | Public, no login | Same as the data portal. | Portal "Last Updated" 16–17 Nov 2026 on the homepage tiles. | Yes (supplier names are the point of `/Supplier`) | **Unknown** from the listing pages opened (no registration-number column was visible in the static HTML). | **Unknown** | **Unknown** | Contract values are shown on `/Contract` (2026 average was published on the page). |
| OCPO public site | https://ocpo.treasury.gov.za/ | HTML | Public pages. `/robots.txt` redirected and then returned HTTP 500 on 17 Nov 2026. | **Unknown** (terms page not opened; site error on robots). | **Unknown** | n/a (not an award register) | n/a | n/a | n/a | n/a |
| CSD public pages | https://secure.csd.gov.za/ | HTML application | Public: home, how to register, terms, restricted-supplier report. Full supplier search is for organs of state. **Logins and registration were not used.** | No `robots.txt` (HTTP 404). Terms: https://secure.csd.gov.za/Home/Terms (fetched 17 Nov 2026). Privacy statement is a download, not opened in full. Terms describe authorised access by organs of state to supplier information. | Restricted-supplier report is updated as entities are listed (PublicFunds already ingests the OCPO PDF). | Restricted-supplier report: yes | Restricted-supplier report: yes (this is a barred-supplier list, not an awards file) | **Unknown** on the public restricted report layout in this pass (PublicFunds already records RSR identifiers). | n/a | n/a |
| Government Gazette / GPW | https://www.gov.za/documents?category=government-gazette ; https://www.gpwonline.co.za/ | HTML; gazette PDFs | `www.gov.za` gazette listing is public. `www.gov.za/documents/gazettes` was 404; `www.gov.za/documents/government-gazettes` failed TLS from this host. GPW home is public; some gazette products historically need a subscription — **Unknown** whether a no-login award extract exists. | https://www.gov.za/robots.txt (200): allows general documents; disallows `/search/`, `/admin/`, `/user/login` and similar (those paths were not fetched). https://www.gpwonline.co.za/robots.txt : 404. | Gazettes are published continuously. Tender Bulletin cadence: **Unknown** in this pass. | **Unknown** (no award gazette sample opened) | **Unknown** | **Unknown** | **Unknown** | **Unknown** |
| Departmental award notices (Correctional Services sample) | https://www.dcs.gov.za/?page_id=199 | HTML + PDF attachments | Public. No `robots.txt` (404). | Copyright / POPIA pages exist on the site; detailed reuse terms **Unknown**. | Ad hoc | The tenders page on 17 Nov 2026 showed invitations, errata, bid-opening / bids-received PDFs and a cancellation notice. A systematic award-of-contract register with winner, date, value and CIPC/CSD was **not found** on that page. | Not found on the listing | Not found on the listing | Not found | Not found |
| Metro award notices — City of Cape Town | https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/tenders-rfqs-and-supply/tenders-awarded/ ; Oct 2026 PDF https://www.capetown.gov.za/media/nb1fgwta/tenders-awarded-october-2026.pdf | Monthly PDF registers (CCT and a DHL series) | Public, no login | https://www.capetown.gov.za/robots.txt : `User-agent: *` / `Allow: /`. Site terms **Unknown** (not opened). | Monthly (Jan–Oct 2026 registers were linked on 17 Nov 2026) | Yes (`Vendor`) | No (0 in the Oct 2026 register) | No (0 in the Oct 2026 register) | Yes (`Date of decision`). Published as `M/D/YYYY`. | Not in the Oct 2026 register. Some earlier months in the same series (e.g. Oct 2025) do have a value column — coverage is inconsistent. |
| Metro award notices — City of Johannesburg | https://joburg.org.za/work_/Pages/Work%20in%20Joburg/Tenders%20and%20Quotations/Tenders-and-Quotations.aspx | SharePoint HTML (JavaScript-heavy) | Public page. Links include bid opening registers, current/closed/cancelled proposals, Non-Awards, Public Adjudication Notices, Acquisition Status Reports. | `robots.txt` 404 (redirects to a SharePoint not-found page). Terms/privacy links exist; not opened. | **Unknown** | **Unknown** (adjudication notices were not opened in this light pass) | **Unknown** | **Unknown** | **Unknown** | **Unknown** |
| Provincial treasury — Western Cape | https://www.westerncape.gov.za/tenders points to eTenders and to https://www.westerncape.gov.za/provincial-treasury/tenders/advertised-cancelled-and-awarded-tenders | HTML | The provincial-treasury awarded-tenders URL returned **HTTP 404** on 17 Nov 2026. | https://www.westerncape.gov.za/robots.txt : disallows `/search/`, `/admin/`, `/user/login` (not fetched). Public tenders path is allowed. | **Unknown** | **Unknown** (destination 404) | **Unknown** | **Unknown** | **Unknown** | **Unknown** |
| AGSA reports | https://www.agsa.co.za/reports ; https://mfma-2025.agsa.co.za/ | HTML, PDF, occasional Excel annexures | Public. `www.agsa.co.za/robots.txt` 404. `mfma-2025.agsa.co.za/robots.txt` : `User-agent: *` / `Disallow:` (empty). | Reuse terms: **Unknown** in this pass (PublicFunds already treats AGSA as a public source). | Annual (PFMA / MFMA general reports) | Sometimes, when a finding names a supplier | **Unknown** (not a systematic award register) | **Unknown** | Finding period, not an award date | Irregular amounts in annexures, not award values |
| `www.gov.za` awarded-tenders hub | https://www.gov.za/awarded-tenders | HTML directory of departmental award pages | Public | Same `www.gov.za` robots as above | **Unknown** / stale: many departmental hrefs look historic | Depends on each department | **Unknown** | **Unknown** | **Unknown** | **Unknown** |
| CIPC company register (out of scope; recorded for completeness) | https://www.cipc.co.za/ | Web search / paid products | Login or paid search. **Not used.** | `robots.txt` 404. | n/a | n/a | This is the registration-year source the idea note cannot use without a GO for a login. | n/a | n/a | n/a |

\*Transparency Portal counters are the portal's own, 17 Nov 2026. They are much larger than the OCP compiled mirror (9,551 awards). PublicFunds' landscape (19 Oct 2026) already noted this gap (portal then claimed 70,873 awards). The official monthly files do not close it on their own: the July 2026 JSON held 849 releases and only 42 awards.

## 1. National Treasury eTenders / OCPO OCDS (recommended source)

### 1.1 URLs

| Role | URL | Opened |
|---|---|---|
| Transparency Portal | https://data.etenders.gov.za/ | 17 Nov 2026, HTTP 200 |
| Monthly bulk listing | https://data.etenders.gov.za/Home/ReleasesFiles (file list via `/Home/GetFiles`) | 17 Nov 2026, 31 months: Jan 2024–Jul 2026 as `01MMYYYY.{json,csv,xlsx}` |
| Publication policy / "Learn more" | https://data.etenders.gov.za/Home/LearnMore | 17 Nov 2026 |
| OCDS API spec | https://ocds-api.etenders.gov.za/swagger/v1/swagger.json | 17 Nov 2026, HTTP 200. The Swagger UI paths `/swagger/` and `/swagger/index.html` returned 404. |
| OCDS API releases | `GET https://ocds-api.etenders.gov.za/api/OCDSReleases` (page/size/date window) and `GET …/api/OCDSReleases/release/{ocid}` | Single-release fetch for `ocds-9t57fa-100167` returned HTTP 500 on 17 Nov 2026. PublicFunds already uses the list endpoint as a delta, with known timeouts/500s (INC-2026-001). |
| OCP registry mirror | https://data.open-contracting.org/en/publication/143 and `…/download?name=full.jsonl.gz` | Publication page opened 17 Nov 2026. Corpus analysed from the PublicFunds copy (fetched 19 Oct 2026 09:38 SAST). OCP page: data range Feb 2017–Sep 2026; last retrieved 20 Sep 2026; licence PDDL; publication policy points at LearnMore. `robots.txt` on `data.open-contracting.org`: `User-agent: *` / `Disallow:` (empty). |
| eTenders opportunities / Awarded tab | https://www.etenders.gov.za/ ; `/Home/opportunities?id=2` | 17 Nov 2026, HTTP 200. Awarded-table POST timed out. |
| Privacy Statement | https://www.etenders.gov.za/files/Privacy%20Statement.pdf | 17 Nov 2026, 201,267 bytes, 6 scanned pages. Text extraction failed. |

### 1.2 Fields actually present

From the OCP compiled mirror (35,309 releases, 9,551 awards, 488 buyers with awards) and the official July 2026 monthly JSON (849 releases, 42 awards):

| Field | Present? | Notes |
|---|---|---|
| Supplier name | Yes | `awards.suppliers.name` / monthly `Name`. Award `title` is often a copy of the name. |
| Supplier id | Internal only | Numeric portal ids, frequently `0` (3,575 of 9,551 in the mirror; July 2026 uses `SupplierID: 0`). Not a CIPC or CSD number. |
| Party `identifier` | `legalName` only | Official API schema (`Identifier`) exposes only `legalName`. No `scheme`, no `id`. |
| CIPC registration number | No, for suppliers | 0/9,551 winners. 56 releases match `YYYY/NNNNNN/NN`; every unique number is Transnet's `1990/000900/30` in `tender.description`. |
| CSD number | Almost never | 0 structured field. 11/9,551 winner names contain `MAAA…` (0.12%), often with value 0 and a polluted name/title. 208 award releases contain a `MAAA…` somewhere, mostly in `tender.tenderers.name`. About 69 winners can be name-matched to such a tenderer (~0.7%). A CSD number does **not** encode registration year. |
| Award date | Proxy | `awards.date` is typically empty (0/9,551 in the mirror; 0/42 in July 2026). Use `contracts.dateSigned` when present (1,691 contracts in the mirror) else `release.date`. PublicFunds already records this as `award_date_basis`. |
| Award value | Usually | All 9,551 mirror awards and all 42 July awards have a `value.amount` + `ZAR`. PublicFunds treats 0 as a placeholder and flags implausible lows/highs. Some published amounts are very large; do not treat them as audited rands. |
| Buyer name / id | Yes | 488 distinct buyers with awards in the mirror. City of Cape Town: 291 awards (a clean pilot set). |
| Tender title, method, documents | Yes | Document URLs point at `https://www.etenders.gov.za/home/Download?blobName=…`. |
| Contact / address | Present in the schema and often in the payload | `tender.contactPerson` (name + telephone) and `parties.contactPoint` (name, email, telephone, fax, url) exist. PublicFunds already drops contact persons. **Do not store these.** In the mirror, `parties.address` was `countryName` only, but the schema also allows street, locality and postal code. |

July 2026 official CSV is a poor serialisation of the same data (shifted columns, `System.Collections.Generic.List\`1[System.String]` in the `tag` field). Prefer JSON.

LearnMore still says bulk data start in May 2021 / 1 April 2022, but `/Home/GetFiles` on 17 Nov 2026 only listed January 2024–July 2026 (31 months). A probe of `01012022.csv` returned HTTP 500. **Unknown:** whether earlier months will return.

### 1.3 Sample award rows (evidence)

Full files with source URL and fetch date: `data/samples/etenders-ocds/`. Three rows from the OCP mirror (City of Cape Town; PublicFunds copy fetched 19 Oct 2026 09:38 SAST):

| ocid | Release date | Buyer | Supplier | Value.amount (as published, ZAR) | CIPC | CSD |
|---|---|---|---|---:|---|---|
| ocds-9t57fa-100167 | 2024-08-30 | City of Cape Town | CAPE AUTOMATION SYSTEMS | 1,981,222,875 | none | none |
| ocds-9t57fa-100171 | 2024-08-30 | City of Cape Town | BLOEMHOF ELECTRICAL | 5,356,639,625 | none | none |
| ocds-9t57fa-100172 | 2024-08-30 | City of Cape Town | F L O SPECIALIZED PRODUCT SOLUTIONS | 138,000,000 | none | none |

Three rows from the official July 2026 monthly JSON (fetched 17 Nov 2026 10:58 SAST; package published 27 Aug 2026 17:25 SAST):

| ocid | Release date | Buyer | Supplier | Value.amount (as published, ZAR) | CIPC | CSD |
|---|---|---|---|---:|---|---|
| ocds-9t57fa-163705 | 2026-07-28 | Special Investigation Unit | CHARTERED GOVERNANCE INSTITUTE OF SOUTHERN AFRICA | 3,854,946 | none | none |
| ocds-9t57fa-165162 | 2026-07-28 | Council for Scientific and Industrial Research (CSIR) | A AND SONS PROPERTY GROUP | 3,450,000 | none | none |
| ocds-9t57fa-165884 | 2026-07-28 | Mine Health and Safety Council | MAHUMA GROUP | 2,777,812 | none | none |

## 2. OCPO / CSD public pages

- CSD home (17 Nov 2026): https://secure.csd.gov.za/ — self-registration and login for suppliers; "Am I Restricted?"; current Restricted Supplier & Tender Defaulter report; 1,464,224 "verified suppliers" displayed on the homepage. This is not a public award database and not a public company-age database.
- Terms (https://secure.csd.gov.za/Home/Terms) describe access to supplier information by authorised users of organs of state. No public bulk dump of CSD numbers or registration dates was found.
- The Register of Restricted Suppliers **does** carry identifiers, including CIPC numbers, and is already ingested by PublicFunds (`ocpo.treasury.gov.za` PDF / CSD report). It is a barred-supplier list, not an awards file. Useful later for a "barred and awarded" check (PublicFunds detector D3 / landscape item 3), not for the young-supplier signal.
- OCPO homepage https://ocpo.treasury.gov.za/ opened (HTTP 200) after `/robots.txt` failed with HTTP 500.

## 3. Government Gazette

Opened: https://www.gov.za/documents?category=government-gazette (200) and https://www.gpwonline.co.za/ (200). A historic Tender Bulletin and occasional award or bid-outcome notices may appear in gazettes, but this pass did not open a gazette PDF, so field coverage is **Unknown**. The Gazette is a poor primary pipeline for a metro pilot (unstructured, not a complete award register). Keep it as a possible corroborating source, not the DEV ingest.

## 4. Departmental and municipal award notices (samples)

### 4.1 Department of Correctional Services

https://www.dcs.gov.za/?page_id=199 (17 Nov 2026). The page is an opportunities board: bid invitations, errata, bid-opening and bids-received PDFs, one cancellation notice. No award register with winner / date / value / CIPC or CSD was found on the listing. **Unknown** whether awards are published elsewhere on the site.

### 4.2 City of Cape Town (pilot buyer candidate)

https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/tenders-rfqs-and-supply/tenders-awarded/ links monthly "CCT tenders awarded" and some "DHL" registers for 2026 (January–October were listed on 17 Nov 2026).

The October 2026 register (https://www.capetown.gov.za/media/nb1fgwta/tenders-awarded-october-2026.pdf, fetched 17 Nov 2026 10:57 SAST, 433,074 bytes) has columns:

`TTS Reference | Decision Reference | Description | Vendor | Date of decision`

No value column in this month. Zero CIPC numbers and zero CSD numbers in the extracted text (24 unique tender-style references). Date strings such as `10/5/2026` are `M/D/YYYY` (the June 2026 file in the same series uses `6/15/2026`).

Sample rows (juristic names only; see `data/samples/city-of-cape-town/`):

| TTS ref | Decision | Vendor | Date of decision (as published / interpreted) | Value | CIPC | CSD |
|---|---|---|---|---|---|---|
| 016S/2026/27 | SCMB 13/10/26 | Octopus Electronics (Pty) Ltd. | 10/5/2026 / 2026-10-05 | not in this file | none | none |
| 172S/2025/26 | SCMB 14/10/26 | Printegration CC | 10/5/2026 / 2026-10-05 | not in this file | none | none |
| 293C/2024/25 | SCMB 25/10/26 | Zutari (Pty) Ltd. | 10/12/2026 / 2026-10-12 | not in this file | none | none |

Some City *contract* PDFs (not the monthly register) can contain a registration number — a 096S/2023/24 memorandum found via search quotes `2004/009201/07` — but those documents also carry addresses and signatory details and are out of scope for a light, POPIA-safe pilot ingest.

The City's registers are a useful **second** source for the Cape Town pilot (name + decision date, sometimes value), not a replacement for OCDS, and they still do not provide registration year.

### 4.3 City of Johannesburg

The tenders and quotations page lists bid opening registers, current/closed/cancelled proposals, Non-Awards, Public Adjudication Notices and Acquisition Status Reports. Those sub-pages were not opened in this light pass. Whether adjudication notices carry CIPC or CSD numbers is **Unknown**.

### 4.4 Western Cape Provincial Treasury

https://www.westerncape.gov.za/tenders directs readers to the national eTender portal and to a provincial "advertised, cancelled and awarded tenders" URL, which returned HTTP 404 on 17 Nov 2026. Field coverage: **Unknown**. Western Cape departments do appear as OCDS buyers (for example Western Cape - Health, Western Cape - Education in the mirror).

## 5. AGSA reports

https://www.agsa.co.za/reports and the MFMA 2024-25 microsite https://mfma-2025.agsa.co.za/ are public. They are audit findings and annexures, not a complete award feed. PublicFunds already ingests AGSA PFMA/MFMA material. Useful later as a *corroborating* official source for fact labels (Confirmed), not as the DEV award ingest. Whether annexures routinely carry CIPC numbers is **Unknown**.

## Overlap with PublicFunds

Repo: `/workspace/publicfunds` (GitHub `GrokForum/publicfunds-sa`, public site https://publicfunds.grokforum.site/).

PublicFunds already:

- Registers `etenders_ocds` in `config/sources.yaml` (bulk from the OCP mirror + API delta; licence note already flags the PDDL / CC BY 4.0 inconsistency).
- Implements the connector in `thusa/connectors/ocds.py` and the parser in `thusa/parsers.py` (`ocds_release_rows` already drops contact persons).
- Builds `curated.award` (`thusa/models/curated/060_award.sql`) with supplier name, internal supplier id, value (cents, with quality notes), award date and date basis, buyer, tender title, method, documents and source hashes.
- Knows the CIPC number format (`classify_identifier` in `thusa/normalise.py`) and matches restricted suppliers on registration number when the RSR provides one (ADR-0006: registration number first, then normalised name, then probabilistic match in a later phase).
- States, in ADR-0006 and the landscape report, that **CSD supplier numbers and directors are not public**, and that OCDS / PPD generally lack registration numbers.

PublicFunds does **not** have a young-supplier / registration-year detector, because the award feed does not carry the year.

**Recommendation:** do not re-ingest eTenders from scratch. Reuse the PublicFunds OCDS connector, parser, value rules and award row shape (or depend on its warehouse). Add TenderWatch-specific fields (registration year, young-supplier indicator, fact labels, right-of-reply status) in this repo or as a PublicFunds extension — the owner should choose (see CHG-TW-001). A second, Cape Town-only parser for the monthly PDF registers would be new work, still without a registration year.

There is also an existing third-party site, tenderwatch.org, mentioned in the PublicFunds landscape (restricted-supplier matching). It is not this project. Any public name or domain for TenderWatch SA needs to stay distinct.

## POPIA handling of samples

- Saved samples live under `data/samples/` and contain only official public award fields: buyer, supplier *organisation* name, references, dates, published values, and explicit `null`/empty CIPC and CSD columns.
- Omitted: `parties.address`, `parties.contactPoint`, `tender.contactPerson`, director names, SA ID numbers, emails, phones, street addresses.
- Sole-trader "t/a" personal names that appear in some City registers were not copied.
- Temporary fetch copies under `/tmp/tw-fetch/` are working files, not part of the repo.

**POPIA check of this file and of `data/samples/`:** PASS. No ID numbers, addresses, phones, emails or private contacts. Company and organ-of-state names are from official public award records and are presented as source extracts, not as findings of wrongdoing.
