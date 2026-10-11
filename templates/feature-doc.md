# <What the feature does, in plain words>

<!-- HOW TO FILL THIS (delete every comment when you write the file)
/build writes one file per ticket at docs/features/<feature>.md, in ONE write, at the close. Two halves:
1. The TOP half is for the owner and anyone who never reads code. Plain words, full sentences, one idea per
   sentence. No code names (no function, class, table, field or setting names), no file names, no rule codes
   (R3, D2, DP1, #Contracts, §Gates), no backticks - except the ONE command under "What you can do now".
   The point that matters most goes first, never under a later heading.
2. After the --- line, the BOTTOM half is for developers and coding agents: everything a reviewer or the next
   build needs, with code names and paths, and every trace line the playbook's checks read (Archetype:,
   Live-path checks walked:, Real-world reach:, the Review section naming every changed code file).
`gate.py --ticket <id> --close` refuses a top half that breaks rule 1. A worked example sits beside this file:
feature-doc-example.md. -->

## 1. In short

<1-2 sentences: why this exists and who it is for.>

## 2. What you can do now

<The one command, or the screen and where to find it, and what you see when you use it.>

## 3. What it protects you from

<What would go wrong without it, said as what a user or the owner would lose. The review finding that mattered
most goes here, in one plain sentence, with the fact that it is fixed and tested.>

## 4. Not done yet

<Known gaps and what a later ticket adds, in plain words. "Nothing known." when nothing is.>

---

## 5. For developers and coding agents

Ticket: <ID> · Archetype: <kind> → §<cluster> opened (or Archetype: none)

### 5.1 Contract

- Consumes: <the typed shapes from #Contracts this ticket reads>
- Exposes: <the typed shape dependants use>

### 5.2 Files

- `<path>` - <what it holds>
- `<path>` (not in the ticket) - <why it changed>

### 5.3 How it was verified

- `<command>` → <the result line, copied from the captured output>
- Live-path checks walked: <the names of the live-path checks whose trigger matched, or none matched>
- Real-world reach: <the real thing this code could touch by mistake> - guarded by test_<name> (or - not guarded: <why>)
- <principle> → <the evidence: command · result · commit>
- Step 3c: <no contradiction with #Contracts, #Architecture, #Scope, DESIGN.md - or the conflict and who won>

### 5.4 Review

<code review + security review R1 <n> findings · R2 (<n> files) <n> findings, or R2 skipped by the user: <reason>>

| Severity | File:line | What goes wrong | Fixed by |
|---|---|---|---|
| <MEDIUM> | `<path>:<line>` | <what a user would see go wrong> | <the fix and the test that proves it> |

- `<path>` - <what the review checked in this file>
