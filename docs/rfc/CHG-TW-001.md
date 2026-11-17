# CHG-TW-001 — TenderWatch SA DEV pilot: source survey, scaffold plan, one-source one-buyer ingest and young-supplier indicator

**Status:** DRAFT for CAB review. Not implemented. No SUCCEEDED / FAILED yet.
**Environment:** DEV only. DEV must not point at a production host, database, mailbox or DNS.
**Date:** 17 Nov 2026, Africa/Johannesburg (SAST).
**Author:** TenderWatch (Grok Bot), from the parked idea note and the 17 Nov 2026 source survey.
**CAB reviewers:** Cavus (expert / charter) and Cassian (shadow / drift). Sign-off must be by someone other than the author. The owner's GO is required before any implementation is merged to `main`, before any push, and before anything is published or sent.
**Pre-change SHA:** `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` (`main`, initial commit). Work lives on branch `rfc/CHG-TW-001`.
**Related:** `SOURCES.md` (evidence), `IDEA-tenderwatch.md` (parked idea, 16 Nov 2026), PublicFunds `/workspace/publicfunds`.
**Owner decision 17 Nov 2026 (relayed by Cavus):** TenderWatch goes ahead as a PublicFunds extension, kept on its own separate track. That decision is recorded in §16. It is not a GO to implement, merge, push or publish.
**Model:** PoliticianWatch SA planning packet and PublicFunds SA change discipline.

This change record describes proposed DEV work. The branch holds the survey, the RFC, sanitized samples, a supplier-type classifier with tests, and the identifier-count script. It does not yet ingest a warehouse or publish a site.

---

## 1. Summary

TenderWatch SA was parked because CIPC lookups need a login, and there is no GO for any login. The revival hypothesis was that public award data might already carry CIPC registration numbers (format `YYYY/NNNNNN/NN`, year only) or CSD numbers, so a "young winning supplier" indicator could be built without that login.

The 17 Nov 2026 survey does **not** support that hypothesis for structured award data:

- **0 / 9,551 (0%)** of award–supplier rows in the eTenders OCDS full mirror carry a supplier CIPC number. The only CIPC number in the corpus is Transnet's own.
- **11 / 9,551 (0.12%)** of winner names contain a CSD-like `MAAA…` token, not as a field. A CSD number does not encode registration year.
- Official July 2026 monthly OCDS: **0 / 42** CIPC, **0 / 42** CSD.
- City of Cape Town October 2026 award register: **0 / 24** tender references with CIPC or CSD.

What *is* feasible, without any login, is a **neutral, sourced awards register** for one buyer, reused from PublicFunds' existing eTenders ingest as a read-only upstream. The registration-year signal should still be specified, tested with fixtures, and shown as **Unknown** by default until a free public document supplies a CIPC year, or publishers start emitting CIPC numbers.

**Owner decision 17 Nov 2026 (relayed by Cavus):** TenderWatch goes ahead as a PublicFunds extension, kept on its own **separate track**. In practice that means:

