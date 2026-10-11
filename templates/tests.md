<!-- The layout of docs/tests.md, written by /test. `set test filled` numbers any heading without one and warns
on long sentences, dash chains, source labels inside sentences and playbook words. Write for a person who did not see
the run: one idea per sentence, about 15-18 words, none over 30. A source or a note goes in a footnote `[1]` with its
text in the appendix. No playbook words: write "the record", "the checks", never "spine", "PRODUCT.md" or a command
name. -->
# {{product}} — tests
_{{date}} · what the tests prove, and what they do not_

## 1. What the tests prove
Three to five short sentences: what works, what is still broken, and how sure we are.

## 2. How to run them
| What | Command | A pass looks like |
|---|---|---|
| All checks | `<the project's check command>` | `<n passed, 0 failed>` |
| The live path | `<the test file>` | `<what the user sees>` |

## 3. What is covered
| Part of the product | Unit | Integration | Live path | Security |
|---|---|---|---|---|
| `<feature or module>` | `<yes / no>` | `<yes / no>` | `<yes / no>` | `<the attacks tried>` |

## 4. Bugs the tests found
One row per bug. The test stays, marked as an expected failure, until the fix lands.

| Test | What goes wrong for a user | Issue |
|---|---|---|

## 5. The defect hunt
| Probe | Where | What it found |
|---|---|---|

## 6. Not tested yet, and why
One line each. "Nothing" is an answer.

## Appendix A — Workings
### A.1 The test database is isolated
How the suite proves it never touches the development data.

### A.2 Notes and sources
[1] `<where a fact came from>`
