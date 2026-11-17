# CHG-TW-002 — Supplier legal-form confirmation and two-person check queue (no silent hide)

| Field | Value |
|---|---|
| Change | CHG-TW-002 |
| Environment | **DEV only** (local box, private repo). No TEST, PROD, Pages or publish under this record. |
| Branch | `dev/CHG-TW-002-supplier-type`, cut from `origin/main` at `f63f5d2ef02621f9a991c4c353788f7377ab2aa7` |
| Pre-change commit (rollback) | `f63f5d2ef02621f9a991c4c353788f7377ab2aa7` (`main` after PR #2). Earlier snapshot tag `snapshot-2026-11-17-pre-tw-pr2` → `fb5a4bcc3ca25724a8c5ebdf0cf1fe0caf6ad17c` |
| Author | the author (TenderWatch) |
| Reviewers | reviewer A (project lead), reviewer B |
| Status | Draft for CAB. DEV build submitted for review and CAB on draft [PR #3](https://github.com/GrokForum/tenderwatch-sa/pull/3). |

## 1. Owner decision (relayed by the project lead, 17 Nov 2026)

Hiding 289 of the 291 Cape Town award suppliers (CHG-TW-001 DEV run) is a no-go; the owner wants 100% data quality. GO on two confirmation methods:

1. **Legal-form suffix.** Confirm a supplier as a legal entity when its name carries a legal-form suffix. Use the City of Cape Town register name first, the OCDS name if needed. Normalise case, punctuation and spacing. Cover (Pty) Ltd, Pty Ltd, Proprietary Limited, Ltd, Limited, CC, Close Corporation, Inc, NPC, SOC Ltd, RF, Trust, JV, Joint Venture.
2. **Two-person check queue.** Everything left goes to a queue with the reason, never a silent hide.

Remaining names are checked for POPIA first: likely sole traders or personal names stay unpublished until checked. No supplier may end up unclassified.

This reverses one CHG-TW-001 rule (§4.4): **Trust is now a legal form.** A trust is registered with the Master of the High Court, not CIPC, so its CIPC age indicator stays Unknown unless a sourced year exists.

## 2. Source-field check (done before building)

Checked against the actual DEV data of CHG-TW-001 (pinned OCDS file SHA-256 `a2849a63…5225`; City 2026 monthly registers, 508 rows).

| Source | Field carrying the supplier name | Rows | Trailing legal suffix |
|---|---|---|---|
| eTenders OCDS (OCP mirror), Cape Town awards | `awards[].suppliers[].name`; `parties[].name` and `parties[].identifier.legalName` are the same string on all 291 | 291 | **2** (0.7%) |
| City of Cape Town monthly award register PDF | `Vendor` column → `supplier_name` | 507 named | **400** (79%; legal name before any `t/a`) |

Plain result: **the OCDS name almost never carries a suffix**, and OCDS has no other legal-form field (`legalName` repeats the name). **The City register usually does**, but it covers Feb–Oct 2026 while the OCDS Cape Town awards are from award years 2021–2025. A City name can only be used where the two-detail rule links it to the award with the normalised name agreeing. **Method 1 therefore cannot reach high coverage on this data, and the queue is large.** Full counts: `docs/dev/CHG-TW-002-classification-report.md` §1.

## 3. Scope

Changes:

* `tw/supplier_type.py`: token-based trailing-suffix matcher with sub-types; `classify_supplier()` giving exactly one status per supplier; `classify_awards()`; `assert_no_silent_hide()`; POPIA-hold heuristic; public-name rule now also requires `confirmed_juristic` and no hold.
* `tw/pilot.py`: `apply_classification()` wired after matching; age fields recomputed (trust → no CIPC year used).
* `tw/export.py`: classification fields in the public export; row count must equal input; guard against any queued or held name.
* `tw/classification_report.py`, `scripts/run_chg_tw_002_classify.py`: DEV classification run over the CHG-TW-001 warehouse (no network) and the DEV report.
* Tests: `tests/test_classification_chg_tw_002.py` (new); `tests/test_supplier_type.py` updated for the Trust reversal.
* Records: this RFC, `docs/dev/CHG-TW-002-classification-report.md`, `STATUS.md`.

Stays: OCDS and City ingest, the two-detail match rule, age bands and indicator window, PublicFunds (read-only pin `de37f666…`), the public site repo (untouched), CHG-TW-001 records (historical; §4.4 there is superseded by this RFC, not edited).

## 4. Design

### 4.1 Normalisation and suffix matching

Name → NFKD ASCII, case-folded, `&` → `and`, every non-alphanumeric run (brackets, dots, commas, hyphens) → one space, then split into tokens. A suffix matches only as whole **trailing tokens** of the **legal-name part** (the part before `t/a` / `trading as`). Never a substring inside a word: `Mccarthy`, `J Mcc`, `Fooltd`, `Trustee`, `Trustworthy`, `Jinc`, `Incline`, `Soccer` do not match. A name made of legal words only (`Pty. Ltd.`) does not match. `C.C.` is read as CC only with its dots.

| Trailing tokens (longest first) | Sub-type |
|---|---|
| proprietary limited; pty ltd; pty limited; ltd; limited; inc; incorporated | `company` (Inc is a personal liability company) |
| soc ltd; soc limited; soc; state owned company | `soc` |
| npc; non profit company | `npc` |
| cc; close corporation; `C.C.` | `close_corporation` |
| trust | `trust` (registry: Master of the High Court) |
| jv; joint venture | `jv` |
| rf on its own | `other_juristic` |

`RF` next to another form (`(RF) (Pty) Ltd`, `(Pty) Ltd (RF)`) is a qualifier; the other form decides the sub-type.

### 4.2 One status per supplier

Order of decision:

1. Candidate names: City names linked by the two-detail rule **with the name agreeing**, then the OCDS name.
2. If any candidate looks personal and none carries a suffix → `check_queue`, `looks_like_personal_name`, `popia_hold`.
3. City names with a suffix: if they disagree on sub-type → `ambiguous_suffix`; if the OCDS name has a different sub-type → `name_mismatch_between_sources`; else `confirmed_juristic`, method `city_register_suffix` (or `…_before_trading_as`).
4. Else the OCDS name with a suffix → `confirmed_juristic`, method `ocds_suffix`.
5. Else queue: `name_mismatch_between_sources` (City rows on the same tender name someone else), `ambiguous_suffix` (a legal word not at the end), `no_suffix`, or `empty_name`.

Fields: `classification_status`, `classification_method`, `legal_sub_type`, `legal_suffix`, `legal_name_source`, `legal_name`, `queue_reason`, `queue_notes`, `popia_hold`, `registry`, `legal_form_link`, `legal_form_fact_label`; `supplier_type` is kept for the age code (`juristic` when confirmed).

### 4.3 Link strength and fact label (CHG-TW-001 §19)

§19 says a name-plus-buyer link is not a tight match. So a legal form taken from a City row linked on name + buyer only is labelled **Reported**; from the OCDS record itself, or a City row that shares the tender reference, **Confirmed**. Status stays `confirmed_juristic` (owner's method 1); the label tells the reader how strong the link is.

### 4.4 POPIA hold

`popia_hold = true` when any source name looks like a sole trader or person: `t/a` without a suffix on the legal name, initials plus surname, a title (Mr, Dr…), a trust with a family or person-style stem, or a bare two-to-four-word name with no business word, digit or legal word. Deliberately over-inclusive: held names are released only by the two-person check. Held names are never written to a public file and are shown in the DEV report only as `[POPIA hold: name withheld until checked]` with an internal row id.

### 4.5 Public export

Every input row is exported (count asserted equal). The name is shown only for `confirmed_juristic` without a hold; queued rows carry their status and reason with the name withheld until checked. This is visible, not a silent hide.

### 4.6 Age indicator

Unchanged rule: needs a sourced CIPC year. Confirming a legal form gives no year, so all rows stay Unknown in this run. Trusts never use a CIPC-derived year.

## 5. DEV result (17 Nov 2026, Africa/Johannesburg)

See `docs/dev/CHG-TW-002-classification-report.md`. Over the 291 rows: **66 `confirmed_juristic`** (64 `city_register_suffix`, 2 `ocds_suffix`; 56 company, 8 close corporation, 1 JV, 1 other juristic; link: 59 name + buyer only → Reported, 5 tender reference + 2 same record → Confirmed) and **225 `check_queue`** (194 `no_suffix`, 24 `looks_like_personal_name`, 7 `name_mismatch_between_sources`). `popia_hold` on 29 rows (24 queued, 5 confirmed). Classified 291 of 291; none hidden. Age indicator: Unknown on all 291 (no sourced CIPC year).

## 6. Risks

* **Coverage.** Method 1 reaches 66 of 291 (23%) here. 100% *classification* is met (every row has a status), but 100% *confirmation* is not reachable from these two free sources; the queue (225 rows, 191 distinct names) needs two-person time.
* **Name-only links.** 59 of 66 confirmations come from a City name linked on name + buyer, years apart. A same-named different entity is possible; hence the Reported label (§4.3).
* **POPIA heuristic.** Over-holds business names (for example two-word brand names) and can miss a personal name followed by a business word (for example "<first name> <surname> Trading"). Mitigation: every queued name stays out of public output until the two-person check, whether held or not.
* **Inc firms named after people.** A confirmed `Inc` (personal liability company) may carry a founder's name. It is a registered entity name; the CHG-TW-001 §19 POPIA check at publish time still applies.
* **City PDF parsing.** Some City vendor strings are wrapped or multi-vendor fragments; they rarely link because the normalised name must agree exactly. Under-matching is acceptable; over-matching is not.
* **Rule reversal.** Trust is now juristic. Family-style trust names are held.

## 7. Test plan

Fresh venv, `pip install -e .[test]`, `pytest`:

* suffix variants (`Pty. Ltd.`, `(PTY)LTD`, `cc.`, `C.C.`, `(RF) (Pty) Ltd`, `SOC Limited`, `Incorporated`, `Non-Profit Company`, `Joint Venture`, Trust…) map to the right sub-type;
* false positives (`Mccarthy`, `J Mcc`, `Fooltd`, `Trustee`, `Trustworthy`, `Jinc`, `Incline`, `Soccer`, `Limited Edition…`, a suffix after `t/a`) do not match;
* no-silent-hide invariant: input count = classified count = public export count; every row has a valid status; queued rows have a reason; the invariant checker rejects a missing status or reason;
* POPIA: personal-looking names are held and never reach the public export; business names are not held;
* trust: registry Master of the High Court, indicator Unknown even if a year is present; a company with a sourced CIPC year keeps its indicator;
* Reported vs Confirmed by link strength;
* all CHG-TW-001 tests still pass (drift).

Result: see §10.

## 8. Rollback

Git only. Before merge: delete the local branch; `main` is untouched. After a merge: `git revert -m 1 <merge-commit>` on a review branch, or reset a branch to `f63f5d2ef02621f9a991c4c353788f7377ab2aa7` (pre-change `main`). The earlier snapshot tag `snapshot-2026-11-17-pre-tw-pr2` (`fb5a4bcc`) stays. No live data, no PublicFunds and no public site are touched, so nothing outside git needs reverting; local DEV outputs are git-ignored and are rebuilt by `scripts/run_chg_tw_002_classify.py`.

## 9. Seen, not touched

* CHG-TW-001 `pilot.run()` still writes `docs/dev/CHG-TW-001-run-report.md` by default; it was not re-run here, so that report stays a record of the CHG-TW-001 run.
* CHG-TW-001 §4.4 still describes the old Trust rule; superseded by this RFC, left as the historical record.
* City register parser keeps some wrapped / multi-vendor fragments as vendor strings (see §6).

## 10. CAB review

Reviewers: **reviewer A** (project lead) and **reviewer B**, as four checks (expert, shadow, charter, drift). Two reviewer PASSes are required on the exact head; each review round and its outcome is recorded in the pull request. A reviewer PASS is not a GO to merge, publish, or open TEST/PROD; only the owner gives that, on the exact head.

Questions for CAB and the owner:

1. Accept **Reported** (not Confirmed) for legal forms from name + buyer-only City links (59 rows)?
2. Accept `…_before_trading_as` as method 1 (a suffix on the legal name before `t/a`)? None occurred in this run.
3. Accept that every queued name, held or not, is withheld from public output until the two-person check?

**Result:** pending.

---
*POPIA check: PASS. No ID numbers, contact details or addresses. Names in this RFC are synthetic. Held names appear in no committed file.*
