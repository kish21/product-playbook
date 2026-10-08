#!/usr/bin/env bash
# product-playbook installer
# Copies the product-playbook skills (each a <name>/SKILL.md folder) into the skills folder of the tool you
# use - Claude Code, Cursor or Antigravity - plus the companion files the skills read (PRINCIPLES.md,
# MECHANISMS.md, MECHANISMS-ON-DEMAND.md, LESSONS.md, STATE-MODEL.md, CAPABILITIES.md, VISION.md, the
# templates, the case files, status.py, session_cost.py), and rewrites every plugin path in them
# (`${CLAUDE_PLUGIN_ROOT}/...`) to where it put the file. Claude Code users can install the plugin instead.
#
# Usage (one-liner, recommended):
#   curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh | bash
#
# Usage (local clone, GLOBAL — available in all your projects):
#   ./install.sh                         Claude Code  → ~/.claude/skills/
#   ./install.sh --tool cursor           Cursor       → ~/.cursor/skills/
#   ./install.sh --tool antigravity      Antigravity  → ~/.gemini/config/skills/
#   ./install.sh --tool codex            Codex        → ~/.codex/skills/
#
# Usage (PROJECT-LEVEL — into one project only; the install is never committed, each teammate runs this too):
#   ./install.sh --project /path/to/project                      → <project>/.claude/skills/
#   ./install.sh --project /path/to/project --tool cursor        → <project>/.agents/skills/ (Cursor, Antigravity, Codex)
#
# Usage (SUBSET — only the skills you name; companions are always included):
#   ./install.sh --only build,ship
#   curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh | bash -s -- --only build,ship

set -euo pipefail

REPO_URL="https://github.com/kish21/product-playbook.git"

usage() {
  cat <<'USAGE'
product-playbook installer

  ./install.sh                          install every skill, globally, for Claude Code (~/.claude/skills/)
  ./install.sh --tool <tool>            claude (default) · cursor (~/.cursor/skills/) · antigravity (~/.gemini/config/skills/)
                                          · codex (~/.codex/skills/)
  ./install.sh --project <path>         install into <path> only (never committed; each teammate installs):
                                          claude → <path>/.claude/skills/ · cursor, antigravity or codex → <path>/.agents/skills/
  ./install.sh --only <a,b,c>           install only the named skills (+ the companions they read)
  ./install.sh --list                   list the skill names --only accepts
  ./install.sh --help                   this message

Flags combine:  ./install.sh --project . --tool cursor --only build,ship
USAGE
}

# --- parse flags (any order) ---
SCOPE="global"
PROJECT_DIR=""
ONLY=""
LIST_ONLY="no"
TOOL="claude"
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
    --tool)
      TOOL="${2:-}"
      case "${TOOL}" in
        claude|cursor|antigravity|codex) ;;
        *) echo "⚠  --tool is claude, cursor, antigravity or codex"; exit 1 ;;
      esac
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

# --- where each tool reads skills (references/capabilities.md §Where the skills are installed) ---
# BASE holds the skills folder and the companions folder; REL_BASE is BASE relative to the project root, used
# in the rewritten paths of a project install so they still resolve after a teammate clones.
if [[ "${SCOPE}" == "project" ]]; then
  case "${TOOL}" in
    claude) REL_BASE=".claude" ;;
    *)      REL_BASE=".agents" ;;   # Cursor, Antigravity and Codex all read <project>/.agents/skills/
  esac
  BASE="${PROJECT_DIR}/${REL_BASE}"
else
  case "${TOOL}" in
    claude)      BASE="${HOME}/.claude" ;;
    cursor)      BASE="${HOME}/.cursor" ;;
    antigravity) BASE="${HOME}/.gemini/config" ;;
    codex)       BASE="${HOME}/.codex" ;;
  esac
fi
TARGET="${BASE}/skills"
# Companions live OUTSIDE skills/ - a folder there is read as a skill, and on case-insensitive filesystems
# VISION.md would collide with the vision skill.
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