- a **separate repo** (`GrokForum/tenderwatch-sa`) and a **separate change track** (`CHG-TW-*`, not PublicFunds' `CHG-2026-*` numbers);
- **reuse** of PublicFunds' `etenders_ocds` ingest as a **read-only upstream or pinned dependency** (a pinned PublicFunds commit or tag, or its warehouse / raw OCDS outputs / connector, consumed without editing that repo);
- **no changes to PublicFunds** without a PublicFunds RFC of its own, with that project's CAB and a quoted owner GO;
- a **separate public site** (`GrokForum/tenderwatch-site`), not a page on publicfunds.grokforum.site.

That decision resolves the proceed-or-park question and the extension-versus-new-bot question. It is **not** a GO to implement this RFC, merge to `main`, push, or publish.

**DEV pilot (DEV GO given 17 Nov 2026; PR #1 merged as `fb5a4bcc`):** one source (eTenders OCDS, read-only reuse of PublicFunds) and one buyer set (City of Cape Town). No TEST, no PROD, no site publish, no right-of-reply messages sent (drafts only, labelled `Right of reply: pending`). Identifier strategy is proposed in §15 and put to the owner in §16.

## 2. Motivation

The idea note (`IDEA-tenderwatch.md`) describes a public-interest pattern: a company that wins a government award very soon after it is registered. That is an *indicator*, not proof of wrongdoing. To compute it we need (a) an official award with a supplier and a date, and (b) the supplier's registration year. (a) is publicly available and already ingested by PublicFunds. (b) is not, on the sources that can be used without a login.

The honest options were: park the product again; build the awards register now and leave age as Unknown; or wait for a free registration-year source. **Owner decision 17 Nov 2026 (relayed by Cavus):** the first option is declined. TenderWatch goes ahead as a PublicFunds extension on a separate track, which is the middle path: a DEV awards register that reuses PublicFunds' ingest, with the age indicator specified and shown as Unknown until a free year source appears. That decision does not by itself authorise implementation.

## 3. Scope (DEV only)

In scope, after a written owner GO that names this RFC and the exact commit, and only on DEV:

1. **Scaffold** this repository: Python package layout, `STATUS.md` discipline, config for one source and one buyer, tests, and a local (box-only) data directory that is gitignored except for sanitized samples.
2. **Ingest the best one source** for the pilot buyer: eTenders OCDS, by **reusing PublicFunds' `etenders_ocds` ingest as a read-only upstream or pinned dependency** (connector, parser, value rules and contact-dropping behaviour in `thusa/connectors/ocds.py`, `thusa/parsers.py`, `thusa/normalise.py`, or the warehouse / raw files those produce). Do not scrape the eTenders HTML UI. Do not edit the PublicFunds repo under this RFC. Optionally, a second *read-only* comparison with the City of Cape Town monthly PDF registers (name + decision date), still DEV, still no CIPC field in that register.
3. **Restrict the buyer set** to City of Cape Town (291 awards in the OCP mirror through Sep 2026; the City also publishes monthly registers). No national roll-out in this change.
4. **Match rule:** a supplier on an award is linked to another record (City register row, restricted-supplier entry, or a later registration-year record) only when **at least two details agree** (see §5). Otherwise the link is not made and the field is Unknown.
5. **Young-supplier indicator** as specified in §6, computed only when a registration year is present, and labelled as an indicator, not an accusation.
6. **Fact labels** and **right-of-reply** placeholders as specified in §7–§8.
7. **Tests** on fixtures (including awards that lack a registration year, which is the real-world case).

**Dependencies (separate track).** This repo is the only place CHG-TW-* changes land. PublicFunds is an upstream: pin a commit or tag, or read its published/local OCDS outputs, and record the pin in config. If PublicFunds itself must change (for example a connector bug that blocks the pilot), that work is a PublicFunds RFC, not a TenderWatch commit. The public site, when a later RFC allows it, is `GrokForum/tenderwatch-site`, not the PublicFunds dashboard.

Supplier-identifier options, and a recommended default for the owner to confirm, are in §15.

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
| `supplier_type` | Classifier on the supplier name (see §4.4) | `juristic` / `natural_person` / `unknown` |
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
| `display_name` / `name_key` | From the award. `display_name` may appear in a public export only when `supplier_type` is `juristic` |
| `supplier_type` | `juristic` / `natural_person` / `unknown`. See §4.4 |
| `cipc_reg_no` / `registration_year` | Only if sourced and the supplier is juristic; otherwise Unknown |
| `csd_no` | Only if sourced |
| `young_supplier_indicator` | See §6. Values: `yes`, `no`, `unknown`. Computed only when `supplier_type` is `juristic` |
| `indicator_window` | `registration_year` is the award year or the year before (0–23 months, stated on the label) |
| `age_band` | For every juristic supplier with a sourced year: `same` (reg year = award year), `-1`, `-2`, or `older`. `unknown` when there is no sourced year or the supplier is not juristic. Recorded so the bands can be trended. `-2` is shown for trends only and does not set the indicator. See §6 and §16 Q4. |
| `right_of_reply` | Always `Right of reply: pending` in this RFC (drafts only; nothing is sent) |
| `evidence` | Pointers to award rows and the year source, each labelled |

No person profile is in the pilot model. No director records.

### 4.3 What we will not store

Director ID numbers, SA ID numbers, home or business street addresses, personal emails, personal phone or fax numbers, tender contact persons, or CSD/CIPC login credentials. If a source payload includes `parties.contactPoint`, `parties.address` (beyond a country name if needed for debugging) or `tender.contactPerson`, those keys are dropped at parse time and must not be written to the warehouse or to git.

### 4.4 `supplier_type` classifier

`supplier_type` is derived only from the official supplier name, in this order:

1. **`natural_person`** if the name contains `t/a` or `trading as` (even when the trading style has a juristic suffix), or if the whole name matches an initials-plus-surname pattern (one to three initials, optional particles such as van/de/du, then a surname, and nothing else).
2. **`juristic`** if, after normalisation, the name **ends** with a legal suffix such as Pty Ltd, (Pty) Ltd, Ltd, Limited, Inc, Incorporated, NPC, SOC, SOC Ltd, CC, Close Corporation, JV, Joint Venture, (RF), RF or Proprietary Limited. Those tokens are never matched as bare words in the middle of a name (so "Limited Edition Printers", "Inc Design Studio" and "Rf Holdings" are not juristic).
3. **`unknown`** for everything else, including empty names, organisation-like strings with no recognised trailing suffix (common in the eTenders dump), and names ending in **Trust** (Trust is not a recognised juristic suffix). A family trust can carry a private person's name, so "Trust" is not treated as juristic unless a later, named check (out of scope here) says otherwise.

The young-supplier indicator is computed **only** for `juristic` suppliers. Names classified `natural_person` or `unknown` must **never** appear in any public output (they may be stored internally for matching, then withheld or replaced with a placeholder in any export or page). The classifier lives in `tw/supplier_type.py` and is covered by synthetic fixture tests in `tests/test_supplier_type.py` (no real private people's names).

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

The indicator is computed **only** when `supplier_type` is `juristic`. For `natural_person` and `unknown` it is always `unknown`, even if a year string happens to be present, and those names are withheld from public output.

Let `registration_year` be the `YYYY` taken from a sourced CIPC number, and `award_year` the calendar year of `award_date` (using `award_date_basis`).

For a juristic supplier the **young-supplier indicator** is `yes` when:

`registration_year == award_year` **or** `registration_year == award_year - 1`

That window is 0–23 months and must be stated on the label. Otherwise, if both years are present, the indicator is `no`. If either year is missing, or the supplier is not juristic, the indicator is `unknown`.

For every juristic supplier with a sourced year, also record **`age_band`** so the series can be trended (owner decision, §16 Q4):

| `age_band` | When | Indicator |
|---|---|---|
| `same` | `registration_year == award_year` | `yes` |
| `-1` | `registration_year == award_year - 1` | `yes` |
| `-2` | `registration_year == award_year - 2` | `no` (`-2` is shown for trends only and does not set the indicator) |
| `older` | `registration_year < award_year - 2` | `no` |
| `unknown` | No sourced year, years missing, or the supplier is not juristic | `unknown` |

A registration year after the award year is `unknown` (not a trend band) until a later change says otherwise.

The indicator is a **mechanical comparison of two official public dates**, labelled as an indicator, never as a finding of fraud, fronting, corruption or any other offence. Surrounding wording must stay in that register: "The registration year on the CIPC number is the same as, or the year before, the award year (0–23 months)" — not "this company was created to win the tender."

### 6.3 Honest limits

- **Year granularity only.** A company registered in January of `award_year - 1` can be up to 23 months old at an award in December, and would still be flagged `yes`. A company registered in December of `award_year` may be a few weeks old, and is flagged the same way. The idea note's "~1 month before the award" test **cannot** be performed from the number alone.
- **Coverage today is effectively zero** on the pilot source. In DEV, almost every Cape Town award will show `young_supplier_indicator = unknown` and `registration_year = Unknown`. That is the correct output, not a defect.
- **False comfort the other way:** a company can be old on paper and still be a shell; a young company can be a legitimate start-up. The indicator does not distinguish these.
- **Enterprise type and re-registrations** are not interpreted in this RFC.
- **Natural persons, sole traders, `unknown` names, and trusts** are not given a registration year and must not be forced into this indicator. A name with "Trust" is classified `unknown` unless further checked, because a family trust can carry a private person's name. These names must never appear in any public output.

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

- TEST or PROD environments, DNS, GitHub Pages, and any update to the separate public site `GrokForum/tenderwatch-site` (the placeholder stays untouched under this RFC).
- Pushing this repository, creating remotes, or merging to `main` without a GO.
- Any change to the PublicFunds repository, pipeline, warehouse schema or public dashboard. Those need a PublicFunds RFC, CAB and a quoted owner GO. This RFC may only *read* a pinned PublicFunds ingest.
- Any login (CIPC, CSD, eTenders official/supplier, GPW subscription, or other), and any paid CIPC or company-data bulk feed (see §15(e)).
- Ingest of the raw Register of Restricted Suppliers PDF as a new pipeline (it contains SA ID numbers and is already ingested, with redaction, by PublicFunds). A later TenderWatch change may *reuse* PublicFunds' redacted RSR output as a read-only cross-reference (see §15(c)).
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
| **PROD** | No | The separate public site repo exists (`GrokForum/tenderwatch-site`) as a noindex placeholder. It is the intended future site for this track, and it must not be updated under this RFC. |

Promotion, if ever, is same-bytes (same commit or tag) and a separate RFC.

## 11. Risks

| Risk | Mitigation |
|---|---|
| **POPIA / personal information** | Organisation awards only. Drop contacts and addresses at parse time. Never store director IDs, SA IDs, or personal contact details. Four-eyes on anything that would later name a supplier in public. See §4.3 and §13. |
| **Defamation / over-claiming** | Indicator wording only; fact labels; no accusation. Almost all live rows will be Unknown on age, which must remain visible. |
| **Over-matching suppliers** | Two-detail rule; name-only matches rejected. |
| **Licence inconsistency (PDDL vs CC BY 4.0 vs LearnMore terms)** | Attribute National Treasury / OCPO, link to the source and to https://data.etenders.gov.za/Home/LearnMore. Do not claim a single licence as settled. **Unknown** which text controls; owner decided 17 Nov 2026 to proceed with credit plus links (§16 Q6). |
| **Incomplete coverage** | eTenders is not a complete record of SA procurement (official policy). Portal headline counts (73,785 awards on 17 Nov 2026) dwarf the compiled mirror (9,551). The pilot will say what it does not know. |
| **Unstable API and messy monthly CSV** | Prefer the monthly JSON and the OCP / PublicFunds compiled corpus; treat the API as a best-effort delta, as PublicFunds already does. |
| **Value quality** | Keep PublicFunds placeholder and implausible-value notes; do not present raw amounts as audited. |
| **Year-only indicator is coarse** | Document the 0–23 month window in the UI/copy; never say "registered one month before". |
| **Name collision with tenderwatch.org** | This project is TenderWatch SA. Keep the distinction in copy. |
| **Scope creep into a login** | No login without a new RFC and a quoted GO. |
| **Duplicating or editing PublicFunds** | Resolved as a separate track (owner decision 17 Nov 2026, relayed by Cavus): reuse `etenders_ocds` as a read-only upstream or pinned dependency; make no PublicFunds changes under CHG-TW-*. |
| **Upstream drift** | Pin a PublicFunds commit or tag and record it. If the pin breaks the pilot, raise a PublicFunds RFC rather than patching that repo from this one. |

## 12. Test plan (DEV)

To be run in DEV after a GO, before any request to merge:

1. Fixture awards for City of Cape Town with a juristic supplier name, value and release date, and **no** CIPC number → `registration_year` and `young_supplier_indicator` are Unknown; award itself is Confirmed as sourced.
2. Juristic fixture with CIPC `2026/123456/07` and award date in 2026 → indicator `yes`, `age_band` `same`.
3. Juristic fixture with CIPC `2025/123456/07` and award date in 2026 → indicator `yes`, `age_band` `-1`.
4. Juristic fixture with CIPC `2024/123456/07` and award date in 2026 → indicator `no`, `age_band` `-2` (trend only; does not set the indicator).
4a. Juristic fixture with CIPC `2023/123456/07` and award date in 2026 → indicator `no`, `age_band` `older`.
5. Fixture with only a CSD number → year and indicator remain Unknown (CSD is not a year).
6. Match rule: same normalised name, different buyer → no link. Same name + same buyer → link. Same CIPC + same name → link. Name only → no link. A link on fewer than two agreeing details must fail the test.
7. Parser drops `contactPoint`, street addresses and `contactPerson`; tests fail if those keys reach the warehouse.
8. A small real-file smoke test on the sanitized samples and, in DEV only, on a *read-only* pinned PublicFunds OCDS copy (`main` `de37f666`, see §18) or one official monthly JSON, filtered to City of Cape Town, counting Unknown rates.
9. No network login and no write to `tenderwatch-site` or to `origin`.
10. `supplier_type` classifier fixtures in `tests/test_supplier_type.py` (synthetic names only): a *trailing* legal suffix → `juristic`; `t/a` and initials-plus-surname → `natural_person`; "Trust" and bare mid-name words such as Limited/Inc/RF → `unknown`.
11. The indicator stays `unknown` for `natural_person` and `unknown` types even when a registration year is present.
12. A public-export helper emits **zero** non-juristic names (`natural_person` and `unknown` are withheld).

This RFC's own deliverable (docs + samples) is checked by review, not by a unit test: links dated, Unknown placeholders present, samples include source URL and fetch date, POPIA scan clean.

## 13. POPIA

Companies and official procurement records are the subject of this pilot, not private individuals.

Never store: director ID numbers, SA ID numbers, passport numbers, home or street addresses, personal emails, personal phones, or family details.

Present **juristic** suppliers as named on the official source, with fact labels. The young-supplier flag is an indicator from dates, computed only for juristic suppliers, not a finding against a person.

`supplier_type` is classified from the name as in §4.4. Names classified `natural_person` or `unknown` must **never** appear in any public output. Classifier tests use synthetic names only; they must not use the names of real private people.

Identity linking follows the two-detail match rule. Temporary fetch files that might contain contacts are kept out of git and should be deleted when the task ends.

**POPIA check of this RFC (including §4.4, §15–§16 and §18), `SOURCES.md`, `data/samples/`, `tw/` and `tests/`:** PASS. No ID numbers, addresses, phones, emails or private contacts are included. Sole-trader personal names were not copied from City registers. Classifier fixtures are invented strings (e.g. "Alex Q. Testperson t/a Testperson Crafts"). Option (c) records that the raw Restricted Suppliers Register contains SA ID numbers and must not be stored here. Fixture CIPC numbers in §12 are synthetic.

## 14. Rollback

Rollback is git. Before any later implementation commit, record the pre-change SHA (this branch is based on `b812102eb8d5eea0c6a486e8a332a1bf62e08d76` on `main`).

- To abandon implementation work on `rfc/CHG-TW-001`: `git switch main` and leave or delete the branch. `main` stays at the initial commit until a GO.
- To undo a later DEV implementation commit: `git revert` or reset the branch to the SHA recorded in this RFC / `STATUS.md`. No `.bkp` files.
- Nothing is deployed, so there is no production rollback to drill under this RFC.

## 15. Supplier-identifier options (for the owner to choose)

Awards almost never carry a CIPC number, so a stable supplier identity has to be built from weaker public signals. None of the options below is a CIPC login. Each is scored against the two-detail match rule in §5, against measured coverage from the 17 Nov 2026 survey (`SOURCES.md`), and against POPIA. Option (e) is listed only so the choice set is complete; it is out of scope and is **not recommended**.

### (a) Normalised supplier-name matching across awards (internal `name_key`)

Give each award a stable internal supplier key by running PublicFunds' `norm_name` (case, punctuation, legal suffixes, `t/a` splits) on the official supplier name, and group awards that share that key **and** the pilot buyer (City of Cape Town).

- **Pros.** Available on every award that has a name, which in the OCDS mirror was all **9,551 / 9,551** award–supplier rows (PublicFunds' landscape counted **7,468** distinct supplier names in that corpus). No login. Already implemented as `supplier_key` in PublicFunds. Lets the pilot show repeat awards to the same normalised name at the same buyer.
- **Cons.** It is a spelling key, not a legal identity. Trading names, joint ventures, abbreviations and capture errors will both over- and under-match. It does not yield a registration year or an age indicator. Portal `supplier_id` values are not a substitute: **3,575 / 9,551** were `0` in the mirror.
- **Expected coverage.** Near 100% of named awards can receive a `name_key`. For the Cape Town pilot that is **291** OCDS awards in the mirror. The key does not claim that two different spellings are the same company.
- **Two-detail rule.** **Yes**, inside the pilot, if the second detail is the buyer or jurisdiction: normalised name **and** City of Cape Town. Normalised name alone, across buyers, is **not** enough and must not be used to merge suppliers.
- **POPIA.** Store official organisation names only. Do not turn a sole-trader or "t/a" personal name into a person profile. No IDs, addresses or contacts.

### (b) CSD `MAAA…` numbers where present (identifier only, not an age signal)

When a winner row or a clearly joinable tenderer row carries a tokenised CSD number, store it as `csd_no`. Never treat it as a registration year (see §6.1).

- **Pros.** When present, it is a stable official supplier number and a strong first detail for the match rule. It is an organisation identifier, not an SA ID number. No login is required to *keep* a number that already appears in the public award payload.
- **Cons.** It is almost never present as a structured field (the OCDS `Identifier` schema exposes `legalName` only). Where it appears, it is often messy (the name or title *is* the `MAAA…` string; values are sometimes a zero placeholder). A CSD number does **not** encode a year, so it does not feed the young-supplier indicator.
- **Expected coverage (measured).** Structured field: **0 / 9,551**. `MAAA…` in the winning supplier name or id: **11 / 9,551 (0.12%)**. Additional winners whose name could be joined to a `tender.tenderers` entry that includes a `MAAA…` prefix, under the rule in `SOURCES.md` §1.4 and `scripts/count_identifiers.py`: **68 / 9,551 (0.71%)**. Official July 2026 monthly JSON: **0 / 42**. City of Cape Town October 2026 register: **0 / 24**. The tenderers join is fuzzier than a structured field and should be accepted only when the winner name clearly agrees with that tenderer row.
- **Two-detail rule.** **Yes**, when an exact canonical `MAAA…` **and** a normalised name agree. A CSD number alone is one detail, not two. A loose join from a tenderers list without a name agreement is **not** a match.
- **POPIA.** Store the organisation CSD number and the official name. Do not use a CSD login or organ-of-state search to look numbers up. Do not keep any personal contact data that might sit near the token in free text.

### (c) Public CSD Restricted Suppliers Register as a cross-reference (barred list only)

Use the official barred-supplier list as a *cross-check* against pilot awards ("barred and awarded"), not as a general identifier for every supplier. The list is already ingested, with redaction, by PublicFunds. This track should only *read* that redacted output, if at all.

- **Pros.** Public, official, and already in PublicFunds. Juristic entries often carry a CIPC number, which can both identify a supplier and, if linked under the two-detail rule, supply a registration year. Useful as an indicator in the same register as age, still labelled as an indicator, not an accusation.
- **Cons.** It is a barred list, not an awards file and not a population-wide identifier. Most Cape Town winners will not appear on it. PublicFunds' landscape already notes under-matching on name when awards lack registration numbers (a third-party site matched 32 of 409 restricted entries for the same reason). The raw PDF contains SA ID numbers for natural persons.
- **Expected coverage.** The PublicFunds load of the report generated 15 Sep 2026 had **409** entries (228 of them natural persons). Overlap with the 291 Cape Town OCDS awards was **not measured** in this survey (**Unknown**). Award-side CIPC coverage remains **0%**, so any match will usually have to rely on name plus another detail, which will under-match.
- **Two-detail rule.** **Yes** for a juristic RSR row that has a CIPC number **and** an agreeing normalised name (or CIPC + shared official reference). Name-only matches to the RSR are **not** allowed. Natural-person RSR rows are out of the pilot.
- **POPIA.** High risk if the raw PDF is ingested here. **Never store director or SA ID numbers.** Do not copy the raw RSR PDF into this repo. If this option is later accepted, reuse only PublicFunds' already-redacted / HMAC'd RSR output as a read-only upstream, and keep only juristic organisations. This is not part of the recommended DEV default below.

### (d) Registration year from free public documents, opportunistic (Confirmed, with a source link)

If a CIPC number `YYYY/NNNNNN/NN` appears in a free, no-login public document that can be tied to the same supplier — for example a Gazette notice, a municipal award or contract register, or an AGSA finding — store the number and the derived `registration_year` with label **Confirmed**, a source URL, and the document date. Compute the young-supplier indicator only then. Otherwise leave year and indicator as **Unknown**.

- **Pros.** No login. The year comes from an official identifier in a cited public document. The Confirmed label and the link keep the claim auditable. Fits the "what we don't know" practice for every other row.
- **Cons.** This is opportunistic, not a complete pipeline. The sources already sampled are almost empty of supplier CIPC numbers. Some contract PDFs that do contain a number also contain addresses and signatories; those documents must not be ingested wholesale. Paywalled gazette products stay out of scope.
- **Expected coverage.** eTenders OCDS suppliers: **0 / 9,551**. City of Cape Town October 2026 monthly register: **0 / 24**. Gazette and AGSA field coverage in this survey: **Unknown**. Occasional official contract documents may carry a number; that does not change the default, which remains Unknown.
- **Two-detail rule.** **Yes**, if the document carries the CIPC number **and** the organisation name (or the name **and** a shared tender / TTS / OCID reference). A number found in a document that does not clearly name the award winner is **not** attached.
- **POPIA.** Store only the organisation name, the CIPC number, the year derived from it, and the source URL and date. Drop addresses, signatories, contact details and any ID numbers that may appear in the same document.

### (e) A CIPC login or bulk paid company data — out of scope, not recommended

A CIPC login, a paid company-search product, or a licensed bulk register would be the only currently obvious way to obtain registration years at scale. It is recorded here so the owner can see the alternative, not so it is pursued.

- **Pros.** Would likely fill `registration_year` for a large share of juristic winners and make the young-supplier indicator computable in the wild, which public award files cannot do today.
- **Cons.** A login or a purchase is blocked without a **named owner GO** for that exact surface. This is why the idea was parked on 16 Nov 2026. Paid or logged-in data may add licence and redistribution limits. The CIPC beneficial-ownership register remains restricted. This RFC **does not recommend** option (e).
- **Expected coverage.** Not measured. Not pursued under this change.
- **Two-detail rule.** An official CIPC number plus an agreeing name would satisfy the rule, but the source itself is out of scope.
- **POPIA.** Company-register products can expose directors and ID numbers. That data must not be fetched or stored. Out of scope.

### Recommended default (a question, not a GO)

The recommended default is **(a) + (b)**, with **(d) as an opportunistic add-on**, and with the **young-supplier indicator shown as Unknown by default**:

- every Cape Town award gets a `name_key` (name + buyer);
- a `csd_no` is stored only when a measured, clearly tokenised `MAAA…` is present and the name agrees (expected on the order of **0.12%** of winners, or **68 / 9,551 (0.71%)** if a careful tenderers join is also accepted);
- a `cipc_reg_no` / `registration_year` is stored only when a free public document supplies it under the two-detail rule, labelled Confirmed and linked;
- option (c) is left for a later change, and only as a read-only reuse of PublicFunds' redacted RSR, not as a general identifier;
- option (e) stays out of scope unless the owner later gives a named GO, which this RFC does not ask for.

This default is put to the owner as question 7 in §16.

## 16. Owner questions and decisions

### Decisions already taken

**Owner decision 17 Nov 2026 (relayed by Cavus):** TenderWatch goes ahead as a PublicFunds extension, kept on its own separate track.

1. **Proceed or park? — Resolved.** The project proceeds. It is not parked pending a registration-year source. Supplier age will be Unknown by default, as the survey measured.
2. **New bot vs PublicFunds extension? — Resolved.** TenderWatch is a PublicFunds extension on a **separate track**: its own repo (`GrokForum/tenderwatch-sa`), its own change series (`CHG-TW-*`), reuse of PublicFunds' `etenders_ocds` ingest as a **read-only upstream or pinned dependency**, **no changes to PublicFunds** without a PublicFunds RFC, and a **separate public site** (`GrokForum/tenderwatch-site`).
3. **Pilot buyer? — Resolved**, implied by the owner's 17 Nov 2026 acceptance of Q7, which named the Cape Town buyer set. The pilot buyer is the City of Cape Town. The owner can reopen this.

Those decisions are not a GO to implement, merge, or publish. A GO must still name this RFC (CHG-TW-001), the environment (DEV), and the exact change.

### Resolved after the 17 Nov decisions

7. **Supplier-identifier default. — Resolved 17 Nov 2026 (owner, directly in TenderWatch chat).** The recommended default in §15 was accepted: (a) + (b) + opportunistic (d); young-supplier indicator Unknown by default; (c) deferred to a later change; (e) out of scope. Coverage figures used in that recommendation, as reproduced by `scripts/count_identifiers.py`, are **11 / 9,551 (0.12%)** of winner names or ids with a CSD token, and **68 / 9,551 (0.71%)** via the documented tenderers join. This is not a GO to implement, merge, or publish; CAB review (§17) still applies.

### Remaining owner questions

The following remain open. They are not a GO. A GO must name this RFC (CHG-TW-001), the environment (DEV), and the exact change.

4. **Indicator window.** Confirm the year rule (`registration_year` equal to the award year or the year before), with the 0–23 month limitation written on the label — or specify a different rule, knowing that month-level "about one month before" is not possible from the number.
   - **Resolved 17 Nov 2026 (owner, directly in TenderWatch chat):** the indicator is `yes` when `registration_year` is the award year or the year before (0–23 months, stated on the label). In addition, record an age band for every juristic supplier with a sourced year, `same` (reg year = award year), `-1` and `-2`, so the bands can be trended over time; `-2` is shown for trend only and does not set the indicator. Unknown when no sourced year.
5. **Right of reply and naming.** For a later change, not this one: may we draft (not send) right-of-reply notes to official City / supplier channels if an indicator is ever `yes`? Flags that would name a supplier in public would follow PublicFunds four-eyes plus your GO.
   - **Resolved 17 Nov 2026 (owner, directly in TenderWatch chat): yes.** In a later change, TenderWatch may draft right-of-reply notes to official City or supplier channels when an indicator is `yes`. Drafts only; the owner sends personally and records stay `Right of reply: pending` until he records the outcome. Public naming still follows PublicFunds four-eyes plus the owner's GO.
6. **Licence and attribution.** Are you content to attribute National Treasury / OCPO and link to the source while the PDDL / CC BY 4.0 / LearnMore wording remains inconsistent, or should we first draft (not send) an enquiry to the contact address published on the eTenders LearnMore page?
   - **Resolved 17 Nov 2026 (owner, directly in TenderWatch chat): credit plus links.** Attribute National Treasury / OCPO and link to the source and the LearnMore policy. No enquiry. All three texts (LearnMore, CC BY 4.0, PDDL) permit reuse; attribution satisfies the strictest. The inconsistency stays logged in SOURCES.md and §11.

## 17. CAB review

Reviewers: **Cavus** and **Cassian**, as four checks (expert, shadow, charter, drift). They review this draft; they do not implement it under this record, and they cannot authorise TEST, PROD, or a send. Review-branch pushes are done by Cavus under the owner's standing GO, given in Cavus's chat on 17 Nov 2026 and relayed by Cavus: "You can push review branches without asking". Merges and publishing still need the owner's GO on the exact head.

Implementation starts only after: (a) both reviewers have signed the draft or a revised draft, and (b) the owner gives a quoted GO for CHG-TW-001 in DEV.

**Result:** Cavus, on `c75e5ef`: **PASS_WITH_CONCERNS** (addressed in `009ea171`). Cavus, on `009ea171` (draft PR #1, pushed 17 Nov 2026 11:59 SAST): **PASS_WITH_CONCERNS**. The remaining concerns (standing-GO citation, trailing-suffix / Trust classification, and the STATUS push record) are addressed in the revision after that SHA. Cassian: not yet recorded. Still DRAFT; not a GO to implement, merge, or publish.

## 18. DEV acceptance criteria

These are the measurable conditions for a later DEV implementation of CHG-TW-001, once the owner has given a quoted GO. They are not satisfied by this docs-and-classifier revision alone, except where a test already exists.

The PublicFunds pin is **`main` `de37f666`** (full SHA `de37f666c12d1d6b7a815860894af0372514ba7f`). It was verified on 17 Nov 2026 in `/workspace/publicfunds`: the object exists, the commit date is 17 Nov 2026 11:29:14 SAST, and the subject is `Merge pull request #12 from GrokForum/chg-2026-063-robots-noindex`. It is the tip of that clone's `origin/main`. At verification the local checkout (`HEAD` / `main`) was `7cb9faf`, an earlier public-data refresh at 03:20 SAST the same day, so the working tree was behind the pin. The survey counts in `SOURCES.md` were taken from the local PublicFunds copy of `src/full.jsonl.gz` (SHA-256 `a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225`, fetched 19 Oct 2026 09:38 SAST), which is a raw file and is not itself stored in that git commit.

A DEV implementation succeeds only if all of the following hold:

1. **Ingest runs end to end** from the pinned PublicFunds `etenders_ocds` data (read-only; pin `de37f666` recorded in config), without editing the PublicFunds repo.
2. **City of Cape Town awards are loaded** into the local DEV warehouse, each with a source URL (or an equivalent source locator plus the retrieval record).
3. **The two-detail match rule is enforced:** tests fail if a link is made on fewer than two agreeing details (see §5 and §12 item 6).
4. **`supplier_type` is classified** as in §4.4, and the fixture tests in `tests/test_supplier_type.py` pass.
5. **The young-supplier indicator is `unknown`** unless a sourced registration year exists **and** the supplier is juristic. It is never computed as yes or no for `natural_person` or `unknown`.
6. **POPIA tests pass:** contacts and addresses do not reach the warehouse; classifier fixtures remain synthetic; no ID numbers are stored.
7. **Zero non-juristic names in the public export:** every `natural_person` and `unknown` supplier name is withheld (see `public_export_rows`).
8. **Age bands** are recorded for every juristic supplier with a sourced year: `same`, `-1`, `-2`, or `older` (and `unknown` when there is no sourced year). The indicator is `yes` only for `same` and `-1` (award year or the year before; 0–23 months, stated on the label). `-2` is stored for trends and does not set the indicator. Consistent with §16 Q4.

## 19. Publish preconditions

These rules apply before any later publish (this RFC does not authorise a publish). They do not change the DEV warehouse, which may still store name-plus-buyer links for exploration.

1. **Tight matches only.** A link may be presented as a confirmed or tight match only when the records **share a tender reference** (TTS / tender id / OCID, §5 item 4). A link that agrees only on a normalised name plus the same buyer or jurisdiction is a **name-only match within one buyer**. It must not be presented as a confirmed match.

2. **POPIA check on every juristic name.** A juristic name can contain a person's name (for example a firm named after its founder). At publish time, every juristic name in the public output gets a POPIA check before it is released.

---
*POPIA check: PASS. See §13.*
