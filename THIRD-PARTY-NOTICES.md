# Third-party notices

Product Playbook is MIT-licensed (see [LICENSE](LICENSE)). It follows open formats and conventions that others
publish, and it can call tools that others make. None of their code is copied into this repository; each is named
here with its licence and what the playbook uses it for.

| Work | By | Licence | How the playbook uses it |
|---|---|---|---|
| [DESIGN.md format](https://github.com/google-labs-code/design.md) | Google Labs | Apache-2.0 | `/design-system` writes DESIGN.md's front matter (`name`, `colors`, `typography`, `rounded`, `spacing`) in this format, so tools that read it get the same tokens. |
| [`@google/design.md` linter](https://www.npmjs.com/package/@google/design.md) | Google Labs | Apache-2.0 | Recommended check for a DESIGN.md (`npx @google/design.md lint DESIGN.md`); not bundled, not installed by the playbook. |
| [shadcn/ui](https://github.com/shadcn-ui/ui) CSS variable names | shadcn | MIT | The colour token names in DESIGN.md (`--background`, `--primary`, `--muted-foreground`, ...), so a project can use shadcn/ui components unchanged. |

Trademarks belong to their owners; naming a work here does not mean its maker endorses this project.
