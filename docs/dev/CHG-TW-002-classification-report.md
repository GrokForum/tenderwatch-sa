# CHG-TW-002 DEV classification report

Environment: **DEV** (local box only). DEV run; publishes nothing. This report carries counts only: no supplier name, queued, held or confirmed.
Run: 2026-11-17 17:44 SAST (Africa/Johannesburg). Input: the 291 City of Cape Town award-supplier rows of the CHG-TW-001 DEV run
(OCDS SHA-256 `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225`, PublicFunds pin `de37f666c12d1d6b7a815860894af0372514ba7f`, read-only) and the
508 City register rows from the same run. No new network fetch.

## 1. Source-field check (done before building)

| Source | Field that carries the supplier name | Rows | Trailing legal suffix | Any legal-form word |
|---|---|---|---|---|
| eTenders OCDS (OCP mirror) | `awards[].suppliers[].name` (same string as `parties[].name` / `parties[].identifier.legalName`) | 291 | **2** | 2 |
| City of Cape Town monthly award register (PDF) | `Vendor` column, parsed to `supplier_name` | 507 named of 508 | **400** | 460 |

Checked in the raw pinned file: 291 supplier `parties[]` entries; `parties[].identifier.legalName` equals `parties[].name` (ignoring case) on 291 of them, and carries a trailing legal suffix on 2.

Plain reading:

* **The OCDS supplier name almost never carries a legal suffix** (2 of 291); 267 of the names are in capitals, and the raw `legalName` field is the same string, so it adds nothing. The OCDS name alone cannot confirm a legal form.
* **The City register `Vendor` column usually does carry a suffix** (400 of 507 rows end the legal name, i.e. the part before any `t/a`, with a suffix; the other rows with a legal word have it inside a multi-vendor line or on a wrapped PDF line).
* **But the two sources cover different periods.** The City register PDFs cover 2026-02, 2026-03, 2026-04, 2026-05, 2026-06, 2026-07, 2026-08, 2026-09, 2026-10; the OCDS Cape Town awards are from award years {2021: 35, 2022: 84, 2023: 52, 2024: 76, 2025: 44}. A City name can be used only where the two-detail rule links it to the award *with the normalised name agreeing*, which is why method 1 reaches only a minority of suppliers.
* Result: method 1 cannot reach high coverage on this data. The two-person queue is large. This is stated, not fudged.

## 2. Counts

| Status | Rows |
|---|---|
| `confirmed_juristic` | 66 |
| `check_queue` | 225 |
| **Total classified** | **291** of 291 input rows (no row unclassified, none hidden) |

Before (CHG-TW-001 rule): {'unknown': 289, 'juristic': 2}. After: {'unknown': 198, 'juristic': 66, 'natural_person': 27}.

### By method

| Method | Rows |
|---|---|
| `city_register_suffix` | 64 |
| `ocds_suffix` | 2 |

`city_register_suffix`: the City register name linked on name + buyer carries the suffix. `ocds_suffix`: the OCDS name itself carries it. `*_before_trading_as`: the suffix is on the legal name before `t/a`.
How the legal form was linked to the award (CHG-TW-001 §19: only a shared tender reference is a tight link):
| `same_record` | 2 |
| `tender_ref` | 5 |
| `name_and_buyer_only` | 59 |

Legal-form fact label: {'Reported': 59, 'Confirmed': 7}. A suffix taken from a City name linked on name + buyer only is labelled
**Reported**, not Confirmed: the City printed that suffix, but the link to the older OCDS award is a name-only match within one buyer.

Confirmed rows where some City spellings of the same name lacked a suffix (noted, not queued): 0.

### By sub-type

| Sub-type | Rows |
|---|---|
| `company` | 56 |
| `close_corporation` | 8 |
| `npc` | 0 |
| `soc` | 0 |
| `trust` | 0 |
| `jv` | 1 |
| `other_juristic` | 1 |

### Queue by reason

| Reason | Rows | of which `popia_hold` | not held |
|---|---|---|---|
| `looks_like_personal_name` | 27 | 27 | 0 |
| `trust_personal_name` | 0 | 0 | 0 |
| `name_mismatch_between_sources` | 6 | 0 | 6 |
| `ambiguous_suffix` | 0 | 0 | 0 |
| `no_suffix` | 192 | 0 | 192 |
| `empty_name` | 0 | 0 | 0 |

`trust_personal_name`: a trust whose stem is a family or person-style name ("<Surname> Trust", "The <Surname> Family Trust"); queued and held, never auto-confirmed.
`ambiguous_suffix` includes names with two or more legal-form names joined by and, &, /, comma, ';' or '+' (note `multiple_legal_entities`): 0 rows. A name ending in JV / Joint Venture stays a JV.

Distinct supplier names in the queue: 191.

### POPIA hold

`popia_hold` = true on **32** rows ({'check_queue': 27, 'confirmed_juristic': 5}). The rule is deliberately over-inclusive:
`t/a` without a legal suffix on the legal name, initials plus surname (alone or followed by business words, e.g. "<initial> <surname> and Associates"), a title, a trust with a family or person-style stem,
or a bare two-to-four-word name with no business word, digit or legal word. Many held names will turn out to be businesses;
the two-person check releases them. Held names are not written to this report or to any public file.
Of the confirmed rows, 5 are held because one of their source names looks personal; their status stays `confirmed_juristic` but the name is withheld until checked.

### Age indicator

Confirmed rows with a sourced CIPC registration year: **0**. Confirming a legal form does not supply a year,
so the indicator stays Unknown. Indicator counts: {'unknown': 291}; age bands: {'unknown': 291}.
A trust is registered with the Master of the High Court, not CIPC: its CIPC indicator stays Unknown unless a sourced year exists.

### Local public export (DEV, git-ignored)

291 rows written (= input, no silent hide); 61 carry a name (confirmed and not held).
Every named row carries `supplier_name_fact_label` next to the name: {'Reported': 54, 'Confirmed': 7}
(Reported = legal form from a City row linked on name + buyer only, CHG-TW-001 §19).
Queued rows keep their row, status and reason, with the name withheld until the two-person check.

## 3. Remaining list for the two-person check (225 rows)

The per-name list (row id, OCDS name, linked City names, reason, notes, `popia_hold`, sources) is written to the git-ignored local file
`data/local/check_queue.csv`; confirmed rows go to `data/local/confirmed_suppliers.csv`. Neither is committed: the repository is to be
open-sourced, so no committed file carries a queued or held supplier name. The two checkers work from the local file by row id.

## 4. Confirmed rows (66)

Counts are in section 2. 5 confirmed rows are held for POPIA.

Fact labels: award rows **Confirmed** as published by the source. Legal form **Confirmed** where the suffix is in the OCDS record itself or in a
City row that shares the tender reference; **Reported** where the City row is linked on name + buyer only. No link uses a registry number.
Registration year: **Unknown** unless sourced. `Right of reply: pending` on every row.
