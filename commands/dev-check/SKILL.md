---
name: dev-check
description: >
  Phase 2 (Development), step 6 of product-playbook — the checkpoint tester / development-complete gate.
  Verify that every core-scope feature is actually built, runs, and met its exit criteria + security
  definition-of-done, before moving to Testing. Use when you think development is done, or run
  /dev-check "is development complete", "checkpoint", "ready to test". Writes the Dev-complete section
  of PRODUCT.md. Run /test next.
---

# `/dev-check` — Phase 2 · Development ⑥ · run as an **engineer/tester**

**Mode:** the user's words `full` · `thorough` · `high` → add `--mode full` to the start command; `lean` · `quick` · `fast` → `--mode lean`; none → the tool decides. Follow the path the start prints.

## Lean path — the start prints `Mode: lean`: this section is the whole run
1. **One call:** `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase dev-check` — each milestone ticket's state, unmerged ticket branches, the gate and live-path commands, `#Plan`'s milestone lines, `#Scope`'s not-to-build list. Open no rule file.
2. **In ONE message, start all three:** the gate command · ONE helper running a security review of the merged code since `main` (and: what REAL thing could it touch by mistake? It loads no other skill and returns only a findings table) · the live path (start, hit the built tickets' routes, stop). Never repeat the helper's reading. A helper that returns nothing found nothing: run it once more; nothing again → security `UNVERIFIED`.
3. Per core-scope feature: built · runs · its ticket's DoD incl. security. Scope: search the code for the not-to-build list.
4. **`#Dev-complete` in ONE call:** its body in a scratch file outside the repo — a line each for the gate, the live path, security and scope with its result — every check runs; a red one decides the verdict, never how much is checked — then the feature table. Then `status.py set dev-check filled --verdict pass|fail --section-from <file>` (one refusal names every gap, a PASS with anything missing included; `--dry-run` lists them).
5. **File findings:** MEDIUM+ one issue each, LOW one grouped issue — a GitHub remote: `gh issue create`; none: `/tickets` files; a security finding never into a public repo.
6. The rest of the close: what `set` printed. **Everything below is the full path (`Mode: full`).**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **The start prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`**, `set` the close's — apply them (a situational companion only when a rule points into it). Load-bearing: **exit-criteria are testable AND verified (not assumed)**,
> **security-in-DoD checked**, **honest gap surfacing**, **scope re-check**, **measure not assume**.

## Contract
- **Purpose:** prove development is actually complete before Testing — a real gate, not a vibe.
- **Reads:** what the start prints (Step 0); more by `status.py section`.
- **Writes:** `PRODUCT.md#Dev-complete` — the checklist, each item checked **with re-runnable evidence** in the one settled form (`STATE-MODEL.md` §2f): `` `evidence: <command> → <result> · <artefact> · <YYYY-MM-DD>` ``. Transcribe what you actually ran; a criterion you judged rather than measured carries **no** evidence line and is reported `UNVERIFIED` by `/drift-check`, which is an honest state — inventing a command you did not run is not.
- **Gate type:** `verification` — pass/fail on repo evidence; no preference involved. Batchable, and **stops on red** - the chain waits; this run still does every check once. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Dev-complete` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:**
  - [ ] Every **core-scope** feature has a `STATUS.md` ticket row, **runs**, and met its DoD (incl. security) — verified. → `Every core-scope feature built & runs`
  - [ ] No hardcoding · prompts externalized · contracts typed · schema↔code consistent · builds/CI green. → `No hardcoding`
  - [ ] No oversized god-files (single-responsibility held); secret-scan + dependency-vuln scan clean. → `Exit criteria + security DoD verified`
  - [ ] **Scope re-check:** nothing built that's in OUT-OF-SCOPE (no creep). → `Scope re-check`
  - [ ] Every "done" has **HOW it was verified** recorded (evidence, not "done"). → `Exit criteria + security DoD verified`

## Step 0 — Context + prior-gate check
- **One first message: run `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase dev-check`** — the facts and this phase's rules in one call, and what this phase must NOT do; never the rule files or `PRODUCT.md` whole (`status.py section` for more). Show its first line.
- **The start prints each milestone ticket's state, the gate for THIS checkout, `#Plan`'s milestone lines and `#Scope`'s not-to-build list.** Unless every ticket is done and merged here and the gate passes on this code, `--verdict pass` is refused.
- **Tickets missing: never stop unchecked** — run every check on what is built; the FAIL names what is missing (no override).
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from dev-check --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing: without it a later reader cannot tell a gate that held from one waved through.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line.
- **The user declines to run it (`MECHANISMS.md` §Declined runs):** record it — `status.py set dev-check declined --reason "<their words>" --gate <the phase that fills it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** "should pass" is not "passes". **Surface gaps honestly** — a half-done feature listed as done is the "thought it was done" trap.

## Step 2 — Run the checkpoint
1. **Coverage:** every core-scope feature present + runs (spot-run the live paths with `/run`, and check the observable result — not just that the command exited 0). **Run the start's gate once, here:** each ticket passed on its own branch; merged, it is new code.
2. **Quality bar:** no hardcoded values; prompts in `prompts/` YAML; contracts typed; schema↔code consistent; CI green.
3. **Security DoD:** each feature's security checks are actually present (not just promised) — for AI, prompt-injection defence exists.
4. **Scope re-check:** compare built features to OUT-OF-SCOPE; flag any creep.
5. **Evidence:** confirm each ticket row records HOW it was verified (`--verified`).

## Step 3 — Write back to `PRODUCT.md`
Fill `#Dev-complete` in the one close call below: tick each box **only with evidence**; list any failing item explicitly.

## Step 3b — Principle-gate: phase-level verification (evidence)
Beyond ticking the per-feature boxes, do a phase-level check: a holistic **`/security-review`** (or equivalent)
across the auth/data surface, run **inside a subagent** so its report returns as input and cannot end the run,
and confirm CI (the auto-layer) is green. Then **report a phase Confidence
Score (0–100%)** with one line each on solid / risky-untested / to-raise-it (per `PRINCIPLES.md`).
**If any box can't be ticked with evidence, the gate FAILS — report exactly what's missing;
no hand-off to Testing.** A failing checkpoint is the point of this skill.

**File what the checkpoint finds, IN THIS RUN** — never handed to the user as a list to file or a decision
to make. **MEDIUM or above: one issue each** (`/tickets "<finding>"`); **LOW and unrated: ONE issue for the
run**, every finding on its own line with its file and what goes wrong. The checkpoint never edits code. Search the
open issues first so nothing is filed twice; **a finding a CLOSED issue claims to have fixed reopens that
issue** (with the evidence as a comment; on GitHub `gh issue reopen`; no GitHub remote — the start's remote line: the
local ticket file, as `/tickets` does). Name every issue filed or reopened in the close.
**A security finding on a PUBLIC repo is never filed publicly** — never into an issue or a committed file,
`docs/dev-check.md` and `PRODUCT.md` included: put it to the user in the close.

**Close the loop (`MECHANISMS.md` §Step 3b):** record it in ONE call — `status.py set dev-check filled --verdict pass|fail --section-from <file>` (`MECHANISMS.md` §Status) — then the rest of the close it prints, in order: reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), Step 3c, **no save question** — the record call saved (`MECHANISMS.md` §Commit the work; never ask *"Save this version of your project? (yes / no)"*; `--no-commit` only if the user said not to save; push only if the user says so), then **the transition guard** (`MECHANISMS.md` §Step 3b, item 4): a verdict for every exit criterion, citing the runs this phase made — never re-run one for its number; `UNVERIFIED` is a normal outcome, silence is not. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (its last line the `Open a NEW conversation` line `set` printed). **The close is the run's last message** — a composed skill's report is input to it, never the close itself.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c: `#Scope`'s core list against the `STATUS.md` ticket rows — a feature marked done that scope never asked for, or a scoped feature quietly dropped. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or a dated `superseded by` line in the earlier section).

## Step 4 — Handoff
"Development checkpoint passed (evidence recorded).
- **Does anything ahead need the product to be REACHABLE?** A milestone criterion naming a second device,
  a real user, or a link someone else opens needs a public URL — run **`/deploy`** first. It executes the
  runtime target `#Architecture` already recorded; it does not re-decide the host.
- Otherwise run **`/test`** — unit, integration, regression, and adversarial/security cases on the LIVE path."
