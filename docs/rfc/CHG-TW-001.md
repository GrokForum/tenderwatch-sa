# CHG-TW-001 — TenderWatch SA DEV pilot: source survey, scaffold plan, one-source one-buyer ingest and young-supplier indicator

**Status:** DRAFT for CAB review. Not implemented. No SUCCEEDED / FAILED yet.
**Environment:** DEV only. DEV must not point at a production host, database, mailbox or DNS.
**Date:** 17 Nov 2026, Africa/Johannesburg (SAST).
**Author:** TenderWatch (Grok Bot), from the parked idea note and the 17 Nov 2026 source survey.
**CAB reviewers:** Cavus (expert / charter) and Cassian (shadow / drift). Sign-off must be by someone other than the author. The owner's GO is required before any implementation is merged to `main`, before any push, and before anything is published or sent.
**Pre-change SHA:** `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` (`main`, initial commit). Work lives on branch `rfc/CHG-TW-001`.
**Related:** `SOURCES.md` (evidence), `IDEA-tenderwatch.md` (parked idea, 16 Nov 2026), PublicFunds `/workspace/publicfunds`.
**Model:** PoliticianWatch SA planning packet and PublicFunds SA change discipline.

This change record describes proposed DEV work. This commit itself delivers only the survey, the RFC, and sanitized samples. It does not scaffold code, ingest a warehouse, or publish a site.

---

## 1. Summary

TenderWatch SA was parked because CIPC lookups need a login, and there is no GO for any login. The revival hypothesis was that public award data might already carry CIPC registration numbers (format `YYYY/NNNNNN/NN`, year only) or CSD numbers, so a "young winning supplier" indicator could be built without that login.

The 17 Nov 2026 survey does **not** support that hypothesis for structured award data:

- **0 / 9,551 (0%)** of award–supplier rows in the eTenders OCDS full mirror carry a supplier CIPC number. The only CIPC number in the corpus is Transnet's own.
- **11 / 9,551 (0.12%)** of winner names contain a CSD-like `MAAA…` token, not as a field. A CSD number does not encode registration year.
- Official July 2026 monthly OCDS: **0 / 42** CIPC, **0 / 42** CSD.
- City of Cape Town October 2026 award register: **0 / 24** tender references with CIPC or CSD.

What *is* feasible, without any login, is a **neutral, sourced awards register** for one buyer, reused from PublicFunds' existing eTenders ingest. The registration-year signal should still be specified, tested with fixtures, and shown as **Unknown** until a free year source appears or publishers start emitting CIPC numbers.

**Proposed DEV pilot (this RFC, if the owner gives a GO):** one source (eTenders OCDS, reused from PublicFunds) and one buyer set (City of Cape Town). No TEST, no PROD, no site publish, no right-of-reply messages sent (drafts only, labelled `Right of reply: pending`).

## 2. Motivation

The idea note (`IDEA-tenderwatch.md`) describes a public-interest pattern: a company that wins a government award very soon after it is registered. That is an *indicator*, not proof of wrongdoing. To compute it we need (a) an official award with a supplier and a date, and (b) the supplier's registration year. (a) is publicly available and already ingested by PublicFunds. (b) is not, on the sources that can be used without a login.

The honest options are therefore: park the product again; build the awards register now and leave age as Unknown; or wait for a free registration-year source. This RFC proposes the middle path in DEV only, so the owner can see the register, the match rule and the labelled indicator working on fixtures, without pretending the year is available in the wild.

## 3. Scope (DEV only)

In scope, after a written owner GO that names this RFC and the exact commit, and only on DEV:

