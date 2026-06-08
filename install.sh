#!/usr/bin/env bash
# product-playbook installer
# Copies the product-playbook skills into ~/.claude/commands/ so they become
# globally available slash commands, plus the companion files the skills read
# (PRINCIPLES.md, VISION.md, templates/PRODUCT.md).
#
# Usage (one-liner, recommended):
#   curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh | bash
#
# Usage (local clone, GLOBAL — available in all your projects):
#   ./install.sh
#
# Usage (PROJECT-LEVEL — commit it into one project so teammates get it on clone):
#   ./install.sh --project /path/to/project
#   (copies skills → <project>/.claude/commands/ and companions → <project>/.claude/product-playbook/)

set -euo pipefail

REPO_URL="https://github.com/kish21/product-playbook.git"

# --- parse mode: global (default) vs --project <path> ---
SCOPE="global"
PROJECT_DIR=""
if [[ "${1:-}" == "--project" ]]; then
  SCOPE="project"
  PROJECT_DIR="${2:-}"
  if [[ -z "${PROJECT_DIR}" || ! -d "${PROJECT_DIR}" ]]; then
    echo "⚠  --project needs an existing directory: ./install.sh --project /path/to/project"
    exit 1
  fi
fi

if [[ "${SCOPE}" == "project" ]]; then
  BASE="${PROJECT_DIR}/.claude"
else
  BASE="${HOME}/.claude"
fi
TARGET="${BASE}/commands"
# Companions live OUTSIDE commands/ — anything *.md under commands/ becomes a slash
# command, and on case-insensitive filesystems VISION.md would collide with vision.md.
SUPPORT="${BASE}/product-playbook"
TMP_CLONE="${HOME}/.product-playbook-install-$$"

echo "─── product-playbook installer (${SCOPE}) ─────────────────────"
mkdir -p "${TARGET}"

# Local clone vs remote
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]:-$0}" )" && pwd )"
if [[ -d "${SCRIPT_DIR}/commands" ]]; then
  echo "Mode: local install from ${SCRIPT_DIR}"
  ROOT="${SCRIPT_DIR}"
else
  echo "Mode: remote install — cloning ${REPO_URL}"
  git clone --depth 1 "${REPO_URL}" "${TMP_CLONE}" >/dev/null 2>&1
  ROOT="${TMP_CLONE}"
  trap 'rm -rf "${TMP_CLONE}"' EXIT
fi

# 1) Install the flat skills (one file = one slash command)
INSTALLED=0
for f in "${ROOT}/commands"/*.md; do
  [[ -e "$f" ]] || continue
  cp "$f" "${TARGET}/$(basename "$f")"
  echo "  ✓ $(basename "$f")"
  INSTALLED=$((INSTALLED + 1))
done

# 1b) Install directory-form skills (commands/<name>/SKILL.md + references/*) — e.g. design-system
for d in "${ROOT}/commands"/*/; do
  [[ -d "$d" ]] || continue
  name="$(basename "$d")"
  rm -rf "${TARGET:?}/${name}"   # prevent a nested copy (design-system/design-system) on re-install
  cp -R "$d" "${TARGET}/${name}"
  files_in=$(find "${TARGET}/${name}" -name "*.md" | wc -l)
  echo "  ✓ ${name}/ (${files_in} files — SKILL.md + references)"
  INSTALLED=$((INSTALLED + 1))
done

# 2) Install the companion files the skills read — into ~/.claude/product-playbook/
#    (NOT commands/, so they don't register as slash commands or collide by case).
mkdir -p "${SUPPORT}"
cp "${ROOT}/PRINCIPLES.md"        "${SUPPORT}/PRINCIPLES.md"
cp "${ROOT}/VISION.md"            "${SUPPORT}/VISION.md"
cp "${ROOT}/templates/PRODUCT.md" "${SUPPORT}/PRODUCT.md"
echo "  ✓ companions → ${SUPPORT} (PRINCIPLES.md · VISION.md · PRODUCT.md)"

if [[ "${INSTALLED}" -eq 0 ]]; then
  echo "⚠  No skills found in ${ROOT}/commands — nothing installed."
  exit 1
fi

echo "─── Done ─────────────────────────────────────────────────────"
echo "Installed ${INSTALLED} skills + companions to ${TARGET}"
if [[ "${SCOPE}" == "project" ]]; then
  echo "Project-level install — commit ${BASE} so teammates get the skills on clone."
fi
echo ""
echo "New here?  Run  /playbook  to be guided one phase at a time."
echo "Or:        /vision → /scope → /plan → /architect → …   (run each in order)"
echo "Anytime:   /drift-check   (are we still building the vision?)"
echo "Journey:   https://github.com/kish21/product-playbook#the-journey"