# --- what this copy of the repo actually ships: every commands/<name>/SKILL.md ---
AVAILABLE=()
for d in "${ROOT}/commands"/*/; do
  [[ -f "${d}SKILL.md" ]] || continue
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

echo "─── product-playbook installer (${TOOL}, ${SCOPE}) ─────────────────────"
echo "Mode: ${SOURCE_NOTE}"
[[ -n "${ONLY}" ]] && echo "Subset: --only ${ONLY}"
mkdir -p "${TARGET}"

# 1) Install the selected skills: each is a folder, SKILL.md + its own references/ and engines.
INSTALLED=0
for name in "${SELECTED[@]}"; do
  rm -rf "${TARGET:?}/${name}"   # prevent a nested copy (build/build) on re-install
  cp -R "${ROOT}/commands/${name}/" "${TARGET}/${name}"
  # Claude Code: older versions of this installer put skills in commands/ - two copies of one skill is an
  # ambiguous slash command, so the old one goes.
  if [[ "${TOOL}" == "claude" ]]; then
    rm -rf "${BASE:?}/commands/${name}"
    rm -f  "${BASE:?}/commands/${name}.md"
  fi
  files_in=$(find "${TARGET}/${name}" -type f | wc -l)
  echo "  ✓ ${name}/ ($(echo "${files_in}" | tr -d '[:space:]') files)"
  INSTALLED=$((INSTALLED + 1))
done

# 2) Install the companion files the skills read — always, subset or not: every skill reads PRINCIPLES.md.
mkdir -p "${SUPPORT}"
cp "${ROOT}/PRINCIPLES.md"        "${SUPPORT}/PRINCIPLES.md"
cp "${ROOT}/references/mechanisms.md" "${SUPPORT}/MECHANISMS.md"
cp "${ROOT}/references/mechanisms-on-demand.md" "${SUPPORT}/MECHANISMS-ON-DEMAND.md"
cp "${ROOT}/references/lessons.md"    "${SUPPORT}/LESSONS.md"
cp "${ROOT}/references/case-files-build.md" "${SUPPORT}/CASE-FILES-BUILD.md"
for f in "${ROOT}/references"/case-files-*.md; do   # every other case file a skill points at, same name
  cp "$f" "${SUPPORT}/$(basename "$f")"
done
cp "${ROOT}/docs/state-model.md"   "${SUPPORT}/STATE-MODEL.md"
cp "${ROOT}/references/capabilities.md" "${SUPPORT}/CAPABILITIES.md"
cp "${ROOT}/references/agent.md"  "${SUPPORT}/AGENT.md"
cp "${ROOT}/VISION.md"           "${SUPPORT}/VISION.md"
cp "${ROOT}/templates/PRODUCT.md" "${SUPPORT}/PRODUCT.md"
mkdir -p "${SUPPORT}/templates"
cp "${ROOT}/templates"/* "${SUPPORT}/templates/"
cp "${ROOT}/tools/session_cost.py" "${SUPPORT}/session_cost.py"
cp "${ROOT}/tools/status.py" "${SUPPORT}/status.py"
cp "${ROOT}/tools/run_report.py" "${SUPPORT}/run_report.py"
cp "${ROOT}/tools/engine.sha256" "${SUPPORT}/ENGINE.sha256"   # status.py refuses a checker edited after install
# the helper agents' briefs (/vision's research helper): read from here by any tool, and installed below where the
# tool looks for its own agents
mkdir -p "${SUPPORT}/agents"
cp "${ROOT}/agents"/*.md "${SUPPORT}/agents/"
echo "  ✓ companions → ${SUPPORT} (PRINCIPLES.md · MECHANISMS.md · MECHANISMS-ON-DEMAND.md · LESSONS.md · CASE-FILES-BUILD.md · case files · STATE-MODEL.md · CAPABILITIES.md · AGENT.md · VISION.md · PRODUCT.md · templates/ · session_cost.py · status.py · run_report.py)"

# 3) Point every plugin path at the file just installed.
#    Skills name the plugin's paths (`${CLAUDE_PLUGIN_ROOT}/…`), which Claude Code fills in only for a plugin;
#    Cursor and Antigravity never fill them in. So a copy install rewrites them all. A project install gets
#    paths relative to the project root, so they still work after a teammate clones, and the header's fallback
#    note is replaced by where that root is: an agent may start in a subfolder.
FALLBACK_NOTE=()
if [[ "${SCOPE}" == "project" ]]; then
  RULES_AT="${REL_BASE}/product-playbook"
  SKILLS_AT="${REL_BASE}/skills"
  FALLBACK_NOTE=( -e "s|(a path still starting with \`\\\$\`: [^)]*)|(paths start at the project root: the nearest folder, from the working directory up, that holds \`${RULES_AT}/\`)|g" )
elif command -v cygpath >/dev/null 2>&1; then
  RULES_AT="$(cygpath -m "${SUPPORT}")"   # Git Bash on Windows: C:/Users/…, a path every tool opens
  SKILLS_AT="$(cygpath -m "${TARGET}")"
else
  RULES_AT="${SUPPORT}"
  SKILLS_AT="${TARGET}"
fi
RULES_ESC="$(printf '%s' "${RULES_AT}" | sed 's/[&|\\]/\\&/g')"
SKILLS_ESC="$(printf '%s' "${SKILLS_AT}" | sed 's/[&|\\]/\\&/g')"
PLUGIN_ROOT='\${CLAUDE_PLUGIN_ROOT}/'
point_rule_paths() {
  sed -i.bak \
    -e "s|${PLUGIN_ROOT}PRINCIPLES\.md|${RULES_ESC}/PRINCIPLES.md|g" \
    -e "s|${PLUGIN_ROOT}references/mechanisms-on-demand\.md|${RULES_ESC}/MECHANISMS-ON-DEMAND.md|g" \
    -e "s|${PLUGIN_ROOT}references/mechanisms\.md|${RULES_ESC}/MECHANISMS.md|g" \
    -e "s|${PLUGIN_ROOT}references/lessons\.md|${RULES_ESC}/LESSONS.md|g" \
    -e "s|${PLUGIN_ROOT}references/case-files-build\.md|${RULES_ESC}/CASE-FILES-BUILD.md|g" \
    -e "s|${PLUGIN_ROOT}references/\(case-files-[a-z-]*\.md\)|${RULES_ESC}/\1|g" \
    -e "s|${PLUGIN_ROOT}docs/state-model\.md|${RULES_ESC}/STATE-MODEL.md|g" \
    -e "s|${PLUGIN_ROOT}references/capabilities\.md|${RULES_ESC}/CAPABILITIES.md|g" \
    -e "s|${PLUGIN_ROOT}references/agent\.md|${RULES_ESC}/AGENT.md|g" \
    -e "s|${PLUGIN_ROOT}tools/session_cost\.py|${RULES_ESC}/session_cost.py|g" \
    -e "s|${PLUGIN_ROOT}tools/status\.py|${RULES_ESC}/status.py|g" \
    -e "s|${PLUGIN_ROOT}tools/run_report\.py|${RULES_ESC}/run_report.py|g" \
    -e "s|${PLUGIN_ROOT}templates/PRODUCT\.md|${RULES_ESC}/PRODUCT.md|g" \
    -e "s|${PLUGIN_ROOT}templates/|${RULES_ESC}/templates/|g"     -e "s|${PLUGIN_ROOT}agents/|${RULES_ESC}/agents/|g" \
    -e "s|${PLUGIN_ROOT}commands/\([a-z-]*\)/|${SKILLS_ESC}/\1/|g" \
    ${FALLBACK_NOTE[@]+"${FALLBACK_NOTE[@]}"} \
    "$1"
  rm -f "$1.bak"
}
for name in "${SELECTED[@]}"; do
  while IFS= read -r f; do point_rule_paths "$f"; done < <(find "${TARGET}/${name}" -name "*.md")
done
for f in "${SUPPORT}"/*.md "${SUPPORT}/templates"/*.md; do point_rule_paths "$f"; done
echo "  ✓ plugin paths → ${RULES_AT} (rules) · ${SKILLS_AT} (engines)"

# 3b) The Python that works here, by its full path, in every command the skills print: a logged Codex run's
#     PowerShell had no `python`, and it spent 5 calls finding one (`uv run python`, sandbox-denied at first).
PY=""
for cand in python3 python py; do
  command -v "${cand}" >/dev/null 2>&1 || continue
  args=(); [[ "${cand}" == "py" ]] && args=(-3)
  exe="$("${cand}" "${args[@]}" -c 'import sys; print(sys.executable) if sys.version_info >= (3, 10) else None' 2>/dev/null | tr -d '\r')"
  if [[ -n "${exe}" ]]; then PY="${exe}"; break; fi
done
# A Microsoft Store Python is an app alias under ...\WindowsApps\: a sandboxed agent cannot run it (a logged Codex
# /vision got "CommandNotFoundException" on it and spent 5 calls finding another). Prefer a regular install.
if [[ "${PY}" == *WindowsApps* ]]; then
  for exe in "${LOCALAPPDATA:-}"/Programs/Python/Python3*/python.exe "${APPDATA:-}"/uv/python/cpython-3.*/python.exe; do
    [[ -f "${exe}" ]] || continue
    ok="$("${exe}" -c 'import sys; print(1) if sys.version_info >= (3, 10) else None' 2>/dev/null | tr -d '\r')"
    if [[ "${ok}" == "1" ]]; then PY="${exe}"; break; fi
  done