1. **Scaffold** this repository: Python package layout, `STATUS.md` discipline, config for one source and one buyer, tests, and a local (box-only) data directory that is gitignored except for sanitized samples.
2. **Ingest the best one source** for the pilot buyer: eTenders OCDS, **reusing** PublicFunds' connector, parser, value rules and contact-dropping behaviour (`thusa/connectors/ocds.py`, `thusa/parsers.py`, `thusa/normalise.py`) rather than scraping the eTenders HTML UI. Optionally, a second *read-only* comparison with the City of Cape Town monthly PDF registers (name + decision date), still DEV, still no CIPC field.
3. **Restrict the buyer set** to City of Cape Town (291 awards in the OCP mirror through Sep 2026; the City also publishes monthly registers). No national roll-out in this change.
4. **Match rule:** a supplier on an award is linked to another record (City register row, restricted-supplier entry, or a later registration-year record) only when **at least two details agree** (see §5). Otherwise the link is not made and the field is Unknown.
5. **Young-supplier indicator** as specified in §6, computed only when a registration year is present, and labelled as an indicator, not an accusation.
6. **Fact labels** and **right-of-reply** placeholders as specified in §7–§8.
7. **Tests** on fixtures (including awards that lack a registration year, which is the real-world case).

Out of scope for CHG-TW-001 is listed in §9.

## 4. Data model (pilot)

Each stored fact should carry `value | label | source_url | source_date | retrieved_at`, following PoliticianWatch §3.1 and PublicFunds' "what we don't know" practice.

### 4.1 Award

| Field | Source | Notes |
|---|---|---|
| `ocid` | OCDS | Stable process id (`ocds-9t57fa-…`) |
| `award_id` | OCDS | |
| `buyer_name` / `buyer_id` | OCDS | Pilot filter: City of Cape Town |
| `tender_title` / `tender_id` / `procurement_method` | OCDS | |
| `supplier_name` | OCDS | Normalised key also stored (PublicFunds `norm_name`) |
| `supplier_id_portal` | OCDS | Internal id only; often `0`; not a registration number |
| `cipc_reg_no` | Award payload or later source | Almost always empty today |
| `csd_no` | Award payload or later source | Almost always empty today; stored if a structured or clearly tokenised `MAAA…` appears, never invented |
| `registration_year` | Derived from a CIPC number `YYYY/…`, or from a future year source | Empty if unknown. Never inferred from a CSD number |
| `value_amount` / `value_currency` / `value_note` | OCDS | Keep PublicFunds rules: `0` → unknown/placeholder; flag implausible lows/highs |
| `award_date` / `award_date_basis` | `contract.dateSigned` else `release.date` | `awards.date` is typically empty |
| `source_url` / `source_file` / `sha256` / `retrieved_at` | Fetch metadata | |
| `fact_label` | See §7 | Default for an official award row: Confirmed (the award as published), with value quality in `value_note` |

### 4.2 Supplier (organisation only)

| Field | Notes |
|---|---|
| `display_name` / `name_key` | From the award; juristic name |
| `cipc_reg_no` / `registration_year` | Only if sourced; otherwise Unknown |
| `csd_no` | Only if sourced |
| `young_supplier_indicator` | See §6. Values: `yes`, `no`, `unknown` |
| `indicator_window` | e.g. `registration_year in {award_year, award_year-1}` |
| `right_of_reply` | Always `Right of reply: pending` in this RFC (drafts only; nothing is sent) |
| `evidence` | Pointers to award rows and the year source, each labelled |

No person profile is in the pilot model. No director records.

### 4.3 What we will not store

Director ID numbers, SA ID numbers, home or business street addresses, personal emails, personal phone or fax numbers, tender contact persons, or CSD/CIPC login credentials. If a source payload includes `parties.contactPoint`, `parties.address` (beyond a country name if needed for debugging) or `tender.contactPerson`, those keys are dropped at parse time and must not be written to the warehouse or to git.

## 5. Match rule (at least two agreeing details)

A link between two records that name a supplier is made only when **two or more** of the following agree, after normalisation:

1. Exact CIPC registration number (canonical `YYYY/NNNNNN/NN`).
2. Exact CSD number (canonical `MAAA` + digits), if both sides have one.
3. Normalised organisation name (`norm_name`, legal suffixes stripped) **and** the same buyer or the same jurisdiction (City of Cape Town for the pilot).
4. Official tender / TTS / OCID reference that both records share.

A normalised name alone is not enough (the PublicFunds and PoliticianWatch rule against over-matching). A common trade name in another municipality is not a match. If fewer than two details agree, the records stay unlinked and any derived field is **Unknown**.

This is conservative on purpose. Under-matching is acceptable in DEV; over-matching is not.

## 6. Registration-year signal and the "young supplier" indicator

### 6.1 What the CIPC number can tell us

A South African company registration number of the form `YYYY/NNNNNN/NN` encodes the **year of registration only**, not the month or day. The two-digit suffix is the enterprise type (for example `07` for a private company), not a date. Without a CIPC login or another year source, this year is almost never available from award files (see `SOURCES.md`).

A CSD number (`MAAA…`) does not encode a registration year and must not be used as one.

### 6.2 Definition (when a year is present)

Let `registration_year` be the `YYYY` taken from a sourced CIPC number, and `award_year` the calendar year of `award_date` (using `award_date_basis`).

The **young-supplier indicator** is `yes` when:

`registration_year == award_year` **or** `registration_year == award_year - 1`

Otherwise, if both years are present, the indicator is `no`. If either year is missing, the indicator is `unknown`.

The indicator is a **mechanical comparison of two official public dates**, labelled as an indicator, never as a finding of fraud, fronting, corruption or any other offence. Surrounding wording must stay in that register: "The registration year on the CIPC number is the same as, or the year before, the award year" — not "this company was created to win the tender."

### 6.3 Honest limits

- **Year granularity only.** A company registered in January of `award_year - 1` can be up to 23 months old at an award in December, and would still be flagged `yes`. A company registered in December of `award_year` may be a few weeks old, and is flagged the same way. The idea note's "~1 month before the award" test **cannot** be performed from the number alone.
- **Coverage today is effectively zero** on the pilot source. In DEV, almost every Cape Town award will show `young_supplier_indicator = unknown` and `registration_year = Unknown`. That is the correct output, not a defect.
- **False comfort the other way:** a company can be old on paper and still be a shell; a young company can be a legitimate start-up. The indicator does not distinguish these.
- **Enterprise type and re-registrations** are not interpreted in this RFC.
- **Natural persons and sole traders** are not given a registration year and must not be forced into this indicator.

Until a registration-year source exists, the fixture suite should include synthetic CIPC numbers to prove the rule, and real OCDS rows to prove the Unknown path.

## 7. Fact labels

Copied from the PoliticianWatch rule, applied to awards and indicators:

| Label | Rule |
|---|---|
| **Confirmed** | An official record (eTenders OCDS, City award register, Gazette, court judgment, AGSA, Public Protector or SIU report) or the supplier's own official statement |
| **Reported** | At least one reputable outlet reported it as fact, attributed and linked |
| **Alleged** | A claim by a named party or investigating body that has not been tested. Always shown with the response or "Right of reply: pending" |
| **Disputed** | Sources conflict, or the supplier denies it. Both sides are shown |
| **Unknown** | Not found. Shown as a placeholder: "Not yet found. Know a public source? Tell us." |

For the pilot:

