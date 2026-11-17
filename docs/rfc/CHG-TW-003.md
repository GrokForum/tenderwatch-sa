# CHG-TW-003 — Can an exact registered-name match move a link from Reported to Confirmed?

| Field | Value |
|---|---|
| Change | CHG-TW-003 |
| Type | RFC only (analysis and proposed rule). No code, no data change, no build under this record. |
| Environment | DEV (records only) |
| Branch | `dev/CHG-TW-003-name-match-rfc`, from `origin/main` at `258dc778a019ac939067dce0307439228723b7d4` (PR #4 merged, head `8663c878`) |
| Rollback reference | `258dc778a019ac939067dce0307439228723b7d4`; snapshot tag `snapshot-2026-11-17-pre-tw-pr4` → `f63f5d2ef02621f9a991c4c353788f7377ab2aa7` |
| Author | the author (TenderWatch) |
| Reviewers | reviewer A (project lead), reviewer B |
| Status | Draft for CAB. Owner questions decided by the project lead under delegated authority (relayed) and confirmed by the owner in chat on 17 Nov 2026 at 18:15 SAST (§9.1). Rule A is adopted in principle only; no build under this record. |

## 1. Question (owner input, relayed by the project lead, 17 Nov 2026)

The owner's premise: CIPC does not allow two companies to register the same name. An applicant submits name options; a clash moves CIPC to the next option; if all clash, the application is rejected. So an exact match on a registered name with its legal suffix identifies one entity.

Question: can **exact normalised registered-name matches** (suffix included; no `t/a` or trading name; no fuzzy match) move a City-register-to-OCDS link from **Reported** to **Confirmed** (CHG-TW-001 §19, CHG-TW-002 §4.3)? Exceptions to handle: trading names, spelling variants, deregistered and re-registered names, and trusts.

## 2. What the law and CIPC say (sources checked 17 Nov 2026)

Labels: **Confirmed** = the cited primary text says it; **Reported** = an official or tribunal source says it, but it is guidance, practice or interpretation rather than statute; **Unknown** = not found in a free primary source.

| # | Point | Label | Source (retrieved 17 Nov 2026) |
|---|---|---|---|
| L1 | A company name must not be **the same as** the name of another company, domesticated company, registered external company, **close corporation** or co-operative (s11(2)(a)(i)), and must not be **confusingly similar** to one unless both are in the same group (s11(2)(b)(i)). | Confirmed | Companies Act 71 of 2008, s11: https://www.acts.co.za/companies-act-2008/11_criteria_for_names_of_companies |
| L2 | The suffix is a separate statutory element: the name "must end with" Inc. / (Pty) Ltd. / Ltd. / SOC Ltd. / NPC by category (s11(3)(c)); "(RF)" must immediately follow the name where the MOI has restrictive provisions (s11(3)(b)); a number-only name ends "(South Africa)" (s11(3)(a)). | Confirmed | Same, s11(3) |
| L3 | CIPC **must reserve** each name applied for unless it is the registered name of another company, CC or co-operative, the name of a registered external company, or already reserved (s12(2)). The name must also not be the same as a defensive name or a business name (Business Names Act 27 of 1960) registered for someone else, a registered or applied-for trade mark of someone else (Trade Marks Act 194 of 1993), or a mark, word or expression restricted under the Merchandise Marks Act 17 of 1941 (s11(2)(a)(ii)–(iv)). Confusing similarity is handled after reservation by notice and the Companies Tribunal (s12(3), s160), not by refusal. | Confirmed | Companies Act s11(2)(a) (retrieved 17 Nov 2026): https://www.acts.co.za/companies-act-2008/11_criteria_for_names_of_companies ; Companies Act s12, official text: https://www.parliament.gov.za/storage/app/media/Acts/2008/Act_71_of_2008_Companies_Act.pdf |
| L4 | Form CoR 9.1 may list **up to four alternative names in order of preference**; CIPC considers them **serially** and confirms one (CoR 9.4) or refuses (CoR 9.5) if each name fails s11/s12 or reg 8. | Confirmed | Companies Regulations 2011, reg 9(1), 9(3): https://www.gov.za/sites/default/files/gcis_document/201409/34239rg9526gon351.pdf |
| L5 | The Companies Tribunal has held that CIPC may refuse a reservation only where the name is **the same as** a registered or reserved name, not merely confusingly similar. CIPC's own guidance lists "confusingly similar" as a refusal ground. Practice and tribunal reading differ. | Reported | Companies Tribunal CT005Mar2017: https://companies.piidigital.co.za/wp-content/uploads/2018/07/ct005mar2017-1.pdf ; CIPC, *Business and Company Name Reservation in South Africa* (PDF created 30 Sep 2026): https://www.cipc.co.za/wp-content/uploads/2026/10/Business-and-Company-Names.pdf |
| L6 | **A suffix is not permitted at the name-reservation stage** ("Pty Ltd", "SOC", "RF", "Ltd", "INC" and similar). So the availability test runs on the name **without** its suffix. | Reported (CIPC guidance; the Act does not say whether "same as" ignores the suffix) | CIPC name-reservation PDF above |
| L7 | Whether the s11(2)(a) "same as" test ignores the suffix, punctuation or case: no statutory or regulatory rule found. | Unknown | Searched the Act and Regulations 2011 above |
| L8 | The owner's premise (no two companies with the same name; options tried in order; rejection if all fail) matches L1, L3 and L4 **for live CIPC registrations at one point in time**. If a name is refused, a profit company may still be registered with its **registration number as its name** plus "(South Africa)". | Confirmed (L1, L3, L4); Reported for the number-name practice | CIPC Name Reservation page: https://www.cipc.co.za/?page_id=10102 ; CIPC PDF above |
| L9 | **Trading names are not registered by CIPC.** The Consumer Protection Act business-name register is "indefinitely deferred"; businesses may trade under another name "in conjunction with the registered name". | Reported (CIPC guidance) | CIPC PDF above |
| L10 | After **final deregistration** the name becomes available to others: a 2013 CIPC notice says "immediately"; 2024 CIPC notices give **6 months' administrative protection** ("not legal"), then anyone may reserve it. A reinstated company keeps its name; if someone else took it meanwhile, the Companies Tribunal decides. | Reported (CIPC notices and FAQ; practice has changed over time) | GN 205 of 2013: https://www.gov.za/sites/default/files/gcis_document/201409/36225gen205.pdf ; CIPC notice Jan 2024: https://www.cipc.co.za/wp-content/uploads/2024/02/Notice_Final-Deregistration-January-2024_v1.0.pdf ; CIPC FAQ: https://www.cipc.co.za/?page_id=4160 |
| L11 | A company may **change its name** (an amendment to its MOI). A Tribunal order can force a change; if not done in 60 business days CIPC changes the name to the registration number with "(South Africa)". | Reported | CIPC Name Reservation page and PDF above |
| L12 | **Close corporations:** CC name reservation and objections now follow Part A of Chapter 2 of the Companies Act (ss11–12) (CC Act s19 and s20 as substituted). New CCs could be formed only **before s13 of the Companies Act came into operation**. | Confirmed | Close Corporations Act 69 of 1984, s19: https://www.acts.co.za/close-corporations-act-1984/19__undesirable_names_and_reservation_of_names ; Companies Act Schedule 3 (amending CC Act ss2, 13, 19, 20): https://www.acts.co.za/companies-act-2008/sched_3_schedule_3_amendment_of_laws |
| L13 | The date on which s13 came into operation (commonly given as 1 May 2011). | Reported (not checked in a primary commencement notice) | — |
| L14 | **Trusts:** the trustee lodges the trust instrument with the **Master of the High Court** (Trust Property Control Act s4); inter-vivos trusts register with the Master where most trust assets are. Trusts are not on the CIPC register. | Confirmed | Trust Property Control Act 57 of 1988, s4: https://www.acts.co.za/trust_/4_lodgement_of_trust_instrument ; Master's Office: https://www.justice.gov.za/master/trust.html |
| L15 | A name-uniqueness rule for trusts: none found in the Act or on the Master's page. | Unknown | Same |
| L16 | A **joint venture** is not one of the company categories in s11(3)(c); "JV" is not a statutory suffix. An unincorporated JV is not a CIPC-registered entity (an incorporated JV company carries an ordinary company suffix). | Confirmed for the suffix list; Reported for the general point | Companies Act s11(3) above |

**What this means for the premise.** Near enough right for **live** CIPC companies and CCs **at one point in time**: an identical name cannot be reserved or registered while another live entity holds it (L1, L3, L4), and the check runs on the name without its suffix (L6). It is **not** a lifetime guarantee: a name can be freed by deregistration and taken by a new entity (L10), changed (L11), or used as an unregistered trading name by someone else (L9). It says nothing about trusts (L14, L15) or unincorporated JVs (L16).

## 3. Two different questions (analysis a)

1. **Entity question.** Does an exact registered name with its suffix identify **one entity**? At one point in time, for a live CIPC company or CC: yes in law (L1, L3), with the gaps above. This question is about the **legal form**, which the City already prints. CHG-TW-002 already uses it: the suffix is what confirms the legal form (method 1).
2. **Link question.** Does a 2026 City register row refer to the **same supplier** as a 2021–2025 OCDS award? This is what CHG-TW-001 §19 and the CHG-TW-002 `legal_form_fact_label` "Reported" are about. A name-and-buyer link is not a tight match.

The owner's rule would change the **link label** (`legal_form_fact_label` / `supplier_name_fact_label`), not the entity status. Name uniqueness helps the link question only when **both** records carry the same registered name, suffix included, at dates close enough that the name cannot have changed hands. If one record carries a bare name, uniqueness of the registered name says nothing about whether the bare name *is* that registered name: it could be a trading name (L9), a sole trader or an unrelated business.

## 4. Measurement on the existing DEV data (analysis b)

Input: the CHG-TW-002 DEV classification of the 291 Cape Town award-supplier rows (OCDS SHA-256 `a2849a63…5225`) and the 508 City register rows (Feb–Oct 2026). Counts only.

| Measure | Count |
|---|---|
| Reported rows (`legal_form_link = name_and_buyer_only`) | **59** (5 of them under POPIA hold) |
| …with an **exact normalised match with suffix in both sources** (same stem, same canonical suffix, no `t/a`) | **0** |
| …where the **City name with suffix matches the OCDS name without any suffix** (stem equal) | **59** |
| …other patterns | 0 |
| …with a `t/a` in the linked City name | 0 |
| …where the linked City spellings disagree on the canonical suffix | 0 (6 rows have more than one City spelling, all with the same suffix) |
| Sub-type of the 59 | 51 company, 8 close corporation |
| Award year of the 59 | 2021: 5, 2022: 16, 2023: 10, 2024: 12, 2025: 16 |
| Gap from award date to the nearest linked City **decision date** (days counted inclusively, both dates included) | ≤365 days: 6; 366–730: 11; 731–1095: 9; >1095: 22; undated: 11 (every linked City row gives only a register month, so the row counts as undated) |
| OCDS supplier names with any trailing suffix, all 291 rows | 2 |
| Tight links (`tender_ref`, 5 rows) with suffix in both sources | 0 |
| City stems seen with **two different** canonical suffixes in the register | 1 of 352 |
| OCDS normalised names that occur under **more than one** eTenders supplier id (all 291 rows) | 24 of 224 |
| …among the 42 distinct names behind the 59 Reported rows | 3 |

Plain result: **the owner's rule, as defined, would move 0 of the 59 Reported rows on this data.** The OCDS award name almost never carries a suffix, so an exact match on the registered name in both sources cannot happen. All 59 are a City registered name against an OCDS bare name, which is **not** an exact registered-name match under the owner's definition.

The two extra counts are warnings, not proof. The same stem with two suffixes in the City register could be a print error or two entities (Unknown). The same normalised name under several eTenders supplier ids could be duplicate portal profiles or different businesses (Unknown).

## 5. Exceptions and risks (analysis c)

* **Names change over time.** A name can be freed by deregistration and taken by a new entity, after 0 to 6 months depending on the period (L10), or changed by the company or by a Tribunal order (L11). Awards span 2021–2025 and the City data covers 2026; 31 of the 59 have a gap over 730 days, and 11 have no City decision date. Uniqueness at the City date does not prove the same holder at the award date.
* **Do not merge legal forms.** Normalisation must keep the canonical suffix: (Pty) Ltd ≠ Ltd ≠ SOC Ltd ≠ Inc ≠ NPC ≠ CC, and the "(RF)" qualifier is part of the registered name (L2). CHG-TW-002's `legal_sub_type` groups the private, public and Inc forms together as `company`, so this rule must compare the **canonical suffix plus the RF flag**, not the sub-type. Under L6, two live entities should not share a stem whatever their suffixes. A stem with two suffixes therefore signals an error or a time change; treat it as a conflict, never as two confirmed entities.
* **The source may print the name wrongly.** For example, a suffix added to a trading name, a missing "(RF)", a wrong suffix, PDF wrapping, or several vendors on one line. A single source's printing is evidence of what it says, not proof of the register.
* **Trading names and `t/a`.** CIPC does not register trading names (L9). A suffix after `t/a` is never a registered name, and a bare name may be a trading name of anyone.
* **Spelling variants.** No fuzzy matching. Any difference after normalisation (case, punctuation, spacing, "&" vs "and") means no exact match. The row stays Reported or queued.
* **Trusts.** Registered with the Master, not CIPC (L14). No name-uniqueness rule found (L15). Excluded from the rule.
* **JVs.** Not a statutory company form (L16). Usually an arrangement between entities. Excluded.
* **Number-names.** "(South Africa)" names are registration numbers, so they are unique by number. They do not occur here. Excluded unless both sources print the full number.
* **Legacy registrations.** Names registered under earlier Acts before 2011 may not have been checked the same way (Unknown).

## 6. Proposed rule (analysis d)

**Rule CHG-TW-003-A (exact registered-name link).** A City-to-OCDS link that is now `name_and_buyer_only` may be labelled **Confirmed** only if **all** of these hold:

1. Both records print a name ending in a statutory suffix (L2): (Pty) Ltd / Proprietary Limited, Ltd / Limited, SOC Ltd, Inc / Incorporated, NPC, or CC / Close Corporation.
2. After normalisation (case, spacing and punctuation only; "&" and "and" are **not** treated as equal), the stems are identical **and** the canonical suffixes are identical **and** the RF flag is identical.
3. Neither name has `t/a` / "trading as", and neither is multi-entity, a trust or a JV (CHG-TW-002 rules).
4. **Time window:** the award date and the actual City **decision date** are within **365 days, counted inclusively** (both dates count as days; for example 1 March 2025 to 28 February 2026 is 365 days and falls inside; 1 March 2025 to 1 March 2026 is 366 days and falls outside) (§9.1 Q2). A City row that gives only a register month and no decision date is **undated**: it never meets the window and the link stays Reported. Justification: L10 shows a deregistered name can pass to a new entity within 0–6 months, and names can be changed (L11). A window does not remove this risk; it only keeps it small. Outside the window the link stays Reported.
5. **No conflict:** the stem is not seen with a different suffix in either source, and the OCDS name is not tied to more than one eTenders supplier id.
6. POPIA holds and the two-person check queue are unchanged. A held name stays withheld whatever its label.

**What stays Reported:** every link that fails any condition, in particular all **City-suffix vs OCDS-bare** links (all 59 today). That is a stem-only match, and a bare OCDS name may be a trading name or another business (L9). Those links can become Confirmed only through an independent second detail: a shared tender reference (already Confirmed under CHG-TW-002), the same CSD or CIPC registration number from a free public document, or the two-person check.

**Expected effect today:** 0 of 59 rows change. The rule matters only if a future source prints the registered name with its suffix in the award record (for example a later eTenders format or another buyer's register).

## 7. Test plan (analysis e; invented names only)

Unit tests for a future build CHG under its own GO:

* Exact match: "Qwertane Widget Supplies (Pty) Ltd" in both, award date 2025-03-01 and City decision date 2025-06-01 → Confirmed.
* Punctuation, case and spacing variants of the same suffix ("Qwertane Widget Supplies Pty. Ltd.", "QWERTANE WIDGET SUPPLIES (PTY) LTD") → Confirmed.
* Different form: "(Pty) Ltd" vs "Ltd", "(Pty) Ltd" vs "SOC Ltd", "CC" vs "(Pty) Ltd", "NPC" vs "(Pty) Ltd" → stays Reported and is flagged as a conflict.
* RF: "Zephyra Holdings (RF) (Pty) Ltd" vs "Zephyra Holdings (Pty) Ltd" → stays Reported.
* Bare OCDS name vs City "Qwertane Widget Supplies (Pty) Ltd" → stays Reported (the 59-row case).
* "&" vs "and" ("Testburg & Sons (Pty) Ltd" vs "Testburg and Sons (Pty) Ltd") → stays Reported (no fuzzy match).
* `t/a`: "Qwertane Widget Supplies (Pty) Ltd t/a Widget World" vs the same → stays Reported.
* Trust ("Example Bursary Trust"), JV ("Acme Widgets JV"), multi-entity → excluded, unchanged.
* Window (365 days, inclusive): award 2025-03-01, City decision 2026-02-28 (365 days) → Confirmed; City decision 2026-03-01 (366 days) → stays Reported. City row with a register month only (e.g. "2026-02", no decision date) → undated, stays Reported. Missing award date → stays Reported.
* Conflict: same stem seen with "CC" elsewhere in either source → stays Reported.
* Held row ("J Q Testerman and Associates (Pty) Ltd") → label may change, name still withheld in the public export.
* Invariants: no row changes status; only `legal_form_fact_label` and `supplier_name_fact_label` may change; the public export still labels every named row; no tracked file carries a queued or held name.
* DEV re-run over the 291 rows: expect 0 changes (§4).

## 8. POPIA notes (analysis f)

* The rule uses only names already in the two public sources. No new personal data and no new source. No CIPC login or paid lookup (outside the project's free-source rule).
* Counts only in committed files. Per-name lists stay in the git-ignored local files (CHG-TW-002 §4.4). This RFC carries no supplier names; its examples are invented.
* A "Confirmed" link does not lift a POPIA hold. Names that look personal stay withheld until the two-person check.
* "Confirmed" here means two official sources print the same registered name close in time. It is an indicator about the record, never a finding about any person.

## 9. Owner questions (analysis h)

1. **Adopt rule A even though it changes 0 of 59 today?** The alternative is to defer until a source prints suffixes in award records.
2. **Time window:** 12 months (proposed; defined in §6 as 365 days counted inclusively between the award date and the actual City decision date), the same calendar year, or another value? Or no window, accepting the reuse risk in L10?
3. **Stem-only matches** (City registered name vs OCDS bare name, the 59 rows): keep them Reported (recommended), or accept stem uniqueness (L6) as enough? Accepting it would rely on CIPC guidance (Reported), not statute, and would ignore trading names (L9).
4. **Different suffixes on one stem:** treat them as a conflict (recommended), given that L6 implies two live entities should not share a stem?
5. **Second detail for the 59:** may a later CHG use free public documents (for example CSD numbers or CIPC numbers printed in public tender documents) as the independent detail? A CIPC login or paid data stays out of scope unless the owner gives a named GO.
6. **Clarification from CIPC:** would the owner like to ask CIPC in writing whether the "same as" test ignores the suffix (L7)? That would be the owner's own message; the author drafts only.

### 9.1 Decisions on the questions

**Decided by the project lead under delegated authority (relayed); confirmed by the owner in chat on 17 Nov 2026 at 18:15 SAST.**

| Q | Decision |
|---|---|
| Q1 | Adopt rule A in principle. Build it only once a source prints suffixes on award records. |
| Q2 | 12 months, defined as 365 days counted inclusively between the award date and the actual City decision date; a City row with only a register month is undated and stays Reported (§6 condition 4). |
| Q3 | Yes: the 59 City-suffix vs OCDS-bare rows stay Reported. |
| Q4 | Yes: different suffixes on one name stem count as a conflict. |
| Q5 | Yes. The next change is an RFC for a second independent detail from CSD or CIPC numbers in free public documents: RFC first, no build, and only after this PR merges. |
| Q6 | No CIPC letter for now; that remains the owner's call. |

## 10. Rollback (analysis g)

This RFC changes records only (`docs/rfc/CHG-TW-003.md`, `STATUS.md`). Before merge: delete the branch. After a merge: `git revert` the merge commit on a review branch, or reset a branch to `258dc778a019ac939067dce0307439228723b7d4`. Snapshot tag `snapshot-2026-11-17-pre-tw-pr4` (`f63f5d2e`) is unchanged. Nothing outside git is touched.

## 11. CAB review

Reviewers: **reviewer A** (project lead) and **reviewer B**, four checks (expert, shadow, charter, drift). Two reviewer PASSes are required on the exact head; each review round and its outcome is recorded in the pull request. A PASS is not a GO to merge, build or publish; only the owner gives that, on the exact head. A build of rule A needs its own CHG and GO.

**Result:** pending.

---
*POPIA check: PASS. No supplier or personal names; counts only; examples invented. No ID numbers, contact details or addresses.*
