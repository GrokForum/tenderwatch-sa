# CHG-TW-004 — A second independent detail: registration numbers from free public documents, owner CIPC lookups, and churn tracking

| Field | Value |
|---|---|
| Change | CHG-TW-004 |
| Type | RFC only (survey, measurement, design). No code, no data change, no build under this record. |
| Environment | DEV (records only) |
| Branch | `dev/CHG-TW-004-second-detail-rfc`, on `origin/main` at `75acab22d260a896937e8ca78e491b3ac53de298` (PR #5 merge after the project lead's history rewrite of 17 Nov 2026; files byte-identical to the pre-rewrite merge `e87c6cb3`) |
| Rollback reference | `75acab22d260a896937e8ca78e491b3ac53de298`; snapshot tag `snapshot-2026-11-17-pre-tw-pr5-rw` → `113432644a902aa7f7bd76af3cd299a5ff3a9bf8` |
| Author | the author (TenderWatch) |
| Reviewers | reviewer A (project lead), reviewer B |
| Basis | CHG-TW-003 §9.1 Q5 (decided by the project lead, confirmed by the owner): the next change is an RFC for a second independent detail from CIPC or CSD numbers in free public documents. Owner input on his own manual CIPC lookups, given in the author's chat on 17 Nov 2026 at 18:16 SAST (summarised in §4, not quoted). |
| Status | Draft for CAB on [PR #6](https://github.com/GrokForum/tenderwatch-sa/pull/6). City option (i) decided by the owner (§13.1); other owner questions open (§13). |

## 1. Summary

* **Free public documents almost never print a supplier's registration number on the award.** On the DEV data, **0 of 291** rows and **0 of 59** Reported rows can gain a CIPC or CSD detail from the free public documents already held (eTenders OCDS and nine City of Cape Town monthly award registers, Feb–Oct 2026). 2 of 291 releases (1 of the 59) contain a CSD token, but it belongs to a tenderer list and cannot be tied to the winner.
* **Owner CIPC lookups** are therefore the only practical source of a registration number and year. This RFC limits them to three fields (registration number, registration date, status), ranks a short list by value, and sets how a lookup becomes Confirmed.
* **A lookup alone does not upgrade a Reported link.** It confirms the entity behind the City name; the City-to-award link still needs a second independent detail (CHG-TW-001 §5, CHG-TW-003 §6). On today's data, lookups give a Confirmed registration year on at most **6** award rows (6 eligible entities whose links are already Confirmed; the seventh Confirmed-link entity is a JV and is excluded); the other **39** eligible entities (behind 54 of the 59 Reported rows; the other 5 are held) would carry a year labelled Reported.
* **CIPC's terms restrict reuse** of what is seen on its site (§4.6). The public output would carry only the derived registration year and our label, and this RFC recommends holding even that until the owner clears the terms.
* **City data is link-only** (owner decision, City option (i), §13.1): published facts come only from eTenders (CC BY 4.0).
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
| S7 | City of Cape Town monthly award registers — https://www.capetown.gov.za/work-and-business/doing-business-with-the-city/tenders-rfqs-and-supply/tenders-awarded/ | **0** CIPC and **0** CSD numbers in all nine 2026 PDFs held (Feb–Oct); no registration column | Confirmed (measured 17 Nov 2026) | `User-agent: * / Allow: /` | Copyright © City of Cape Town (https://www.capetown.gov.za/general/terms-of-use/, retrieved 17 Nov 2026): redistribution or reproduction is prohibited except (a) printing or downloading extracts to a local disk for personal, non-commercial use, and (b) copying the content to individual third parties for their personal use, if the City's website is acknowledged as the source. Any other distribution or commercial use needs the City's **express written permission**, with enquiries to the City webmaster; each permitted reference must acknowledge that the information resides at and is the property of the City of Cape Town. Unless otherwise specified, URL references for non-commercial purposes are permitted on the condition that each acknowledges that the information resides at and is the property of the City of Cape Town. Confirmed. | **Link only** (owner decision, City option (i), §13.1): cite the City URL with that acknowledgement, and carry no City-derived facts in the public output. Local downloads for DEV analysis only |
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

Score each eligible entity, highest first; ties broken by total award value:

| Factor | Points | Why |
|---|---|---|
| Award value at the buyer (sum of usable values; quartile of the eligible set) | top 3, second 2, third 1, none or unusable 0 | Larger public spend first |
| Young-company **candidate** (internal proxy: first seen as an eTenders winner no earlier than 1 June 2022 and within 365 days before this award) | 3 | The age indicator matters most here; the proxy is weak and never published |
| Buyer concentration (3 or more awards at the buyer) | 2 | Repeat winners at one buyer |
| Link already Confirmed | 2 | The year becomes Confirmed at once (§5) |
| Link Reported | 1 | The lookup is one detail of two; still useful for checks |

**DEV result (counts only):** 45 eligible; 30 with a usable value; 23 young-company candidates; 4 with 3+ awards. Score spread: 7 pts: 4, 6: 5, 5: 11, 4: 12, 3: 4, 2: 1, 1: 8. **Batch 1 (top 10): 2 Confirmed-link and 8 Reported entities, 8 young-company candidates, 2 repeat winners, all 10 with a usable value.** Five batches of 10 cover all 45 (the fifth has 5).

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

**Consequence.** Until the owner clears the terms (written permission, or his own legal view), the public output never carries CIPC records, registration numbers from lookups, dates, statuses, or anything copied from a CIPC screen. This RFC goes one step further than the minimum: because §4(7) may reach derived facts, it recommends that even the derived year and age band stay internal until the owner decides (§13 Q1). If the owner allows it, the public output carries only `registration_year`, `age_band` and our label.

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
| C4 | Young winners clustered at one buyer | 3 or more distinct entities with `age_band` `same` or `-1` win at one buyer within 365 days (threshold: §13 Q8) |
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

* **City copyright (S7).** The City's terms (https://www.capetown.gov.za/general/terms-of-use/, retrieved 17 Nov 2026) prohibit redistribution or reproduction of its content, except personal non-commercial extracts and copies to individual third parties for their personal use with the City's website acknowledged as the source. Anything else needs the City's express written permission (enquiries to the City webmaster). Non-commercial URL references are permitted only if each acknowledges that the information resides at and is the property of the City of Cape Town. The CHG-TW-001 public-site plan republished City-derived names and fields; the owner has since chosen City option (i) (§13.1): City data is link-only, and published facts come only from eTenders. A letter asking the City for permission is drafted for the owner to send himself; its outcome is pending.
* **CIPC derived-works clause (§4.6).** Even a derived year may fall under §4(7). Recommendation: keep it internal until the owner decides.
* **Owner time.** 45 eligible entities ≈ 5 batches; returns may be slow. The ranking puts value first.
* **Weak young-company proxy.** "First seen on eTenders" reflects publication coverage, not company age. It is used only for ranking and never shown.
* **Name reuse and conversions.** A name can pass to a new entity (CHG-TW-003 L10); a converted close corporation may show a number year that differs from its company registration. Mitigation: §4.5 checks; conflicts stay Reported.
* **Status has no date.** A current status says little about the status at the award date; C3 fires only with a dated public notice.
* **Over-reading.** Age and churn are indicators, never findings; wording rules from CHG-TW-001 apply.

## 12. Rollback

RFC only: this commit changes `docs/rfc/CHG-TW-004.md` and `STATUS.md`. Before merge, delete the branch. After a merge, `git revert` the merge commit on a review branch, or reset a branch to `75acab22d260a896937e8ca78e491b3ac53de298`. Tag `snapshot-2026-11-17-pre-tw-pr5-rw` (`11343264`) is unchanged. For a future build: the lookup files, snapshots and churn notes are local and git-ignored; deleting them returns every year to `unknown`.

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

### 13.1 Decisions

* **City option (i), decided by the owner on 17 Nov 2026 at 20:07 SAST, relayed by the project lead.** City of Cape Town data is **link-only**: the public output cites City URLs with the acknowledgement the City's terms require and carries no City-derived facts. Published facts come only from eTenders (CC BY 4.0). The author reads this as still allowing City registers to be read locally in DEV to find links and conflicts (owner to confirm, §13 Q10).
* **Two letters**, one to the City of Cape Town (permission to reuse its award registers) and one to CIPC Legal Services (reuse of information seen on its site), are drafted for the owner to send himself. They are not part of this repository. **Outcome: pending.**

## 14. CAB review

Reviewers: **reviewer A** (project lead) and **reviewer B**, four checks (expert, shadow, charter, drift). Two reviewer PASSes are required on the exact head; each review round and its outcome is recorded in the pull request. A PASS is not a GO to merge, build or publish; only the owner gives that, on the exact head. A build needs its own CHG and GO.

**Result:** pending.

---
*POPIA check: PASS. No supplier or personal names; counts only; examples invented. No ID numbers, contact details or addresses. CIPC fields limited to registration number, registration date and status.*
