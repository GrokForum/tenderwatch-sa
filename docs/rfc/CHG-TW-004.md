# CHG-TW-004 — A second independent detail: registration numbers from free public documents, owner CIPC lookups, and churn tracking

| Field | Value |
|---|---|
| Change | CHG-TW-004 |
| Type | RFC only (survey, measurement, design). No code, no data change, no build under this record. |
| Environment | DEV (records only) |
| Branch | Revision 7: `dev/CHG-TW-004-owner-answers`, from `origin/main` at `a644332620176db675e8fd9ff04c3bc9395c9f89` (PR #6 merge). Revisions 1–6: `dev/CHG-TW-004-second-detail-rfc`, on `origin/main` at `75acab22d260a896937e8ca78e491b3ac53de298` (PR #5 merge after the project lead's history rewrite of 17 Nov 2026; files byte-identical to the pre-rewrite merge `e87c6cb3`) |
| Rollback reference | Revision 7: `a644332620176db675e8fd9ff04c3bc9395c9f89`. Revisions 1–6: `75acab22d260a896937e8ca78e491b3ac53de298`; snapshot tag `snapshot-2026-11-17-pre-tw-pr5-rw` → `113432644a902aa7f7bd76af3cd299a5ff3a9bf8` |
| Author | the author (TenderWatch) |
| Reviewers | reviewer A (project lead), reviewer B |
| Basis | CHG-TW-003 §9.1 Q5 (decided by the project lead, confirmed by the owner): the next change is an RFC for a second independent detail from CIPC or CSD numbers in free public documents. Owner input on his own manual CIPC lookups, given in the author's chat on 17 Nov 2026 at 18:16 SAST (summarised in §4, not quoted). Revision 7: owner's answers, 17 Nov 2026 21:51 SAST, relayed by the project lead (§13.2). |
| Status | Revisions 1–6 merged via [PR #6](https://github.com/GrokForum/tenderwatch-sa/pull/6) (`a6443326`). Revision 7 records the owner's answers to §13 Q1–Q11 (relayed, §13.2) and the legal basis (§15); draft for CAB on its own pull request. Records only. New owner questions in §13.6. |

## 1. Summary

* **Free public documents almost never print a supplier's registration number on the award.** On the DEV data, **0 of 291** rows and **0 of 59** Reported rows can gain a CIPC or CSD detail from the free public documents already held (eTenders OCDS and nine City of Cape Town monthly award registers, Feb–Oct 2026). 2 of 291 releases (1 of the 59) contain a CSD token, but it belongs to a tenderer list and cannot be tied to the winner.
* **Owner CIPC lookups** are therefore the only practical source of a registration number and year. This RFC limits them to three fields (registration number, registration date, status), ranks a short list by value, and sets how a lookup becomes Confirmed.
* **A lookup alone does not upgrade a Reported link.** It confirms the entity behind the City name; the City-to-award link still needs a second independent detail (CHG-TW-001 §5, CHG-TW-003 §6). On today's data, lookups give a Confirmed registration year on at most **6** award rows (6 eligible entities whose links are already Confirmed; the seventh Confirmed-link entity is a JV and is excluded); the other **39** eligible entities (behind 54 of the 59 Reported rows; the other 5 are held) would carry a year labelled Reported.
* **CIPC's terms restrict reuse** of what is seen on its site (§4.6). The public output would carry only the derived registration year and our label, and this RFC recommended holding even that until the owner clears the terms. The owner has since decided to publish the year with its label (§13.2, Q1); the terms point is unchanged.
* **City data:** the link-only rule (City option (i), §13.1) is superseded by the owner's answer "Public data is public data, act accordingly" (§13.2): City register facts may be published, cited to the City document, on a site labelled DRAFT. Knock-on in §13.5.
* **Owner answers and legal basis (revision 7):** §13.2–§13.6 record the answers, a proposal for the 192 bare-name rows and a neutral indicator list; §15 quotes the verified provisions (Companies Act ss11(3), 32(4), 186, 187; Companies Regulations, 2011, regs 174 and 177).
* **Churn indicators** are defined as private working notes for the owner only (§7).

## 2. Scope

In scope (design only): (1) a survey of free public documents that might print CIPC (`YYYY/NNNNNN/NN`) or CSD (`MAAA…`) numbers, with access rules; (2) owner CIPC lookups: fields, ranking, batch, template, labels and terms; (3) snapshots and churn indicators; a POPIA check for one-person businesses; how the age indicator gets its sourced year; data model, tests, risks, rollback and owner questions.

Out of scope: any build; any use of the owner's CIPC login by the bot; any automated query of CIPC or CSD; any message to CIPC or a supplier; TEST, PROD and the public site.

## 3. Part 1 — Free public documents: what prints a registration number

All links opened or re-checked on **17 Nov 2026**. Labels: **Confirmed** = seen in the source or measured on the data; **Reported** = stated by the publisher or by an earlier survey, not re-measured here; **Unknown** = not established. "Link" means cite the URL and do not copy the file; "scrape" means automated download is acceptable within the stated rules.

| # | Source | Prints supplier CIPC / CSD on the award? | Label | robots.txt (17 Nov 2026) | Terms | Link or scrape |
|---|---|---|---|---|---|---|
| S1 | eTenders OCDS bulk and API — https://data.etenders.gov.za/ ; https://ocds-api.etenders.gov.za/ ; OCP mirror https://data.open-contracting.org/en/publication/143 | CIPC: 0 of 9,551 winners. CSD: 11 of 9,551 winner names contain a `MAAA` token, no field. (`SOURCES.md`) | Confirmed (measured) | None (HTTP 404 on all three eTenders hosts) | Data "licensed under Creative Commons BY 4.0" (data.etenders.gov.za home page); OCP mirror licence PDDL | Scrape (bulk download with attribution; already reused via the PublicFunds pin) |
| S2 | OCDS tenderer lists (bid-opening data inside the same releases) | 194 award-releases carry a CSD token in `tender.tenderers`; 68 of 9,551 award rows (0.71%) join a CSD-bearing tenderer to the winner (`SOURCES.md`) | Confirmed (measured) | As S1 | As S1 | Scrape (same files) |
| S3 | eTenders bid documents (PDF), e.g. https://www.etenders.gov.za/home/Download/?blobName=a53d7e4d-77da-41c3-9bdb-03bf515f53ad.pdf&downloadedFileName=COM02-2026+SUPPLY+AND+DELIVERY+OF+HIGH+DENSITY+REFUSE+BAGS+FOR+CITY+OF+MBOMBELA.pdf | No. Bid documents are blank forms issued before award ("CSD REG NO: MAAA___"); they never name the winner. They do print officials' names, phones and emails. | Confirmed (two documents read) | None (404) | No reuse terms found on the portal (privacy statement only): Unknown | Link only; do not store (contact details) |
| S4 | eTenders portal "Awarded" tab — https://www.etenders.gov.za/Home/opportunities?id=2 | Same records as S1 in HTML | Reported | None (404) | Unknown | Link only (S1 is the sanctioned bulk route) |
| S5 | CSD public pages — https://secure.csd.gov.za/ ; terms https://secure.csd.gov.za/Home/Terms | Supplier search is for organs of state. Terms §2.7.1: institutional users "may not disclose the supplier information to any person" except as an organ of state instructs. No public bulk data. | Confirmed (terms read) | None (404) | Restrictive (above) | Neither; not a source for this change |
| S6 | OCPO Register of Restricted Suppliers (public PDF/report via https://ocpo.treasury.gov.za/ and CSD) | Carries identifiers, including CIPC numbers, for **barred** suppliers only (`SOURCES.md` §2) | Reported | `ocpo.treasury.gov.za/robots.txt` HTTP 500 | Unknown | Link; usable only as a barred-and-awarded check, not a general detail |
| S7 | City of Cape Town monthly award registers — https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/tenders-rfqs-and-supply/tenders-awarded/ | **0** CIPC and **0** CSD numbers in all nine 2026 PDFs held (Feb–Oct); no registration column | Confirmed (measured 17 Nov 2026) | `User-agent: * / Allow: /` | Copyright © City of Cape Town (https://www.capetown.gov.za/general/terms-of-use/, retrieved 17 Nov 2026): redistribution or reproduction is prohibited except (a) printing or downloading extracts to a local disk for personal, non-commercial use, and (b) copying the content to individual third parties for their personal use, if the City's website is acknowledged as the source. Any other distribution or commercial use needs the City's **express written permission**, with enquiries to the City webmaster; each permitted reference must acknowledge that the information resides at and is the property of the City of Cape Town. Unless otherwise specified, URL references for non-commercial purposes are permitted on the condition that each acknowledges that the information resides at and is the property of the City of Cape Town. Confirmed. | **Link only** (owner decision, City option (i), §13.1): cite the City URL with that acknowledgement, and carry no City-derived facts in the public output. Local downloads for DEV analysis only. Superseded by the owner's answer to Q10/Q11 (§13.2): City facts may be published, cited to the City document |
| S8 | Other metros: Johannesburg (https://joburg.org.za/), eThekwini supplier portal "Awarded Tenders" (https://ethekwinisupplierportal.durban.gov.za/) | Not opened in this pass | Unknown | joburg.org.za: 404; durban.gov.za: fetch failed | Unknown | Link only until surveyed |
| S9 | Departmental lists — www.gov.za awarded-tenders hub (https://www.gov.za/awarded-tenders); Correctional Services sample (https://www.dcs.gov.za/?page_id=199) | DCS page showed invitations and bid-opening lists, no award register; hub links look historic (`SOURCES.md`) | Unknown | www.gov.za: fetch failed today; dcs.gov.za: 404 | Unknown | Link only |
| S10 | Government Gazette — https://www.gpwonline.co.za/ ; https://www.gov.za/documents?category=government-gazette ; mirror https://gazettes.africa/ | No gazette PDF opened; whether award notices print registration numbers is not known | Unknown | gpwonline: 404; gazettes.africa: content-signal robots with terms | Unknown (GPW); gazettes.africa terms at /terms-of-use/ | Link only |
| S11 | AGSA reports — https://www.agsa.co.za/reports | Audit findings and annexures, not an award feed | Reported | www.agsa.co.za: 404 | Copyright page exists, not read: Unknown | Link; corroboration only |
| S12 | CIPC site and e-services — https://www.cipc.co.za/ ; https://eservices.cipc.co.za/ | Enterprise search and disclosures need a customer login | Confirmed | cipc.co.za: 404; eservices: disallows Bingbot only | Terms §3(c) bar "any technology to search and gain any information from this site without the prior written permission of CIPC"; §4 below | **Never scrape.** Manual owner lookups only (§4) |

**Measurement on DEV data (counts only).**

| Measure | All 291 rows | 59 Reported rows |
|---|---|---|
| Supplier CIPC number in the OCDS release | 0 | 0 |
| CSD token anywhere in the OCDS release | 2 | 1 |
| CSD token tied to the winner (winner field, or a tenderer whose folded name equals the winner) | 0 | 0 |
| CIPC or CSD number in the linked City register rows (508 rows, 9 PDFs) | 0 | 0 |
| **Rows that can gain a second detail from free public documents held today** | **0** | **0** |

So part 1, on its own, adds nothing today. It stays worth a cheap periodic check (S2 tenderer joins, S8 metros, S10 gazettes), but the realistic second detail now is an owner lookup.

## 4. Part 2 — Owner CIPC lookups

### 4.1 Rules (owner input, 17 Nov 2026 18:16 SAST, author's chat)

* The owner has a CIPC login as a company owner and does manual lookups himself. **The bot never uses, asks for, stores or automates that login.** No automated CIPC query of any kind (S12 terms §3(c)).
* A lookup records **only** three facts about the enterprise: **registration number**, **registration date**, **status** (as CIPC shows it, e.g. in business, deregistration process, final deregistration). Never director or member names, ID numbers, addresses, contact details, or any other CIPC field.
* Each lookup carries the source `owner CIPC lookup` and the lookup date.
* A lookup's link to an award is labelled **Confirmed only once the two-detail rule holds** (§5).

### 4.2 Who goes on the list (eligibility)

* Only entities with a **registered name from a source** (a statutory suffix printed by the City or OCDS, CHG-TW-002 `confirmed_juristic`). On DEV that is **49** distinct registered names.
* **Excluded:** POPIA-held names (3 of the 49), queue rows (personal-looking, trust, mismatch, no suffix), trusts (Master's Office, not CIPC), JVs and multi-entity names. A bare name with no suffix (192 queue rows) is not looked up: a name search on a bare name is ambiguous and could surface the wrong entity (§13 Q6).
* **Eligible on DEV: 45 entities** (6 with an already-Confirmed link, 39 Reported). Of the 49, 3 are held and 1 is a JV (its link is Confirmed), so 49 − 3 − 1 = 45.

### 4.3 Ranking (value per minute of the owner's time)

Score each eligible entity and take the highest first. The counts below are reproduced by `scripts/count_chg_tw_004_lookup_pool.py` (counts only; its output is committed as `scripts/count_chg_tw_004_lookup_pool.out.json`).

| Factor | Points | Why |
|---|---|---|
| Award value at the buyer (see method below) | at or above Q75: 3; at or above Q50 and below Q75: 2; above 0 and below Q50: 1; missing: 0 | Larger public spend first |
| Young-company **candidate** (internal proxy; rule below) | 3 | The age indicator matters most here; the proxy is weak and never published |
| Buyer concentration (3 or more of the 291 award rows at the buyer) | 2 | Repeat winners at one buyer |
| Link already Confirmed | 2 | The year becomes Confirmed at once (§5) |
| Link Reported | 1 | The lookup is one detail of two; still useful for checks |

**Method (exact).**

* *Entity:* one distinct registered `legal_name` among CHG-TW-002 `confirmed_juristic` rows. It is excluded if any of its rows is held, has sub-type JV or trust, or is a multi-entity name. Its link is Confirmed if any of its rows has a Confirmed link.
* *Value:* the sum of `value_amount` over the entity's rows whose `value_note` is empty. Rows marked `zero_placeholder`, `implausible_high` or `implausible_low`, and rows with no amount, count as missing. An entity whose rows are all missing scores 0 and is left out of the quartile set.
* *Quartiles:* the quartile set is the list V of the positive entity values of the 45 eligible entities, **sorted ascending**, with duplicates kept. Cut points use the lower nearest-rank rule with no interpolation: Q(p) = V[floor(p × (n − 1))], used for p = 0.50 and 0.75. A value equal to a cut point takes the higher band. There is no separate bottom-quartile band: every positive value below Q50 scores 1.
* *Young-company rule:* first_seen is the earliest OCDS release `date` in the pinned eTenders file (SHA-256 `a2849a63…5225`) of any release whose award supplier name has the same `norm_name` as one of the entity's supplier names. The entity is a candidate only if both dates are known, first_seen is on or after 2022-06-01, **and** its earliest award date is 0 to 365 days after first_seen (a first_seen later than the award is not young).
* *Date parsing (strict):* a date must be `YYYY-MM-DD`, optionally followed by a `T` time that ends in `Z`, in a `±HH:MM` offset (converted to UTC before the date is taken), or in nothing (bare time; the written date is kept). Any other shape (e.g. `20240101`, `2024-W01-1`, trailing text) and any invalid calendar date is unknown. The whole string must match (a trailing newline is rejected), digits must be ASCII, `-00:00` counts as UTC, and the end-of-day form `24:00` is unknown. The pinned eTenders file uses only `YYYY-MM-DDTHH:MM:SSZ` for release dates (35,309 of 35,309); `awards[].date` is empty in all 9,551 award entries; the warehouse `award_date` is a plain `YYYY-MM-DD` (291 of 291).
* *Why the UTC calendar day:* the pinned eTenders source gives every release date in UTC (`Z`), so taking the UTC day gives one consistent calendar for all dates rather than mixing UTC and SAST days. As a result, `2022-06-01T00:30+02:00` (00:30 SAST on 1 June) falls on 2022-05-31 UTC and is before the young-company cut-off.
* *Unknown dates:* a missing or placeholder date (empty, any shape other than the above, 9999-12-31, 1900-01-01, 1970-01-01, 0001-01-01, or a year outside 1990–2099; `tw/lookup_pool.py`) is never filled in. It scores **0** young points, and an unknown earliest award date sorts last in the batch order. On the DEV data: **0** entities (0 rows) have an unknown first-seen date; **0** entities (0 rows) have an unknown earliest award date; **0** entities have a first-seen date after their earliest award.
* *Batch order (tie-break):* score descending, then value descending, then number of rows descending, then earliest award date ascending, then smallest internal award id: all-digit ids compare numerically ('9' before '10') and come before non-numeric ids, which compare as strings. An unknown award date or id sorts last. Batch 1 is the first 10.

**DEV result (counts only; script output, identical on two runs):** 45 eligible (6 Confirmed-link, 39 Reported); 30 with a usable value (value points: 3: 9, 2: 7, 1: 14, 0: 15); 23 young-company candidates; 4 with 3+ rows. Score spread: 7 pts: 4, 6: 5, 5: 11, 4: 12, 3: 4, 2: 1, 1: 8. **Batch 1 (top 10): 2 Confirmed-link and 8 Reported entities, 8 young-company candidates, 2 repeat winners, all 10 with a usable value; scores 7, 7, 7, 7, 6, 6, 6, 6, 6, 5.** Five batches of 10 cover all 45 (the fifth has 5).

*Note on the first draft:* its table said "top 3, second 2, third 1, none or unusable 0", which reads as giving the bottom quartile 0 points. The counts were in fact computed with the method above, where every positive value below Q50 scores 1, and the counts are unchanged. Only the wording was ambiguous.

*Note on revision 4 (reviewer B):* revision 3 of the script filled a missing first-seen date with 9999-12-31, and that fill passed the young-company test, so an unknown date would have scored as young. On the DEV data, no eligible entity has a missing or placeholder date, so no count changed. The fix in `tw/lookup_pool.py` is covered by `tests/test_lookup_pool.py`.

*Note on revision 5 (reviewer A):* the date parser is now strict and converts offsets to UTC, and award ids compare numerically when they are all digits. Two runs gave byte-identical output that matches the previous `.out.json`. No count changed, and the full batch order (including batch 1) is the same.

*Note on revision 6 (reviewer A):* the parser now uses a full-string match with ASCII-only digits (no trailing newline, no non-ASCII digits). Tests pin 24:00 as unknown, 2024-02-29 as kept, 2023-02-29 as unknown, `-00:00` as UTC, and the SAST-midnight example above. Two runs gave byte-identical output matching the committed `.out.json`; no count changed.

### 4.4 Batch and template

* **Batch size: 10.** The next batch is generated only after the previous one is returned.
* Template (git-ignored): `data/local/cipc_lookups/batch-YYYY-MM-DD.csv`, generated by a future build with these columns only:

| Column | Filled by | Content |
|---|---|---|
| `lookup_id` | build | Internal id |
| `rank`, `score` | build | From §4.3 |
| `name_to_search` | build | The registered name as printed by the source (local file only) |
| `cipc_reg_no` | owner | `YYYY/NNNNNN/NN` or blank |
| `registration_date` | owner | `YYYY-MM-DD` |
| `status` | owner | One of a fixed list (in business; deregistration process; final deregistration; business rescue; liquidation; other) |
| `result` | owner | `found` / `not_found` / `several_matches` |
| `lookup_date` | owner | `YYYY-MM-DD` |
| `source` | build | Fixed `owner CIPC lookup` |

No free-text column. The loader rejects any extra column, any 13-digit number, email, phone pattern or address-like text, so personal data cannot be pasted in by accident.

### 4.5 What a lookup feeds

* `registration_year` = the `YYYY` of `cipc_reg_no`; it must agree with the year of `registration_date`. If they disagree (for example after a conversion), the year stays Unknown and the row goes to the owner.
* A plausibility check: `registration_date` must be on or before the award date. If not, the name may have passed to a newer entity (CHG-TW-003 L10): the link is marked as a conflict and stays Reported, and a churn note is raised (§7).
* `status` is stored with its `lookup_date` for the churn snapshots; it is never published.

### 4.6 CIPC terms of use (finding)

CIPC Terms and Conditions (https://www.cipc.co.za/?page_id=11883, same text at https://eservices.cipc.co.za/TermsConditions.aspx; read 17 Nov 2026; no version date shown):

* §4(3): a visitor or customer "may not reproduce, duplicate, publish … display, or distribute or in any way exploit any of the contents". **Confirmed.**
* §4(4): content "can be used, transmitted or distributed for private or personal purposes". **Confirmed.**
* §4(5): business use only as part of a service to specified clients, limited to them. **Confirmed.**
* §4(6): permission requests in writing to CIPC Legal Services. **Confirmed.**
* §4(7): "strictly prohibited from creating works and/or software materials derived from or which are based on the contents found on this site". **Confirmed.**
* §3(c): no use of "any technology to search and gain any information" without written permission. **Confirmed.**
* CIPC's privacy page cites Companies Act s187(4)(c): CIPC must make the information in its registers efficiently available to the public (https://eservicese.cipc.co.za/privacy.aspx). **Reported** (not checked against the Act in this pass).
* Whether a registration **year**, as a bare fact derived from a lookup, is "content" under §4 or a "derived work" under §4(7): **Unknown**. No legal view has been taken.

**Consequence.** Until the owner clears the terms (written permission, or his own legal view), the public output never carries CIPC records, registration numbers from lookups, dates, statuses, or anything copied from a CIPC screen. This RFC goes one step further than the minimum: because §4(7) may reach derived facts, it recommends that even the derived year and age band stay internal until the owner decides (§13 Q1). If the owner allows it, the public output carries only `registration_year`, `age_band` and our label. Revision 7: the owner has decided to publish the year with its label (Q1) and to keep Reported age bands internal (Q2) (§13.2); §15 quotes s187(4)(c), which this section labelled Reported.

## 5. The two-detail rule for lookups

A lookup is evidence about an **entity**: the registered name with suffix and its number. It is one detail. Linking it to an **award** needs a chain in which every step is tight:

1. **Lookup → source row:** the CIPC name equals the source's registered name with suffix under CHG-TW-003 rule A normalisation (same stem, same canonical suffix, same RF flag, no `t/a`). This step confirms the entity behind the City row (or OCDS row).
2. **Source row → award:** already Confirmed (`same_record`, or `tender_ref` + buyer), **or** confirmed by another independent detail: a registration or CSD number printed in a public document tied to that award (part 1), or a later rule.
3. **No conflict:** registration date on or before the award date; status not final deregistration before the award (only knowable from a dated public notice, otherwise Unknown); no other entity found under the same name (`result` = `found`, not `several_matches`).

Labels: `registration_year_label` = Confirmed only when steps 1–3 hold. If step 2 is only a name-and-buyer link (the 59), the year is a Confirmed fact about the City entity but its use on the award is **Reported**. `registration_year_source` = `owner CIPC lookup YYYY-MM-DD` (internal), shown publicly (if allowed) as "registration year from a CIPC lookup".

**Effect on DEV if all 45 were looked up:** up to 6 award rows (the 6 eligible Confirmed links) could get a Confirmed year and age band; the 59 Reported rows stay Reported; no row changes its CHG-TW-002 status.

## 6. Age indicator: where the year comes from

Unchanged definition (CHG-TW-001 §6): `same` (registration year = award year), `-1`, `-2` (trend only), `older`, `unknown`; the young-supplier indicator is `yes` only for `same` and `-1`; computed only for juristic suppliers; a CSD number is never a year.

Source order for `registration_year`:

1. A CIPC number printed in a free public document tied to the award (part 1). Label per §5.
2. An owner CIPC lookup (§4), label per §5.
3. Otherwise `unknown`.

`age_band_label` is the weaker of the year label and the link label. Public display (if allowed, §13 Q1–Q2): `age_band` only when its label is Confirmed; a Reported age band stays internal and the public row shows `unknown`.

## 7. Part 3 — Snapshots, deregistration and churn (private)

### 7.1 Snapshots

Each refresh writes a dated snapshot under `data/local/snapshots/YYYY-MM-DD/` (git-ignored): per entity `name_key`, registered name, canonical suffix, `cipc_reg_no` and `registration_year` (if looked up), last known `status` with its `lookup_date`, buyer, award ids. Snapshots are append-only; the churn job compares the newest snapshot with all earlier ones.

### 7.2 Churn indicators (definitions)

| Id | Indicator | Fires when |
|---|---|---|
| C1 | Name reappears under a newer registration | The same normalised registered name is later seen with a **different** registration number whose year is later than the earlier one |
| C2 | Status change | A looked-up entity's status differs from its previous lookup (e.g. in business → deregistration process → final deregistration, or reinstatement) |
| C3 | Award after deregistration | An award date falls after a dated final-deregistration notice from a public source (status alone has no date and does not fire C3) |
| C4 | Young winners clustered at one buyer | 3 or more distinct entities with `age_band` `same` or `-1` win at one buyer within 365 days (threshold 3: owner's answer, §13.2) |
| C5 | Registration after award | `registration_date` is later than the award date (§4.5) |
| C6 | Name with two suffixes | A stem appears with two canonical suffixes across sources or snapshots (CHG-TW-003 Q4 conflict) |

### 7.3 Privacy of churn notes

* Churn flags are **private working notes for the owner** in `data/local/churn/` (git-ignored). They are **never published**, never written to the public export, and never placed next to a supplier name in any public data. Tests enforce this (§9).
* A churn flag is a prompt for the owner to look, not a finding about anyone.

## 8. POPIA

* **One-person businesses.** CIPC does not register sole proprietors, and a one-person company can carry a personal name. Rows that are personal-looking (CHG-TW-002 `looks_like_personal_name`, `trust_personal_name`, initials-and-surname names, or a personal name followed only by a suffix) are **held**: their details stay unpublished until the two-person check (CHG-TW-002), whatever a lookup shows. They are not put on the lookup list by default (§13 Q5). If the owner looks one up, the record still carries only number, date and status.
* **Never recorded from CIPC:** director or member names, ID numbers, dates of birth, addresses, phone numbers, emails. The template has no column for them and the loader rejects such patterns (§4.4).
* **Bid documents (S3)** print officials' contact details; they are linked, never stored.
* **Per-name files stay local.** Lookup batches, snapshots and churn notes are git-ignored; committed files carry counts only and invented examples.
* **No automated CIPC or CSD access**; no login used by the bot.

## 9. Test plan (invented names only)

* Loader accepts a valid row for "Qwertane Widget Supplies (Pty) Ltd": `2024/123456/07`, `2024-03-12`, in business, found, `2026-11-20`.
* Loader rejects: an extra column; a 13-digit number anywhere; an email; a phone number; address-like text; a status outside the fixed list; a malformed `cipc_reg_no`; a registration year that disagrees with `registration_date`.
* Two-detail: Confirmed link (`tender_ref`) + exact name with suffix → `registration_year_label` Confirmed, award 2025 → `age_band` `-1`, indicator `yes`.
* Reported link (name + buyer only) + lookup → year stored, `age_band_label` Reported, public row shows `unknown`.
* Name mismatch ("Zephyra Holdings (RF) (Pty) Ltd" in CIPC vs "Zephyra Holdings (Pty) Ltd" at the City) → no link, conflict noted.
* `several_matches` → no year.
* C5: registration date 2025-06-01, award 2025-03-01 → conflict, link stays Reported, churn note written locally.
* C1: "Testburg and Sons (Pty) Ltd" seen with `2015/…/07`, later with `2025/…/07` → C1 note.
* C2: status in business → final deregistration between two lookups → C2 note.
* C4: three invented young entities win at one buyer within 365 days → C4 note; two → none.
* Privacy: public export has no `cipc_reg_no`, `registration_date`, `status`, churn or score columns; no churn file is tracked by git; a held row ("J Q Testerman and Associates (Pty) Ltd") stays withheld after a lookup.
* Ranking: deterministic order on a fixture; batch size 10; held, trust, JV and bare-name rows never appear.
* Regression: DEV re-run over the 291 rows changes no CHG-TW-002 status; with no lookups loaded, every year stays `unknown`.

## 10. Data model and files (proposed)

* New git-ignored paths: `data/local/cipc_lookups/` (batches and returned files), `data/local/snapshots/YYYY-MM-DD/`, `data/local/churn/`.
* New internal fields on the classified award rows: `cipc_reg_no_source`, `registration_date` (internal), `cipc_status` + `cipc_status_seen_on` (internal), `registration_year_source`, `registration_year_label`, `age_band_label`, `lookup_conflict` (internal).
* Public export (only if allowed, §13 Q1): `registration_year`, `registration_year_label`, `age_band`, `age_band_label`. Nothing else from lookups.
* Code (future build): `tw/lookups.py` (template, loader, validation, ranking), `tw/churn.py` (snapshots and C1–C6), tests `tests/test_lookups.py`, `tests/test_churn.py`.

## 11. Risks and concerns

* **City copyright (S7).** The City's terms (https://www.capetown.gov.za/general/terms-of-use/, retrieved 17 Nov 2026) prohibit redistribution or reproduction of its content, except personal non-commercial extracts and copies to individual third parties for their personal use with the City's website acknowledged as the source. Anything else needs the City's express written permission (enquiries to the City webmaster). Non-commercial URL references are permitted only if each acknowledges that the information resides at and is the property of the City of Cape Town. The CHG-TW-001 public-site plan republished City-derived names and fields; the owner has since chosen City option (i) (§13.1): City data is link-only, and published facts come only from eTenders. A letter asking the City for permission is drafted for the owner to send himself; its outcome is pending. Revision 7: the owner has replaced link-only with "Public data is public data, act accordingly" (§13.2).
* **CIPC derived-works clause (§4.6).** Even a derived year may fall under §4(7). Recommendation: keep it internal until the owner decides.
* **Owner time.** 45 eligible entities ≈ 5 batches; returns may be slow. The ranking puts value first.
* **Weak young-company proxy.** "First seen on eTenders" reflects publication coverage, not company age. It is used only for ranking and never shown.
* **Name reuse and conversions.** A name can pass to a new entity (CHG-TW-003 L10); a converted close corporation may show a number year that differs from its company registration. Mitigation: §4.5 checks; conflicts stay Reported.
* **Status has no date.** A current status says little about the status at the award date; C3 fires only with a dated public notice.
* **Over-reading.** Age and churn are indicators, never findings; wording rules from CHG-TW-001 apply.

## 12. Rollback

RFC only: this commit changes `docs/rfc/CHG-TW-004.md` and `STATUS.md`. Before merge, delete the branch. After a merge, `git revert` the merge commit on a review branch, or reset a branch to `75acab22d260a896937e8ca78e491b3ac53de298`. Tag `snapshot-2026-11-17-pre-tw-pr5-rw` (`11343264`) is unchanged. For a future build: the lookup files, snapshots and churn notes are local and git-ignored; deleting them returns every year to `unknown`.

Revision 7 (records only) changes `docs/rfc/CHG-TW-004.md` and `STATUS.md` on `dev/CHG-TW-004-owner-answers`. Before merge, delete the branch; after a merge, `git revert` the merge commit on a review branch, or reset a branch to `a644332620176db675e8fd9ff04c3bc9395c9f89`. The City PDFs downloaded for the owner (§13.2) are outside the repository and are not part of any rollback.

## 13. Owner questions

1. **Publication of derived years:** keep the derived registration year and age band internal until CIPC's terms are cleared (recommended), or publish year + label now?
2. **Reported age bands:** keep them internal (recommended), or show them labelled Reported?
3. **Ranking weights (§4.3):** accept them, or put the 6 eligible Confirmed-link entities first so the first batch yields Confirmed years at once?
4. **Batch size:** 10, or another number?
5. **One-person businesses:** keep personal-looking names off the lookup list until the two-person check (recommended)?
6. **Bare names (192 no-suffix queue rows):** out of the lookup list (recommended), or allow the owner to search some by name?
7. **CIPC permission:** answered in §13.1 (a letter to CIPC Legal Services is drafted for the owner to send himself).
8. **C4 threshold:** 3 young winners at one buyer within 365 days, or another value?
9. **Periodic part-1 checks:** survey other metros (S8) and gazettes (S10) in a later records-only change?
10. **Local DEV reading of City registers under option (i):** may the City PDFs still be downloaded and read locally in DEV (never published) to find links and conflicts?
11. **Public legal form under link-only (knock-on of City option (i), §13.1).** What may the public export say about legal form while the City's permission is pending?
    *Recommendation:*
    * Internally, keep using City data for classification, the POPIA gate and lookup ranking.
    * In the public export, show only eTenders facts. For City-derived rows, show the eTenders supplier name with legal form "Unknown (pending source permission)" and a link to the City source document, carrying the acknowledgement the City's terms require.
    * Publish a confirmed legal form only for the 2 rows whose suffix eTenders itself prints, until the City replies.
    * Make no code change under this RFC; the export change needs its own CHG and GO.
    * One open point for the owner: whether to show an eTenders name at all when the only basis for treating it as a company (and so publishable under the POPIA gate) is a City fact the public cannot see. The safer reading is to show it, because the name is an eTenders fact, while the public row states plainly that the legal form is unconfirmed.

### 13.1 Decisions

* **City option (i), decided by the owner on 17 Nov 2026 at 20:07 SAST, relayed by the project lead.** City of Cape Town data is **link-only**: the public output cites City URLs with the acknowledgement the City's terms require and carries no City-derived facts. Published facts come only from eTenders (CC BY 4.0). The author reads this as still allowing City registers to be read locally in DEV to find links and conflicts (owner to confirm, §13 Q10). **Superseded** by the owner's answer to Q10/Q11 (17 Nov 2026 21:51 SAST, relayed; §13.2).
* **Two letters**, one to the City of Cape Town (permission to reuse its award registers) and one to CIPC Legal Services (reuse of information seen on its site), are drafted for the owner to send himself. They are not part of this repository. **Outcome: pending.**
* **Knock-on of option (i)** (as measured under link-only; recomputed in §13.5) (verified by `scripts/count_chg_tw_004_lookup_pool.py`):
  * 64 of the 66 CHG-TW-002 confirmed legal-form rows take their suffix and legal name from the City register; only 2 take them from eTenders (OCDS).
  * All 59 Reported links are City-derived.
  * Of the 45 eligible lookup entities, 44 have a City-derived registered name and 1 an eTenders-derived one.
  * Under link-only, the public export could name only the **2 OCDS-suffix rows** as confirmed legal entities until the City grants permission (§13 Q11).
* **What this means for the public site** (under link-only; superseded by §13.5)**.** Until the City replies, the public site would be little more than a re-presentation of eTenders award data for one buyer. It would show award, buyer, date and usable value from eTenders, with links to City documents, but a confirmed legal form on only 2 of 291 rows and no age indicator on any row. The work that makes TenderWatch useful (legal-form confirmation, City cross-links, lookups, ages and churn notes) stays internal. A public launch under these limits would add little over eTenders itself, so the owner may prefer to wait for the City's answer before publishing.

### 13.2 Owner answers (revision 7, records only)

**Provenance.** Owner's answers, 17 Nov 2026 21:51 SAST, given in the project lead's (Cavus) chat and relayed by the project lead; the author has not heard them from the owner directly.

**Numbering.** The answers were relayed as Q1–Q11. The questions in this file are §13 Q1–Q11 (this RFC has no §9.1; that section number belongs to CHG-TW-003). Q1–Q6 match by number and topic. From Q7 on, the relayed numbers are one lower than this file's, because §13 Q7 (CIPC permission) was already answered in §13.1. The author maps them by topic as below. The mapping of relayed Q8 to §13 Q9 is the author's reading and is for the owner or the project lead to confirm (§13.6 A).

| Relayed | §13 question | Owner's answer (as relayed) | Recorded effect |
|---|---|---|---|
| Q1 | Q1 Publication of derived years | Publish the registration year with its fact label. | `registration_year` and `registration_year_label` may go into the public export in a later build CHG. The recommendation to hold the year internal (§4.6) is not adopted. The CIPC terms point (§4.6, §4(7)) is unchanged and the letter to CIPC Legal Services stays drafted for the owner to send. |
| Q2 | Q2 Reported age bands | Reported age bands stay internal, as recommended. | The public row shows `unknown` for any age band whose label is not Confirmed (§6, unchanged). See §13.6 B on the year itself. |
| Q3 | Q3 Ranking weights | Ranking accepted as is. | §4.3 unchanged. |
| Q4 | Q4 Batch size | Batch of 10 accepted. | §4.4 unchanged. |
| Q5 | Q5 One-person businesses | One-person businesses may be on the lookup list, but the public display masks the name to its first and last letter (example given: `C*****************a`), so only someone who already knows the name can match it. | The 3 held registered names (5 rows, all Reported links) may join the lookup list: 48 entities by count (6 Confirmed-link, 42 Reported). The §4.3 ranking and batch order are **not** recomputed in this records-only revision; the build CHG re-runs the script. The 14 personal-looking bare names (27 rows) have no suffix, so §4.2 still keeps them off the list. POPIA note below. |
| Q6 | Q6 Bare names (192 no-suffix rows) | The 192 bare-name rows must be recorded; the RFC proposes how. | Proposal in §13.3. |
| Q7 | Q8 C4 threshold | The C4 threshold of 3 young winners at one buyer within 365 days is accepted. Also: indicators for repeat awards to the same supplier and for other patterns worth a closer look, as a neutral, sourced list. | C4 threshold fixed at 3 (§7.2). Indicator proposal in §13.4. |
| Q8 | Q9 Periodic part-1 checks (author's reading) | Keep development structured. | Read as: the S8 and S10 surveys and every later step go through their own records-only CHG, with RFC, review and the owner's GO, as now. |
| Q9 | Q10 Local DEV reading of City registers | Publish links to the City documents, and download the City award PDFs to the box for the owner to read. | Done for reading only (below). Links to City documents go into the public output with each City fact. |
| Q10/Q11 | Q10 and Q11 (and §13.1 City option (i)) | "Public data is public data, act accordingly." | Replaces the link-only rule of §13.1 (below). |

**Q5 POPIA note (author; the owner's decision is not changed).** A mask that keeps the first letter, the last letter **and the length** is pseudonymous, not anonymous: the length narrows the name a great deal, and the same row also shows the buyer, date, value and a citation to the City document, which prints the name in full. Anyone who opens the cited source can read the name, so the mask stops only a casual reader. Possible safeguards, for the owner to choose (§13.6 C): (1) a fixed-length mask (for example first letter, three asterisks, last letter, whatever the name's length); (2) no other identifying detail next to a masked name beyond what the award itself needs; (3) for masked rows, cite the City document at the register level rather than the row level. The POPIA rules in §8 stay: only number, date and status are recorded from a lookup, and no personal contact or identity data is recorded at all.

**Q9 City PDFs (done).** On 17 Nov 2026 the author downloaded every award-register PDF linked from the City's tenders-awarded page (https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/tenders-rfqs-and-supply/tenders-awarded/): **150 PDFs** (150 links, 0 errors after one retry of a timed-out file; about 82 MB; registers from 2016 to 2026). robots.txt (`User-agent: * / Allow: /`) was checked first; one request at a time with a 2-second pause and an identifying user agent. They are stored on the box at `/home/box/tenderwatch-private/city-pdfs/` for the owner to read, **outside the repository and never committed**. A private manifest beside them (`/home/box/tenderwatch-private/manifest.json`, SHA-256 `5a5259a9…1fc4`) records the count and, per file, the URL, size, SHA-256 and retrieval time. They are not parsed or used for any count in this revision.

**Q10/Q11 Public data is public data.** The owner's answer replaces City option (i): City of Cape Town register facts may be published, each cited to the City document it comes from. The public site stays labelled **DRAFT**. If challenged, the answer is that it is a draft built only from the public record, presented as found. For the record, once: the City's website terms (§3 S7, §11) do not permit redistribution of its content without the City's express written permission; the owner has decided to publish anyway, and the permission letter to the City remains drafted for him to send. Nothing is published under this revision; the export and site changes need their own CHG and the owner's GO on the exact head.

### 13.3 Proposal: recording the 192 bare-name rows (Q6)

On the DEV data, 192 award rows (157 distinct names) carry no legal-form suffix in any source and have no City cross-link (CHG-TW-002 `no_suffix`). A bare name can be a company written without its suffix, or a sole proprietor trading under a personal name, which a reader cannot tell apart. Proposal (for a later build CHG; nothing changes here):

1. **Every row is recorded and shown** as an award: buyer, award date, usable value, tender reference and title, all from eTenders (CC BY 4.0), with links to the eTenders source.
2. **Legal form: "Unknown"** with the fact label **Unknown** and the reason "no legal-form suffix in any source". No age indicator (it needs a juristic supplier, §6).
3. **Name display.** The supplier name is shown only after the two-person check (CHG-TW-002) finds that it is not a personal name. Until then the row shows "Supplier name pending check", so no personal name is exposed. If the owner prefers, the Q5 mask can be used instead (§13.6 C applies).
4. **Two-person check queue.** The 157 names go through the existing queue, ranked by usable value; each check records only the outcome (`not_personal`, `personal`, `unclear`) and the date, in the git-ignored local file. A `personal` outcome keeps the name withheld; `unclear` stays pending.
5. **Upgrade path.** A row leaves the Unknown state only on a sourced suffix (a later City register, a public document under part 1, or an owner lookup that matches under §5), never on a guess.
6. Counts in the public method page: rows recorded, rows with legal form Unknown, names pending check.

### 13.4 Proposal: neutral, sourced indicator list (Q7)

Rules for every indicator: it is a pattern in the public record that may merit a closer look, never a finding about anyone. It cites its source documents, states counts and dates rather than adjectives, carries "Right of reply: pending", and uses the wording below. The private churn notes C1–C6 (§7) stay private; C4's threshold is now fixed at 3 (owner, relayed). Thresholds marked "proposed" are for the owner to confirm (§13.6 D). DEV measurements are counts on the 291 rows (one buyer, City of Cape Town; award dates 2021-08-20 to 2025-11-07).

| Id | Indicator | Definition | Data source | Threshold | Public wording (template) | DEV measurement | Status |
|---|---|---|---|---|---|---|---|
| I1 | Repeat awards to one supplier | Number of awards and total usable value to the same supplier (same `name_key`; same registration number once looked up) at one buyer, per municipal financial year (1 July to 30 June) and per rolling 365 days | eTenders OCDS (S1); City register (S7) cited per award | Shown for every supplier with 2 or more awards; highlighted at 3 or more in one financial year (proposed) | "This supplier received N awards (R X usable value) from [buyer] in financial year YYYY/YY. Source: [links]. This is a count from the public record." | 224 suppliers: 17 with 2 awards and 3 with 3 awards in one financial year; none with more | Ready to build |
| I2 | Awards just under a procurement threshold | Two or more awards to the same supplier at one buyer within 30 days, each below the competitive-bidding threshold for that kind of buyer, together at or above it | eTenders OCDS values; threshold from the Municipal SCM Regulations as amended (§15.3) | Metro: R750 000 (VAT included); 30-day window (proposed) | "N awards to this supplier from [buyer] within D days were each below the R750 000 competitive-bidding threshold for a metro and together total R X. Source: [links]." | 0 windows. Only 4 rows with a usable value are below R750 000, because eTenders mostly carries competitive bids; whether OCDS values include VAT is Unknown | Built only with a quotation-level source; Unknown until then |
| I3 | Deviations and contract expansions | An award made through a deviation from the normal procurement process (Municipal SCM Regulation 36), or a contract expanded or varied above the limit in the applicable Treasury instruction | City reports of deviations to council and the notes to its annual financial statements; OCDS contract amendments where present | Any listed deviation tied to an award by tender reference; any expansion above the cited limit | "The [buyer] reported this award as a deviation under SCM Regulation 36 in [document, page]." / "The contract value was increased by P% on [date]. Source: [link]." | Not measured: no deviation or amendment source held | Source survey needed (own CHG). Regulation 36 text: Reported (§15.3); expansion limits: Unknown |
| I4 | Registered shortly before the bid closed | Company registration date within 365 days before the tender's closing date | Registration date from an owner CIPC lookup (§4); closing date from OCDS `tender.tenderPeriod.endDate` | 365 days (proposed) | "Registered in YYYY; the bid closed on [date]. Sources: CIPC lookup (registration year), eTenders." Only the year is public (Q1); the day gap stays internal | Closing date present on 278 of 278 releases behind the 291 rows; registration dates: none yet (no lookups returned) | Ready once lookups return |
| I5 | Deregistered or in liquidation at award | An award dated after a dated public notice of final deregistration, winding-up or liquidation of the winner | Dated public notices (Government Gazette S10, court or Master's notices); CIPC status from a lookup is undated and internal (§4.5) and never fires I5 | Notice dated before the award date | "A [notice type] dated [date] ([Gazette no., page]) concerns a company with this name and number; the award is dated [date]." | Not measured: no Gazette notices held | Needs the S10 survey (own CHG) |
| I6 | AGSA finding that names the award | An Auditor-General report or annexure that names the tender reference or contract | AGSA reports (S11), cited with page | Any finding that names the award | "The Auditor-General's [report, year, page] refers to this award: '[short quote]'." | Not measured | Needs the S11 survey; AGSA copyright terms Unknown, so link and quote briefly |
| I7 | Single-bid award | An award where the published bid-opening record shows one bid | OCDS `tender.numberOfTenderers`, or a bid-opening list published as complete | Exactly one bid, where the data shows it | "The published bid record lists one bid for this tender. Source: [link]." | `numberOfTenderers` absent on all 278 releases; a tenderer list is present on 24, with one entry on 21. Whether a one-entry list means one bid is Unknown (a list may carry only the winner) | Not enabled until a complete bid-opening record is confirmed |
| C4 | Young winners clustered at one buyer | As §7.2 | As §7.2 | 3 or more within 365 days (owner, relayed) | Private churn note only (§7.3) | Not measured (no lookups yet) | Threshold fixed |

General wording on the method page (draft): "An indicator is a pattern in the public record that may merit a closer look. It is not a finding that anyone did anything wrong. Every indicator links to its sources, and each supplier named has a right of reply."

### 13.5 Knock-on recomputed (public data is public data)

Counts from the same DEV outputs as §13.1 (`data/local/warehouse/awards_classified_chg_tw_002.jsonl`, 291 rows; the `.out.json` counts are unchanged). "Publishable" means allowed under the owner's answers, subject to the POPIA gate; nothing is published under this RFC.

| Measure | Under link-only (§13.1) | Now |
|---|---|---|
| Confirmed legal-form rows (CHG-TW-002 `confirmed_juristic`, 66) that can show their legal form | 2 (OCDS suffix only) | **61**: 59 City-derived + 2 OCDS. The other 5 (City-derived) are POPIA-held and show only under the Q5 mask, if the owner applies it to held rows (§13.6 C) |
| Of those 61, the award link label | n/a | 7 Confirmed (5 by tender reference, 2 same record), 54 Reported (name and buyer only) |
| City cross-links (59 Reported) that can be shown with their City citation | 0 | 54, plus 5 held rows under the mask |
| Lookup entities whose registered name can be shown | 1 (eTenders-derived) | **45** of 45 (44 City-derived, 1 eTenders); with Q5, 48 (the 3 added names masked) |
| Rows that can carry a Confirmed registration year after all lookups (§5) | 6 (held under the §4.6 recommendation) | **6** (Q1: published with its label) |
| Rows whose year would be Reported (Reported link) | 54 | 54 (59 with the 5 held rows); whether the year itself is shown is open (§13.6 B); the age band stays internal (Q2) |
| Bare-name rows recorded (Q6) | not addressed | 192 rows (157 names), legal form Unknown, names pending the two-person check (§13.3) |
| Personal-looking queue rows (`looks_like_personal_name`, POPIA-held) | withheld | 27 rows (14 names): still withheld; whether the Q5 mask applies to them is open (§13.6 E) |
| Name-mismatch queue rows | withheld | 6 rows: unchanged, pending the two-person check |

**What this means for the public site.** The §13.1 conclusion (that the site would add little over eTenders) no longer holds. A later export CHG could show a sourced legal form on 61 of 291 rows (7 with a Confirmed award link), City cross-links with citations, registration years from lookups as they return, and the indicators in §13.4, while 192 rows carry an Unknown legal form and 33 rows (27 personal-looking, 6 mismatched) stay withheld pending the check.

### 13.6 New owner questions (revision 7)

* **A. Numbering.** Is the relayed Q8 ("keep development structured") the answer to §13 Q9 (periodic part-1 checks in a later records-only change), as the author reads it?
* **B. Reported years.** Q1 publishes the year with its label; Q2 keeps Reported age bands internal. For the up to 54 rows whose year would be Reported, a shown year lets a reader work out the band. Show Reported years with the label Reported (recommended: no, show `unknown` until Confirmed, which matches Q2), or show them?
* **C. Mask safeguard (Q5).** Keep the length-preserving mask as decided, or use a fixed-length mask, and should masked rows cite the City document at the register level only? Does the mask also apply to the 5 held rows of confirmed companies?
* **D. Indicator thresholds (§13.4).** Confirm I1 (3 or more in one financial year), I2 (30 days), I4 (365 days).
* **E. Personal-looking rows.** Do the 27 personal-looking rows (14 names) stay withheld until the two-person check (recommended), or show under the Q5 mask?

## 14. CAB review

Reviewers: **reviewer A** (project lead) and **reviewer B**, four checks (expert, shadow, charter, drift). Two reviewer PASSes are required on the exact head; each review round and its outcome is recorded in the pull request. A PASS is not a GO to merge, build or publish; only the owner gives that, on the exact head. A build needs its own CHG and GO.

**Result:** pending.

## 15. Legal basis (for the RFC now; later for the site's sources and method page)

All sources below were opened by the author on **17 Nov 2026**. Acts Online (acts.co.za) is a private consolidation; its wording was cross-checked against the Act as published in the Government Gazette (copy hosted by Parliament). Labels: **Confirmed** = wording read in the opened source; **Reported** = seen only in a secondary copy; **Unknown** = not established. No legal view is taken: the provisions are quoted as found.

### 15.1 Name, registration number and legal form (Companies Act 71 of 2008)

* **s32(4)** (Confirmed): "Every company must have its name and registration number mentioned in legible characters in all notices and other official publications of the company, including such notices and publications in electronic format as contemplated in the Electronic Communications and Transactions Act, and in all bills of exchange, promissory notes, cheques and orders for money or goods and in all letters, delivery notes, invoices, receipts and letters of credit of the company."
  Source: https://www.acts.co.za/companies_act_2008/32_use_of_company_name_and_registration_number (accessed 17 Nov 2026). Same wording in the Act as published, Government Gazette No. 32121, Notice No. 421, 9 April 2009: https://www.parliament.gov.za/storage/app/media/Acts/2008/Act_71_of_2008_Companies_Act.pdf (accessed 17 Nov 2026; file SHA-256 `6387b2fd…dd40`).
* **s32(1)(a)** (Confirmed, same sources): a company must "provide its full registered name or registration number to any person on demand".
* **s11(3)(c)** (Confirmed): "a company name, irrespective of its form or language, must end with one of the following expressions, as appropriate for the category of the particular company: (i) The word "Incorporated" or its abbreviation "Inc.", in the case of a personal liability company. (ii) The expression "Proprietary Limited" or its abbreviation, "(Pty) Ltd.", in the case of a private company. (iii) The word "Limited" or its abbreviation, "Ltd.", in the case of a public company. (iv) The expression "SOC Ltd." in the case of a state-owned company. (v) The expression "NPC", in the case of a non-profit company."
  Source: https://www.acts.co.za/companies_act_2008/11_criteria_for_names_of_companies (accessed 17 Nov 2026); same wording in Gazette No. 32121. s11(3)(b) ("(RF)") reads differently in the two: the consolidation adds "restricting or prohibiting the amendment of any particular provision of the Memorandum". Which amending Act made that change: Unknown (not opened).

### 15.2 The companies register is public (Companies Act and Companies Regulations, 2011)

* **s187(4)** (Confirmed): "The Commission must— (a) establish and maintain in the prescribed manner and form— (i) a companies register; and (ii) any other register contemplated in this Act, or in any other legislation that assigns a registry function to the Commission; (b) receive and deposit in the registry any documents required to be filed in terms of this Act; (c) make the information in those registers efficiently and effectively available to the public, and to other organs of state; …"
  Source: https://www.acts.co.za/companies-act-2008/187_functions_of_commission (accessed 17 Nov 2026); same wording for s187(4)(a) and (c) in Gazette No. 32121. This confirms the s187(4)(c) citation on CIPC's privacy page that §4.6 labelled Reported.
* **s187(5)** (Confirmed, same sources): "Subject to the provisions of subsections (6) and (7), any person, on payment of the prescribed fee, may— (a) inspect a document filed under this Act; …". **s187(6)**: "Subsection (5) does not apply to any part of a filed document if that part has been determined to be confidential, or contain confidential information, in accordance with section 212."
* **s186(1)(b)** (Confirmed, https://www.acts.co.za/companies_act_2008/186_commission_objectives and Gazette No. 32121): an objective of the Commission is "the maintenance of accurate, up-to-date and relevant information concerning companies, … and the provision of that information to the public and to other organs of state".
* **Companies Regulations, 2011** (Confirmed): Government Notice No. R. 351, Government Gazette No. 34239 (Regulation Gazette No. 9526), 26 April 2011, made under s223 of the Act. The brief's reference is verified. Sources: https://www.gov.za/sites/default/files/gcis_document/201409/34239rg9526gon351.pdf (Part A, title page; SHA-256 `4daa96e5…e490`) and https://www.gov.za/sites/default/files/gcis_document/201409/34239rg9526gon351d.pdf (Part D; SHA-256 `a790ebe5…3663`), both accessed 17 Nov 2026.
  * **Reg 174(1)** (Gazette p. 157): "A regulatory agency must keep any register required in terms of the Act in an official language of the Republic, in a manner sufficient to provide an adequate information base to— … (b) provide simple and efficient access to the public to information required to exercise any right in terms of the Act, or any other applicable law."
  * **Reg 177(1)** (Gazette p. 160): "Any person, upon payment of the prescribed fee, may inspect or copy any record of a regulatory agency— (a) if it is not restricted information; …". Reg 176(2) lists the five classes of restricted information (confidential information under s212, a complainant's identity, complaint material, internal deliberative documents, and records a public body may withhold under PAIA).
* **s26** (Confirmed, https://www.acts.co.za/companies_act_2008/26_access_to_company_records, accessed 17 Nov 2026): it gives access to records held **by a company** (for example its Memorandum of Incorporation and director records), not to CIPC's register. It is not the provision that makes the register public.

### 15.3 Procurement thresholds and deviations (for the indicators in §13.4)

* **Municipal SCM Regulations, regulation 19(b), as substituted on 14 Dec 2023** (Confirmed): "no requirement for goods or services above an estimated transaction value of— … (iii) R750 000 (VAT included), in the case of a metropolitan municipality, may deliberately be split into parts or items of lesser value merely for the sake of procuring the goods or services otherwise than through a competitive bidding process." The same notice sets the competitive-bidding threshold for a metro above R750 000 (VAT included) in regulation 12(1)(d)(iii). Source: Notice No. 4198, Government Gazette No. 49863, 14 December 2023, https://mfma.treasury.gov.za/RegulationsandGazettes/Municipal%20SCM%20Amendment%20Regulations.pdf (accessed 17 Nov 2026; SHA-256 `abf57842…05af`). It amends the regulations published under General Notice No. 868 of 30 May 2005.
* **Regulations 32 and 36** of the Municipal SCM Regulations (Government Gazette No. 27636, 30 May 2005): the brief's "s32 and s36 of the MFMA" are read as these regulations (32: goods and services under contracts secured by other organs of state; 36: deviation from, and ratification of minor breaches of, procurement processes). Titles and regulation 36 wording seen only in search-result extracts of municipal SCM policies that reproduce them (the policies were not opened): **Reported**. The Gazette text was not opened (the National Treasury page links a different file under that title): **Unknown**.
* **Contract expansion limits** (MFMA Circular 62, and the PFMA-side Treasury instruction): not opened, **Unknown**. Seen only as 20% (construction) and 15% (other) in a search-result extract of a municipal SCM policy (not opened): Reported.

### 15.4 What stays Unknown

* Whether ss187(4)–(5) and regs 174 and 177, which make the register available and allow inspection and copying, permit **republication** of what a CIPC lookup shows, given CIPC's website terms §4(3) and §4(7) (§4.6). No legal view taken: Unknown. The letter to CIPC Legal Services stays drafted for the owner to send.
* Whether regs 174, 176 and 177 have been amended since 26 April 2011: not checked, Unknown.
* The City's website terms (§3 S7) are website terms, not statute; how they interact with the public-access provisions above: Unknown, no legal view taken.

### 15.5 Draft text for the sources and method page (not published; a later site CHG)

"TenderWatch SA is a DRAFT built only from the public record and presented as found. Award data comes from the National Treasury eTenders portal (Creative Commons BY 4.0) and from the City of Cape Town's published award registers, each cited to its document. A company's legal form comes from its name, which the Companies Act requires to end with an expression such as "(Pty) Ltd" (s11(3)(c)), and every company must print its name and registration number on its notices and publications (s32(4)). The Companies and Intellectual Property Commission must make the information in its registers efficiently and effectively available to the public (Companies Act s187(4)(c); Companies Regulations, 2011, reg 174(1)(b)). Indicators are patterns in the public record, not findings about anyone. Private individuals are not identified."

---
*POPIA check: PASS. No supplier or personal names; counts only; examples invented. No ID numbers, contact details or addresses. CIPC fields limited to registration number, registration date and status. Revision 7: the mask example is the owner's own, is reproduced as relayed, and matches no supplier name in the DEV data (checked: no name of that length with that first and last letter); the downloaded City PDFs are outside the repository.*
