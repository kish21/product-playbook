#!/usr/bin/env bash
# product-playbook installer
# Copies the product-playbook skills into ~/.claude/commands/ so they become
# globally available slash commands, plus the companion files the skills read
# (PRINCIPLES.md, MECHANISMS.md, LESSONS.md, VISION.md, templates/PRODUCT.md).
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
#
# Usage (SUBSET — only the skills you name; companions are always included):
#   ./install.sh --only build,ship
#   curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh | bash -s -- --only build,ship

set -euo pipefail

REPO_URL="https://github.com/kish21/product-playbook.git"

usage() {
  cat <<'USAGE'
product-playbook installer

  ./install.sh                          install every skill, globally (~/.claude/commands/)
  ./install.sh --project <path>         install into <path>/.claude/ so teammates get it on clone
  ./install.sh --only <a,b,c>           install only the named skills (+ the companions they read)
  ./install.sh --list                   list the skill names --only accepts
  ./install.sh --help                   this message

--only and --project combine:  ./install.sh --project . --only build,ship
USAGE
}

# --- parse flags (any order) ---
SCOPE="global"
PROJECT_DIR=""
ONLY=""
LIST_ONLY="no"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      SCOPE="project"
      PROJECT_DIR="${2:-}"
      if [[ -z "${PROJECT_DIR}" || ! -d "${PROJECT_DIR}" ]]; then
        echo "⚠  --project needs an existing directory: ./install.sh --project /path/to/project"
        exit 1
      fi
      shift 2
      ;;
    --only)
      ONLY="${2:-}"
      if [[ -z "${ONLY}" ]]; then
        echo "⚠  --only needs a comma-separated list of skills: ./install.sh --only build,ship"
        exit 1
      fi
      shift 2
      ;;
    --list) LIST_ONLY="yes"; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "⚠  unknown option: $1"
      echo ""
      usage
      exit 1
      ;;
  esac
done

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

# Local clone vs remote
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]:-$0}" )" && pwd )"
if [[ -d "${SCRIPT_DIR}/commands" ]]; then
  SOURCE_NOTE="local install from ${SCRIPT_DIR}"
  ROOT="${SCRIPT_DIR}"
else
  SOURCE_NOTE="remote install — cloning ${REPO_URL}"
  git clone --depth 1 "${REPO_URL}" "${TMP_CLONE}" >/dev/null 2>&1
  ROOT="${TMP_CLONE}"
  trap 'rm -rf "${TMP_CLONE}"' EXIT
fi

# --- what this copy of the repo actually ships ---
# AVAILABLE holds every skill name: flat `commands/<name>.md` and directory-form `commands/<name>/`.
AVAILABLE=()
for f in "${ROOT}/commands"/*.md; do
  [[ -e "$f" ]] || continue
  AVAILABLE+=( "$(basename "${f%.md}")" )
done
for d in "${ROOT}/commands"/*/; do
  [[ -d "$d" ]] || continue
  AVAILABLE+=( "$(basename "$d")" )
done
if [[ "${#AVAILABLE[@]}" -eq 0 ]]; then
  echo "⚠  No skills found in ${ROOT}/commands — nothing to install."
  exit 1
fi
AVAILABLE_SORTED=$(printf '%s\n' "${AVAILABLE[@]}" | sort)

if [[ "${LIST_ONLY}" == "yes" ]]; then
  echo "product-playbook ships ${#AVAILABLE[@]} skills:"
  echo "${AVAILABLE_SORTED}" | sed 's/^/  /'
  exit 0
fi

