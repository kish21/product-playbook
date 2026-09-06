## 🎯 Pull Request Overview

### Related Issue(s):
- Closes #[Issue Number]

### 📝 Summary of Changes:
- 

### 📁 Modified Modules & Files:
<!-- Should match the ticket's Target Files. Anything outside that list is either creep or a ticket that needs widening — say which. -->
- `src/...`
- `tests/...`

### 🔒 Verification & Definition of Done:
<!-- Run the project's own gate — the `check` target in the Makefile / package scripts (see STRUCTURE.md) — and paste the command you ran. -->
- [ ] Tests pass — command: `        `
- [ ] Build / type-check passes — command: `        `
- [ ] Secret-scan clean (the pre-commit hook from `/foundation`)
- [ ] No hardcoded values — new endpoints, keys, model names, thresholds live in config / `.env`
- [ ] Feature doc `docs/features/<feature>.md` matches the code
- [ ] UI changes verified against `DESIGN.md` (`/frontend-audit` 0 errors) — or N/A

<!-- Lane mode (Lanekeeper present): this file is NOT used — Lanekeeper owns the PR template and the lane gate. See PRINCIPLES.md §Lane mode. -->
