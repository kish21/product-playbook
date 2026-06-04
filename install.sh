#!/usr/bin/env bash
# product-builder installer
# Copies the product-builder skills into ~/.claude/commands/ so they become
# globally available slash commands, plus the companion files the skills read
# (PRINCIPLES.md, VISION.md, templates/PRODUCT.md).
#
# Usage (one-liner, recommended):
#   curl -fsSL https://raw.githubusercontent.com/kish21/product-builder/master/install.sh | bash
#
# Usage (local clone):
#   ./install.sh

set -euo pipefail

REPO_URL="https://github.com/kish21/product-builder.git"
TARGET="${HOME}/.claude/commands"
# Companions live OUTSIDE commands/ — anything *.md under commands/ becomes a slash
# command, and on case-insensitive filesystems VISION.md would collide with vision.md.
SUPPORT="${HOME}/.claude/product-builder"
TMP_CLONE="${HOME}/.product-builder-install-$$"

echo "─── product-builder installer ────────────────────────────────"
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

# 1) Install the skills (flat, one file = one slash command)
INSTALLED=0
for f in "${ROOT}/commands"/*.md; do
  [[ -e "$f" ]] || continue
  cp "$f" "${TARGET}/$(basename "$f")"
  echo "  ✓ $(basename "$f")"
  INSTALLED=$((INSTALLED + 1))
done

# 2) Install the companion files the skills read — into ~/.claude/product-builder/
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
echo ""
echo "Start a product:  /vision  →  /scope  →  /plan  →  /architect  → …"
echo "Anytime:          /drift-check   (are we still building the vision?)"
echo "See the journey:  https://github.com/kish21/product-builder#the-journey"
