# CHG-TW-005 — RFC pre-answer board

| Field | Value |
|---|---|
| Change | CHG-TW-005 |
| Type | RFC and process document only. No code, no data change, no build under this record. |
| Environment | DEV (records only) |
| Branch | `dev/CHG-TW-005-pre-answer-board`, from `origin/main` at `905562ad649dc07427d77c515f687e84825d09a4` (PR #7 squash merge) |
| Rollback reference | `905562ad649dc07427d77c515f687e84825d09a4`; snapshot tag `snapshot-2026-11-17-pre-tw-pr7` → `a6443326` |
| Author | the author (TenderWatch) |
| Reviewers | reviewer A (project lead), reviewer B |
| Basis | Owner GO to draft an RFC pre-answer board, 17 Nov 2026 23:03 SAST, relayed by the project lead; the author and reviewer B have not heard it from the owner directly. |
| Status | Draft for CAB on its own pull request. Records only. |

## 1. Goal

To make owner questions cheaper to answer. Before an RFC's questions reach the owner, a short board pass runs them past five fixed viewpoints and attaches a draft answer to each, with a recommendation, a confidence level, what would change it, and a kept dissent. The owner still decides every question; the board saves him reading time and surfaces objections early.

## 2. What changes

* New: `docs/process/pre-answer-board.md` (viewpoints, rules, budget and ratchet, format).
* New: this RFC, with a trial on CHG-TW-004 §13.6 B–E (§4).
* `STATUS.md`: one row.

**What stays:** the it-project gates, CAB review by two reviewers, and the owner's GO on the exact head for any merge, build, publish or send. No RFC's existing questions or answers change.

## 3. Sources and adaptation

The design adapts ideas from the owner's own local "ai-board-of-advisors" skill. **The author did not read that skill directly.** Its features are known only as relayed by the project lead:

* a fixed budget, and a git ratchet with real metrics;
* roles plus plain prose;
* a Socratic planner that protects the budget;
* very short answers.

The adaptations are: fixed viewpoints in role words; a word budget per question; a planner step ("is this an owner decision, and what is the smallest decision that settles it?"); a committed scorecard with a git ratchet on blind match rate; and one-line answers.

## 4. Trial on CHG-TW-004 §13.6 B–E (not blind)

**This trial is not blind.** The owner's answers to B–E were already known when these drafts were written (17 Nov 2026, after 22:31 SAST). To limit that bias, each draft's recommendation is taken from the recommendation the RFC already carried **before** the answers, in revision 7 as first pushed (`d4e6a239`, §13.6), where there was one. Where there was none, the draft says so, and that part of the score is marked as contaminated. The blind test is proposed in §5.

**B — Show Reported, Unconfirmed registration years?**
Board draft, not an owner answer.
Recommendation: no. Show `unknown` until Confirmed; this matches Q2 (from `d4e6a239`). Confidence: high.
Would change it: the owner preferring visible tracking over a blank cell.
Lawyer: §4.6 CIPC-terms risk is smaller with fewer published lookup facts. | Privacy: no change. | Editor: an unconfirmed year next to a supplier reads as a fact. | Data: the 54 rows depend on lookups not yet returned. | Budget: no build cost.
Dissent (neutral editor, against): a labelled Reported, Unconfirmed year is more transparent than `unknown`.
Other: the owner may answer outside these options.

**C — Mask safeguard, register-level citation, and held rows?**
Board draft, not an owner answer.
Recommendation: a fixed-length mask, no other identifying detail, register-level citation, and the mask on the 5 held rows too. Confidence: medium. (`d4e6a239` listed the three safeguards as options without recommending them, and said nothing on held rows.)
Would change it: an owner view that the source documents are public, so masking adds little.
Lawyer: POPIA favours minimal identifiability. | Privacy: length leaks; a row-level citation unmasks. | Editor: the mask must not look like an allegation. | Data: 32 rows affected. | Budget: one display rule.
Dissent (budget keeper, against): keep the decided mask and ship sooner; a fixed-length mask adds a build rule.
Other: the owner may answer outside these options.

**D — Indicator thresholds I1, I2 and I4?**
Board draft, not an owner answer.
Recommendation: accept as proposed (I1: 3 or more in a financial year; I2: 30 days and the metro threshold; I4: 365 days) (from `d4e6a239` §13.4). Confidence: medium.
Would change it: a blind back-test showing too many or too few flags.
Lawyer: I2 rests on the 2023 SCM amendment, opened. | Privacy: none. | Editor: counts, not adjectives. | Data: I2 has 0 cases and I7 is not enabled, so the thresholds are untested. | Budget: no build until each source exists.
Dissent (data skeptic, against): defer the I2 and I4 thresholds until real data tests them.
Other: the owner may answer outside these options.

**E — The 27 personal-looking rows: withheld, or shown masked?**
Board draft, not an owner answer.
Recommendation: keep them withheld until the two-person check (from `d4e6a239`). Confidence: medium.
Would change it: the owner accepting the fixed-length mask as enough protection.
Lawyer: these may be sole proprietors, so POPIA applies in full. | Privacy: withholding is the lowest risk. | Editor: a masked row still shows that someone won. | Data: 27 rows, 14 names. | Budget: no extra rule.
Dissent (neutral editor, against): withholding hides public awards; show them masked so the register stays complete.
Other: the owner may answer outside these options.

### 4.1 Scorecard

| Question | Owner's recorded answer (CHG-TW-004 §13.6) | Score | Note |
|---|---|---|---|
| B | Only Confirmed years published, each with its label; Reported, Unconfirmed years internal until confirmed | **Matched (against the 22:30 answer); later extended at 22:41** | The owner briefly reconsidered before answering at 22:30. The score is against that answer, which was inside the options. At 22:41 he extended it beyond the options with the masked placeholder (§4.2). Had the extension been the answer, it would score Missed. |
| C | Fixed-length mask, no extra identifying detail, register-level citation; the mask also covers the 5 held rows | **Matched (contaminated)** | There was no prior recommendation, so the draft was written knowing the answer. Not evidence for the board. |
| D | I1–I7 thresholds accepted as proposed | **Matched** | The dissent (defer) was not taken up. |
| E | The 27 personal-looking rows show masked | **Missed** | The kept dissent matched the owner's answer. This is why dissent is kept. |

Result: 2 clean matches (one later extended), 1 contaminated match, 1 miss, on a non-blind set.

**Per-RFC ratchet row** (proposed format; see the process doc):

| RFC | Question set | Blind | Scored | Matched (clean) | Owner questions sent | Cut by the budget keeper |
|---|---|---|---|---|---|---|
| CHG-TW-004 | §13.6 (revision 7) | No | 4 (B–E) | 2 | 5 (A–E) | 0 (no board existed) |

These are the baseline only; a non-blind row does not count toward the ratchet. This shows the format works on real questions. It does not show the board predicts the owner.

### 4.2 Example: the owner going beyond the options

For B, the options were "show Reported, Unconfirmed years" or "show `unknown`". Later the owner asked for a third form, a fully masked placeholder, `Year: ****, Reported, Unconfirmed`, so it "can be seen as being tracked while full privacy upheld" (17 Nov 2026 22:41 SAST, author's chat; recorded in CHG-TW-004 revision 8). The board format therefore keeps an "Other" line on every draft, and the scorecard records an owner answer outside the options as **Missed**, with a note. A draft is scored against the answer the owner actually gave to that question; a later extension beyond the options is noted next to the score, as for B.

## 5. Proposal: a blind trial

On the next RFC that carries owner questions, write the board drafts and commit them **before** the questions go to the owner (the commit time is the proof). Score each against the owner's answer and add the rows to the scorecard. Under the ratchet, a later change to this process is kept only if the blind match rate does not fall and the owner questions sent do not rise by more than one (see the keep rule in the process doc).

## 6. Success, rollback, seen not touched

* **Success:** two reviewer PASSes on the exact head, then the owner's GO to merge. The process is used only after merge.
* **Rollback:** before merge, delete the branch. After a merge, `git revert` the merge commit, or reset a branch to `905562ad649dc07427d77c515f687e84825d09a4`.
* **Seen, not touched:** none.

## 7. CAB review

Reviewers: reviewer A (project lead) and reviewer B, four checks (expert, shadow, charter, drift). A PASS is not a GO; only the owner gives that, on the exact head.

**Result:** pending.

---
*POPIA check: PASS. No supplier or personal names; counts only; role words only.*
