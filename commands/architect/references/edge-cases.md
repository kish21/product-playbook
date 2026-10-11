# /architect — the unusual cases

> Opened from Step 0 of `SKILL.md` only when the case is real; a normal first run never opens this file.

## Step 0 — the cases a first run does not meet

- **A `running` upstream gate BLOCKS from here on** (`STATE-MODEL.md` §2a): a pending result needs the result, or a recorded override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from architect --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- **A NARROW run — one decision, called from another phase** (`/deploy` finds a unit with no runtime
  target): decide that row only — its search, its provenance, one line in `#Architecture` (a changed recorded decision gets its ADR) — then hand back: no chain or commit offer, no close, no state recorded, no full-section exit criterion; the calling phase's close reports it. (case file: Two closes in one run)
- **Chain mode is never asked** (`MECHANISMS-ON-DEMAND.md` §Batch mode, *chain*): stopping after the architecture is the default. A user who asks to continue into `/structure` gets the chain — every question still asked, two records, two commits, one close. A red gate here never reaches `/structure`.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a decision that changes gets a `### change D<n>` field (was · now · why · affects): the save writes its ADR and marks the old decision superseded.
- **The gate is unmet and the run stops here (`MECHANISMS.md` §Declined runs):** `status.py set architect declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.
- **A refusal the user says does not apply** (a check that read the wrong line): the user's message already says why → record it, no question: `status.py waive --from architect --check "<words of that refusal>" --reason "<those words>"`. Else ONE question (your question tool, else numbered options): *"Fix it" (Recommended: the check guards the record)* · *"Other - type why this check does not apply"* — that text is the reason; record it the same way. The next `set` drops that refusal only. A secret, `.env`, install or security refusal is never waived.
