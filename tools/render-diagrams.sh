#!/usr/bin/env sh
# Regenerate the README diagrams from their mermaid sources.
#
# The README embeds pre-rendered SVGs instead of live ```mermaid blocks:
# GitHub's mermaid renderer is version-pinned and has rejected valid syntax
# in the past ("Unable to render rich display"). Pre-rendering makes the
# diagrams work on github.com, the plugin marketplace, VS Code preview and
# any README mirror, with no renderer dependency at all.
#
# Usage:  sh tools/render-diagrams.sh
# Needs:  npx (Node). Set PUPPETEER_EXECUTABLE_PATH if Chrome is not found.
set -eu

DIR="$(cd "$(dirname "$0")/.." && pwd)/docs/diagrams"

for name in architecture design-system; do
  npx -y @mermaid-js/mermaid-cli \
    -i "$DIR/$name.mmd" -o "$DIR/$name-light.svg" -t default -b transparent
  npx -y @mermaid-js/mermaid-cli \
    -i "$DIR/$name.mmd" -o "$DIR/$name-dark.svg"  -t dark    -b transparent
done

# mermaid-cli emits width="100%" with no height, which collapses inside an
# <img>. Give each SVG intrinsic dimensions taken from its viewBox.
python - "$DIR" <<'PY'
import glob, os, re, sys
for f in glob.glob(os.path.join(sys.argv[1], "*.svg")):
    s = open(f, encoding="utf-8").read()
    w, h = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s).groups()
    s = s.replace('<svg id="my-svg" width="100%"',
                  f'<svg id="my-svg" width="{round(float(w))}" height="{round(float(h))}"', 1)
    s = re.sub(r'style="max-width: [\d.]+px; background-color: transparent;"',
               'style="background-color: transparent;"', s, count=1)
    open(f, "w", encoding="utf-8", newline="\n").write(s)
    print("rendered", os.path.basename(f))
PY