# --- resolve the requested subset (default: everything) ---
# Names are normalised so `/build`, `build` and `build.md` all mean the same skill.
SELECTED=()
if [[ -n "${ONLY}" ]]; then
  UNKNOWN=()
  IFS=',' read -r -a REQUESTED <<< "${ONLY}"
  for raw in "${REQUESTED[@]}"; do
    name="$(echo "${raw}" | tr -d '[:space:]')"
    name="${name#/}"
    name="${name%.md}"
    [[ -z "${name}" ]] && continue
    if printf '%s\n' "${AVAILABLE[@]}" | grep -qx -- "${name}"; then
      SELECTED+=( "${name}" )
    else
      UNKNOWN+=( "${name}" )
    fi
  done
  # Fail loud, before anything is copied — a partial install is worse than none.
  if [[ "${#UNKNOWN[@]}" -gt 0 ]]; then
    echo "⚠  unknown skill(s): ${UNKNOWN[*]}"
    echo ""
    echo "Valid names (${#AVAILABLE[@]}):"
    echo "${AVAILABLE_SORTED}" | sed 's/^/  /'
    exit 1
  fi
  if [[ "${#SELECTED[@]}" -eq 0 ]]; then
    echo "⚠  --only matched no skills: ./install.sh --only build,ship"
    exit 1
  fi
else
  SELECTED=( "${AVAILABLE[@]}" )
fi

echo "─── product-playbook installer (${SCOPE}) ─────────────────────"
echo "Mode: ${SOURCE_NOTE}"
[[ -n "${ONLY}" ]] && echo "Subset: --only ${ONLY}"
mkdir -p "${TARGET}"

# 1) Install the selected skills — flat file (one file = one slash command)
#    or directory form (commands/<name>/SKILL.md + references/*), e.g. design-system.
INSTALLED=0
for name in "${SELECTED[@]}"; do
  if [[ -f "${ROOT}/commands/${name}.md" ]]; then
    # A skill that USED to ship as a directory leaves its folder behind; two forms of one skill
    # in commands/ is an ambiguous slash command, so the old form goes before the new one lands.
    rm -rf "${TARGET:?}/${name}"
    cp "${ROOT}/commands/${name}.md" "${TARGET}/${name}.md"
    echo "  ✓ ${name}.md"
  else
    rm -rf "${TARGET:?}/${name}"   # prevent a nested copy (design-system/design-system) on re-install
    rm -f  "${TARGET:?}/${name}.md"  # ...and the flat file it shipped as before it grew references/
    cp -R "${ROOT}/commands/${name}/" "${TARGET}/${name}"
    files_in=$(find "${TARGET}/${name}" -name "*.md" | wc -l)
    echo "  ✓ ${name}/ ($(echo "${files_in}" | tr -d '[:space:]') files — SKILL.md + references)"
  fi
  INSTALLED=$((INSTALLED + 1))
done

# 2) Install the companion files the skills read — into ~/.claude/product-playbook/
#    (NOT commands/, so they don't register as slash commands or collide by case).
#    Always installed, subset or not: every skill reads PRINCIPLES.md and writes the PRODUCT.md spine.
mkdir -p "${SUPPORT}"
cp "${ROOT}/PRINCIPLES.md"        "${SUPPORT}/PRINCIPLES.md"
cp "${ROOT}/references/mechanisms.md" "${SUPPORT}/MECHANISMS.md"
cp "${ROOT}/references/lessons.md"    "${SUPPORT}/LESSONS.md"
cp "${ROOT}/VISION.md"            "${SUPPORT}/VISION.md"
cp "${ROOT}/templates/PRODUCT.md" "${SUPPORT}/PRODUCT.md"
echo "  ✓ companions → ${SUPPORT} (PRINCIPLES.md · MECHANISMS.md · LESSONS.md · VISION.md · PRODUCT.md)"

echo "─── Done ─────────────────────────────────────────────────────"
echo "Installed ${INSTALLED} skill(s) + companions to ${TARGET}"
if [[ "${SCOPE}" == "project" ]]; then
  echo "Project-level install — commit ${BASE} so teammates get the skills on clone."
fi
echo ""
if [[ -n "${ONLY}" ]]; then
  echo "Subset installed. Some skills call others: /build → /code-review · /ship → /security-review"
  echo "· /drift-check → /doc-audit. Those must be available too, or the step is skipped."
  echo "Add more later:  ./install.sh --only <names>    See them all:  ./install.sh --list"
else
  echo "New here?  Run  /playbook  to be guided one phase at a time."
  echo "Or:        /vision → /scope → /plan → /architect → …   (run each in order)"
fi
echo "Anytime:   /drift-check   (are we still building the vision?)"
echo "Journey:   https://github.com/kish21/product-playbook#the-journey"
