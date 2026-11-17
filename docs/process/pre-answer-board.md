# RFC pre-answer board

Status: draft under CHG-TW-005 (records only). It is not in use until the owner gives a GO on a merged head.

## Purpose

Before an RFC's owner questions reach the owner, a short board pass runs each question past five fixed viewpoints. The owner gets a recommendation he can accept, change or overrule in one line. The board drafts answers. It never answers for the owner.

## Viewpoints (role words only)

| Viewpoint | Checks |
|---|---|
| Lawyer | The Companies Act, POPIA and site terms. It cites only sources that were actually opened; otherwise the point is Unknown. |
| Privacy reviewer | Whether a natural person can be identified, alone or in combination. Masks, citations, and anything shown next to a name. |
| Neutral editor | The wording describes patterns and counts, never findings about anyone. Labels are used exactly (Confirmed; Reported, Unconfirmed; Unknown). |
| Data skeptic | Does every count reproduce from a committed script or a stated query? If not, the count is marked as not reproduced. |
| Budget keeper | The smallest change that answers the question; the owner's time, usage and build time. It cuts questions that are not owner decisions. |

## Rules

1. Every draft is labelled **"Board draft, not an owner answer"**.
2. The owner's GO stays required. A board draft is never recorded as a decision, and it never unlocks a merge, build, publish or send.
3. At least one viewpoint argues against the recommended answer. The dissent is kept in the record, even after the owner answers.
4. Each draft gives a **recommendation**, a **confidence** (low, medium or high) and **what would change it**.
5. Role words only. No bot or person names.
6. Every draft keeps an "Other" line open: the owner may go beyond the options offered.

## Budget and ratchet

- **Fixed budget:** one pass per question set, and at most about 120 words per question block. When a question needs more, that means it should be split, or it is not ready for the owner.
- **Planner first:** before drafting, the budget keeper asks one question per item: "Is this an owner decision, and what is the smallest decision that settles it?" Items that fail go back to the author.
- **Git ratchet with real metrics:** after the owner answers, each draft is scored as matched, partly matched or missed, in a committed scorecard row (RFC, question, score, blind yes or no). A change to this board process is kept only if the match rate on the next **blind** set does not fall; otherwise it is reverted with git.

## Format (one short block per question)

```
Q<id> — <question in one line>
Board draft, not an owner answer.
Recommendation: <one line>   Confidence: <low|medium|high>
Would change it: <one line>
Lawyer: <one line> | Privacy: <one line> | Editor: <one line> | Data: <one line> | Budget: <one line>
Dissent (<viewpoint>): <one line, kept>
Other: the owner may answer outside these options.
```