- The existence of an award row taken from eTenders or the City register is **Confirmed** as a publication of that source (the portal's own disclaimer still applies: Treasury does not guarantee completeness or accuracy).
- `registration_year` and `young_supplier_indicator` are **Unknown** unless a sourced CIPC year exists, in which case the *years* are Confirmed as taken from that official identifier, and the *indicator* is a derived label, not an accusation.
- No Reported or Alleged controversy items are in this DEV change.

## 8. Right of reply

No message is sent under this RFC. Any right-of-reply text prepared in DEV is a **draft** for the owner's later GO, and the stored status is exactly:

`Right of reply: pending`

A later change would be needed to contact anyone, and only through an official channel, with a drafted message, a named recipient, and a quoted owner GO. That work is out of scope here.

## 9. Out of scope

- TEST or PROD environments, DNS, GitHub Pages, and the public `GrokForum/tenderwatch-site` placeholder.
- Pushing this repository, creating remotes, or merging to `main` without a GO.
- Any login (CIPC, CSD, eTenders official/supplier, GPW subscription, or other).
- Ingest of the Register of Restricted Suppliers as a new pipeline (already in PublicFunds); a later change may *reuse* it.
- Director, beneficial-ownership, PEP or personal-interest matching.
- National or multi-buyer roll-out; departmental scrapers (DCS, Joburg, Gazette, AGSA) except as documented sources.
- Sending or posting right-of-reply, social, or press messages.
- Accusatory language, scoring "risk" as guilt, or publishing flags that name a supplier without four-eyes review and an owner GO (the PublicFunds rule).
- Paying for data or using paywalled gazette products.

## 10. Environments: DEV / TEST / PROD

| Env | Allowed under this RFC? | Notes |
|---|---|---|
| **DEV** | Yes, after owner GO | Local box only. No production host, database, mailbox or DNS. Data under a gitignored `data/raw/` tree. |
| **TEST** | No | Requires its own change record, CAB decision, drilled rollback, and a quoted owner GO. |
| **PROD** | No | The public site repo exists (`GrokForum/tenderwatch-site`) as a noindex placeholder. It must not be updated under this RFC. |

Promotion, if ever, is same-bytes (same commit or tag) and a separate RFC.

## 11. Risks

| Risk | Mitigation |
|---|---|
| **POPIA / personal information** | Organisation awards only. Drop contacts and addresses at parse time. Never store director IDs, SA IDs, or personal contact details. Four-eyes on anything that would later name a supplier in public. See §4.3 and §13. |
| **Defamation / over-claiming** | Indicator wording only; fact labels; no accusation. Almost all live rows will be Unknown on age, which must remain visible. |
| **Over-matching suppliers** | Two-detail rule; name-only matches rejected. |
| **Licence inconsistency (PDDL vs CC BY 4.0 vs LearnMore terms)** | Attribute National Treasury / OCPO, link to the source and to https://data.etenders.gov.za/Home/LearnMore. Do not claim a single licence as settled. **Unknown** which text controls. |
| **Incomplete coverage** | eTenders is not a complete record of SA procurement (official policy). Portal headline counts (73,785 awards on 17 Nov 2026) dwarf the compiled mirror (9,551). The pilot will say what it does not know. |
| **Unstable API and messy monthly CSV** | Prefer the monthly JSON and the OCP / PublicFunds compiled corpus; treat the API as a best-effort delta, as PublicFunds already does. |
| **Value quality** | Keep PublicFunds placeholder and implausible-value notes; do not present raw amounts as audited. |
| **Year-only indicator is coarse** | Document the 0–23 month window in the UI/copy; never say "registered one month before". |
| **Name collision with tenderwatch.org** | This project is TenderWatch SA. Keep the distinction in copy. |
| **Scope creep into a login** | No login without a new RFC and a quoted GO. |
| **Duplicating PublicFunds** | Reuse, don't fork the ingest (owner question 2). |

## 12. Test plan (DEV)

To be run in DEV after a GO, before any request to merge:

1. Fixture awards for City of Cape Town with supplier name, value and release date, and **no** CIPC number → `registration_year` and `young_supplier_indicator` are Unknown; award itself is Confirmed as sourced.
2. Fixture with CIPC `2026/123456/07` and award date in 2026 → indicator `yes`.
3. Fixture with CIPC `2025/123456/07` and award date in 2026 → indicator `yes`.
4. Fixture with CIPC `2024/123456/07` and award date in 2026 → indicator `no`.
5. Fixture with only a CSD number → year and indicator remain Unknown (CSD is not a year).
6. Match rule: same normalised name, different buyer → no link. Same name + same buyer → link. Same CIPC + same name → link. Name only → no link.
7. Parser drops `contactPoint`, street addresses and `contactPerson`; tests fail if those keys reach the warehouse.
8. A small real-file smoke test on the sanitized samples and, in DEV only, on a PublicFunds OCDS copy or one official monthly JSON, filtered to City of Cape Town, counting Unknown rates.
9. No network login and no write to `tenderwatch-site` or to `origin`.

This RFC's own deliverable (docs + samples) is checked by review, not by a unit test: links dated, Unknown placeholders present, samples include source URL and fetch date, POPIA scan clean.

## 13. POPIA

Companies and official procurement records are the subject of this pilot, not private individuals.

Never store: director ID numbers, SA ID numbers, passport numbers, home or street addresses, personal emails, personal phones, or family details.

Present suppliers as named on the official source, with fact labels. The young-supplier flag is an indicator from dates, not a finding against a person.

Identity linking follows the two-detail match rule. Temporary fetch files that might contain contacts are kept out of git and should be deleted when the task ends.

**POPIA check of this RFC, `SOURCES.md` and `data/samples/`:** PASS. No ID numbers, addresses, phones, emails or private contacts are included. Sole-trader personal names were not copied from City registers.

## 14. Rollback

Rollback is git. Before any later implementation commit, record the pre-change SHA (this branch is based on `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` on `main`).

- To abandon implementation work on `rfc/CHG-TW-001`: `git switch main` and leave or delete the branch. `main` stays at the initial commit until a GO.
- To undo a later DEV implementation commit: `git revert` or reset the branch to the SHA recorded in this RFC / `STATUS.md`. No `.bkp` files.
- Nothing is deployed, so there is no production rollback to drill under this RFC.

## 15. Owner questions

1. **Proceed or park?** Given 0% CIPC coverage on public awards, do you want a Cape Town awards-register pilot in DEV that leaves supplier age as Unknown (this RFC), or should TenderWatch stay parked until a free registration-year source exists?
2. **New bot vs PublicFunds extension?** PublicFunds already ingests eTenders OCDS and has the award model, value rules and four-eyes review. Should TenderWatch SA be a thin product on top of that warehouse, a new detector inside PublicFunds, or a separate bot that reuses the connector only?
3. **Pilot buyer.** Confirm City of Cape Town. The alternative with more OCDS awards is Public Works (417), which is a national department, not a single metro.
4. **Indicator window.** Confirm the year rule (`registration_year` equal to the award year or the year before), with the 0–23 month limitation written on the label — or specify a different rule, knowing that month-level "about one month before" is not possible from the number.
5. **Right of reply and naming.** For a later change, not this one: may we draft (not send) right-of-reply notes to official City / supplier channels if an indicator is ever `yes`? Flags that would name a supplier in public would follow PublicFunds four-eyes plus your GO.
6. **Licence and attribution.** Are you content to attribute National Treasury / OCPO and link to the source while the PDDL / CC BY 4.0 / LearnMore wording remains inconsistent, or should we first draft (not send) an enquiry to `cpo@treasury.gov.za`?

No question in this list is a GO. A GO must name this RFC (CHG-TW-001), the environment (DEV), and the exact change.

## 16. CAB review

Reviewers: **Cavus** and **Cassian**, as four checks (expert, shadow, charter, drift). They review this draft; they do not implement it under this record, and they cannot authorise TEST, PROD, a push, or a send.

Implementation starts only after: (a) both reviewers have signed the draft or a revised draft, and (b) the owner gives a quoted GO for CHG-TW-001 in DEV.

**Result:** (blank — DRAFT, awaiting review)

---
*POPIA check: PASS. See §13.*
