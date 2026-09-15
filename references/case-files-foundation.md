# Case files — `/foundation`

War stories behind the rules in `commands/foundation/SKILL.md`. Each heading is pointed to from its rule.

## The runbook in the spine

**A logged test run, after 11 of 16 phases (#167).** `PRODUCT.md` had reached 73 KB and 435 lines, with five
sections still essentially empty. The playbook held its own files to 15 KB and set no size rule for the
spine. `#Foundation` alone was **14.0 KB**, nearly the whole ceiling the playbook sets for one skill file.
It held the boot sequence, every `.env` variable, what each guard refuses and how to prove it: a runbook
sitting in a spine section. #185 split it. The operational detail went to `docs/runbook.md`, written for
someone who was not there, and `#Foundation` became a record with a pointer (`PRINCIPLES.md`: a section
is a record, not a container).

## The skeleton nobody saw boot

**A logged test run, `/foundation` (2026-09-13), read from the session log: 229 tool calls, 07:49 → 08:45 UTC.**
Step 2 item 1 already ends with *a runnable entrypoint with a health path*, so the app could run after
item 1 of 8. Nothing told the run to show it.

- **The first boot came at call 133 of 229, 22 minutes in** (08:12). A local `node backend/dist/index.js`
  answered `{"status":"ok"}`, but by then most of the skeleton had been built on top of it. It was also the
  first thing in the phase the owner could have seen.
- **An earlier boot did not vouch for a later one.** At 08:17 (call 148) the container boot failed:
  `EACCES: permission denied, mkdir '/app/C:/Program Files/Git/data'`. Git Bash had rewritten the `/data`
  volume path into a Windows one. That failure had nothing to do with the code, and the 08:12 boot could
  not have caught it. The run then edited `backend/src/index.ts`, because the boot's error log had come back
  with an empty stack, and rebuilt the image before the container answered `healthy after`.
- **A late boot did count.** At 08:39 (call 221) remote CI booted the container on the final tree:
  `healthy after 2s`. After that, only `PRODUCT.md` and notes outside the repo changed.

**The rules this earned.** First, Step 2 item 1 ends by proving the boot: hit the health path, print one plain line
saying the app runs and how to see it, and stop whatever was started. A broken boot then surfaces before
seven items sit on top of it. The line is printed, not asked, so a batched run does not stop. Second, the
`runs end-to-end` line in Step 3b may cite an earlier boot only under `/build`'s condition, word for word
(case file `case-files-build.md`: *The audit the review fix outran*). Step 2's items 3–8 add the startup guard,
logging, adapters, the token import and the container, all of which change the boot path. So the item-1
boot never qualifies, and a CI health check on the final tree can. The permission covers that one line. The guard
proofs are new work at Step 3b, not repeats, so they always run.

*Deliberately not added:* a git recipe for "what changed since the evidence", for the reason
*The audit the review fix outran* records. #251's items 2 (one copy of the eight steps) and 4 (a tiered
CVE gate) were declined by the owner and are not part of this change.
