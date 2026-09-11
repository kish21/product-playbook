# The isolated test datastore — a recipe per custody

> Opened by /foundation at Step 2, when wiring the test datastore and its guard. Which recipe applies is
> decided by the **data custody `#Architecture` already recorded** — this file never picks a vendor for
> the project, and the vendors named are dated examples, not a supported list. The playbook does not
> pre-decide a trade-off the project's own constraints should decide (`PRINCIPLES.md`).

## §Why this needed writing down

The requirement is one of the most operationally demanding in the playbook — *provisioned, disposable,
created and torn down by the task runner, fail-closed, with throwaway CI credentials* — and it was stated
with **no path at all**. Near-trivial on a container; genuinely different work on a managed service.
So the obvious fallback is to point `TEST_DATABASE_URL` at the development database — **the one thing it
forbids, and the one whose failure is silent until the data is gone.**

## §The recipes

**How you obtain it depends on the custody `#Architecture` already recorded**, and the mechanics are
not comparable — this requirement is near-trivial on a container and real work on a managed service,
which is why the obvious shortcut is the one thing it forbids:
- **Local / self-hosted** → a throwaway instance created for the run and dropped after it.
- **Managed-serverless** → a **database branch per run** where the platform offers one (created and
  deleted by the task runner with a provisioning token), otherwise a **second project/instance** kept
  solely for tests. Budget for quotas and for CI needing credentials that can create and destroy a
  remote resource — that is the real cost, and it is why this gets designed here rather than
  discovered in CI.
- **Embedded** → a temp file (or in-memory instance) per run, deleted after.
These are **recipes per custody, with vendors as dated examples — never a supported-vendor list**;
the playbook does not pre-decide a trade-off the project's own constraints should decide
(`PRINCIPLES.md`). **If none of them is achievable today, say so and record it** — an honestly
recorded gap beats pointing `TEST_DATABASE_URL` at dev, whose failure is silent until the data is gone.
