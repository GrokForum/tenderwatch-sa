# IDEA: TenderWatch bot (parked, not an RFC yet)
Filed: 2026-11-16 18:50 SAST, owner's request. Status: PARKED. No build, no GO.

## Concept
SA government publishes/mails available tenders (e.g. 10k plastic cups for Dept of Correctional Services).
Red flag pattern: winning company registered with CIPC within ~1 month before the award.
A bot could match tender awards to company registration dates and flag very young winners.

## Why parked
- CIPC company lookups need a CIPC login; manual lookups are zero-sum effort right now.
- No GO for any login (standing law: no login without a named GO).

## Revisit if
- A free/bulk source of company registration dates appears (open data, API, third-party dataset).
- Tender award data turns out to include registration numbers (registration year is encoded in the CIPC number, e.g. 2026/xxxxxx/07 — year only, not month).
- Overlap with PublicFunds (supplier flags, four-eyes review) makes it a PublicFunds extension instead of a new bot.

## Guardrails when revived
- POPIA: companies and public procurement are fair game; directors who are private citizens need care — no doxxing.
- Flags are indicators, not accusations; right-of-reply pattern like PoliticianWatch.
