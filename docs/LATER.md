# TenderWatch SA: later list

Parked ideas that are not worth tackling yet. Nothing here is scoped, approved or scheduled.
An item moves out of this list only through a normal RFC and review.

Started 2026-11-19.

## Site and register

- A combined site that aggregates all four watch registers (Build project, private repo; owned by the owner, not TenderWatch).
- Per-department and per-municipality views (award counts, share going to companies under 2 years old).
- Supplier age-band chart over time (by award month).
- Data dictionary for the published (masked) register CSV (`/register.csv` already ships).
- RSS or Atom feed of new awards added each night.
- Search by tender reference and by CSD number.

## Sources

- More departmental and municipal award lists beyond the City of Cape Town (only where terms allow).
- Government Gazette award notices as a second confirming source.
- Published AGSA findings linked to the department, never to a private person.

## National expansion follow-ups (from CHG-TW-011)

- Widen past stage 1 (eThekwini, Mangaung) only once the "all buyers" DEV build scans clean: buyer names taken from short or placeholder source strings, phone-shaped values in titles, and loaded words in titles still fail closed.
- A company-age source for national rows: OCP Pub 143 has no CIPC numbers, so every national row is Year: Unknown today. Only a free, public source; no CIPC login.
- Municipal award lists (PDF, HTML, xlsx) per metro: read each site's terms and robots first. Several metro hosts currently fail TLS certificate checks; those stay logged as fetch errors, never fetched with verification off.
- Re-pin OCP Pub 143 when the publisher refreshes it, with the new size, SHA-256 and Last-Modified in the run record.
- Per-buyer review load: all 138 stage-1 national rows sit in the check queue (no legal suffix or personal-name shape), so reviewer time scales with buyers added.

## Process and quality

- Make GENERIC_WORDS a tracked config (BAU queue item).
- A fixed set of approved basis phrases for POPIA holds instead of free text.
- A public changelog page generated from merged RFCs.
- A "how to correct a record" page linking the right-of-reply process (the owner still sends every reply).

## Not doing (for the record)

- No CIPC login, paywalled or login-gated sources without the owner's named GO.
- No director-level personal data, ever.