fi
if [[ -n "${PY}" ]]; then
  command -v cygpath >/dev/null 2>&1 && PY="$(cygpath -m "${PY}")"
  # Unquoted, so the one command runs in bash AND PowerShell: to PowerShell a quoted path is a string, not a program
  # (a logged Cursor /vision's first command failed "Unexpected token"). A path with spaces: its short form first.
  [[ "${PY}" == *" "* ]] && command -v cygpath >/dev/null 2>&1 && PY="$(cygpath -m -s "${PY}")"
  PYQ="${PY}"; [[ "${PY}" == *" "* ]] && PYQ="\"${PY}\""
  PY_ESC="$(printf '%s' "${PYQ}" | sed 's/[&|\\]/\\&/g')"
  for name in "${SELECTED[@]}"; do
    while IFS= read -r f; do
      sed -i.bak -e "s|python ${RULES_ESC}/|${PY_ESC} ${RULES_ESC}/|g" \
                 -e "s|python ${SKILLS_ESC}/|${PY_ESC} ${SKILLS_ESC}/|g" "$f"
      rm -f "$f.bak"
    done < <(find "${TARGET}/${name}" -name "*.md")
  done
  printf '%s\n' "${PY}" > "${SUPPORT}/PYTHON"
  echo "  ✓ commands use ${PY}"
  # Codex's sandbox cannot see the user's AppData, where the Store alias and a per-user Python live: a logged
  # Codex /vision's first command failed there, and it hunted until it found the Azure CLI's bundled Python
  # (2026-10-01). Its shell tool can run one command outside the sandbox, and a prefix the user approves once
  # covers the rest - so every skill opens with that, before its first command.
  if [[ "${TOOL}" == "codex" && "$(printf '%s' "${PY}" | tr '[:upper:]' '[:lower:]')" == */appdata/* ]]; then
    NOTE="> **Codex: the playbook's Python is outside your sandbox.** Run every \`${PYQ} … status.py …\` command with \`sandbox_permissions: \"require_escalated\"\`, the \`justification\` \"Run the playbook's status script\" and \`prefix_rule\` = that command's first two words, so the user approves once. Never search for another Python. Each escalated call is reviewed on its own: use the fewest - one start, one \`set … --commit\` (it saves; no git call of your own)."
    for name in "${SELECTED[@]}"; do
      f="${TARGET}/${name}/SKILL.md"
      [[ -f "$f" ]] || continue
      awk -v note="${NOTE}" '
        /^---[[:space:]]*$/ && fm < 2 { fm++; print; if (fm == 2) { print ""; print note }; next }
        { print }' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    done
    echo "  ✓ Codex: each skill runs the playbook's Python outside the sandbox (the user approves once)"
    # in the Codex VS Code extension every escalated call opened its own review thread, and the owner's sends
    # were lost three times; the standalone Codex app handled the same thread at once
    echo "  ⚠ Codex: run the playbook in the Codex app - the VS Code extension can lose your replies while a command is reviewed"
  fi
else
  echo "  ⚠  no Python 3.10+ found: the skills' commands say \`python\` - install Python, then run this again"
fi

# 3c) The helper agents, where each tool looks for its own (CAPABILITIES.md §Subagents). Codex has no agent files:
#     /vision tells it to spawn one with the brief from ${SUPPORT}/agents/.
case "${TOOL}" in
  claude)      AGENTS_AT="${BASE}/agents" ;;
  cursor)      AGENTS_AT="$([[ "${SCOPE}" == "project" ]] && echo "${PROJECT_DIR}/.cursor/agents" || echo "${HOME}/.cursor/agents")" ;;
  antigravity) AGENTS_AT="${BASE}/agents" ;;
  *)           AGENTS_AT="" ;;
esac
if [[ -n "${AGENTS_AT}" ]]; then
  mkdir -p "${AGENTS_AT}"
  cp "${SUPPORT}/agents"/*.md "${AGENTS_AT}/"
  echo "  ✓ helper agents → ${AGENTS_AT}"
fi

# 4) Which copy this is. `status.py next` prints it first, so a run can see which playbook it is using.
VERSION="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${ROOT}/.claude-plugin/plugin.json" | head -1)"
[[ -z "${VERSION}" ]] && VERSION="unknown"
printf '%s\n' "${VERSION}" > "${SUPPORT}/VERSION"
# status.py reads which tool this copy serves: off Claude Code a review is recorded by the route that ran and the
# user is told which one (a logged Gemini build recorded a /code-review its tool does not have)
printf '%s\n' "${TOOL}" > "${SUPPORT}/TOOL"

# 5) Cursor also lists the skills Claude Code has installed, under the same names and descriptions, so a user
#    can start the other copy without knowing (a logged test run did). Label this copy where the menu shows it.
if [[ "${TOOL}" != "claude" ]]; then
  LABEL="[product-playbook ${VERSION}]"
  for name in "${SELECTED[@]}"; do
    f="${TARGET}/${name}/SKILL.md"
    awk -v label="${LABEL} " '
      /^---[[:space:]]*$/ { fm++; print; next }
      fm == 1 && !done && pending { match($0, /^[[:space:]]*/); print substr($0, 1, RLENGTH) label substr($0, RLENGTH + 1); pending = 0; done = 1; next }
      fm == 1 && !done && /^description:[[:space:]]*>-?[[:space:]]*$/ { print; pending = 1; next }
      fm == 1 && !done && /^description:[[:space:]]/ { v = $0; sub(/^description:[[:space:]]*/, "", v)
        if (v ~ /^".*"$/) { v = substr(v, 2, length(v) - 2) }
        print "description: >"; print "  " label v; done = 1; next }
      { print }' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  done
  echo "  ✓ each skill's description starts ${LABEL}"
  if grep -qs '"product-playbook@[^"]*"[[:space:]]*:[[:space:]]*true' "${HOME}/.claude/settings.json"; then
    echo "  ⚠  Claude Code also has product-playbook switched on, and Cursor lists Claude Code's skills too: you may"
    echo "     see each skill twice. Pick the one whose description starts ${LABEL}."
  fi
fi

echo "─── Done ─────────────────────────────────────────────────────"
echo "Installed ${INSTALLED} skill(s) + companions to ${TARGET}"
if [[ "${SCOPE}" == "project" ]]; then
  echo "Project-level install in ${REL_BASE}/ - it stays out of git (the save never commits it); each teammate runs this installer."
fi
echo ""
if [[ -n "${ONLY}" ]]; then
  echo "Subset installed. Some skills call others (review, security review, running the app) - see"
  echo "${SUPPORT}/CAPABILITIES.md for your tool's way to do each."
  echo "Add more later:  ./install.sh --only <names>    See them all:  ./install.sh --list"
else
  echo "New here?  Run  /playbook  to be guided one phase at a time."
  echo "Or:        /vision → /scope → /plan → /architect → …   (run each in order)"
fi
echo "Anytime:   /drift-check   (are we still building the vision?)"
echo "Your tool: ${SUPPORT}/CAPABILITIES.md says how it does code review, security review, the live check."
