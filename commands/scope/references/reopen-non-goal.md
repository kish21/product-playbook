# /scope — reopening a Non-goal later

> Opened only when the owner wants to reverse a Non-goal. Part of `commands/scope/SKILL.md`.

## Reopening a Non-goal later (the reversal protocol)
A Non-goal is "never *for this product's vision*", not "never discussable." The owner may reverse
one when the world changes (a competitor makes it table stakes, the buyer demands it). When that
happens, the move is an **explicit recorded reversal, never silent drift**:
1. **Record the decision** — date, who decided, and the *reason the world changed* — in the spine
   (`PRODUCT.md`: strike the Non-goal line with a pointer, add it to Deferred or scope) and in the
   feature's design doc header.
2. **Re-sort, don't just delete** — a reversed Non-goal usually lands in **Deferred with a trigger**
   (e.g. "design doc + benchmark done"), not straight into scope.
3. **Check the blast radius** — a reversal is often a *new capability track*, not a sub-item of the
   feature that prompted it. Name it separately so its true size is visible.
If the assistant notices work quietly contradicting a Non-goal without this protocol, that is
drift — surface it (`/drift-check` treats an unrecorded reversal as a finding, not a decision).
