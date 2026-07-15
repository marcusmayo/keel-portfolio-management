#!/usr/bin/env bash
# Birth the public `keel` repo: whitelist-copy tracked code from this
# working tree (keel-agent), flip config, gate for residue, init+commit.
# NEVER pushes -- prints next steps. Usage: seed-fresh-repo.sh [dest]
set -euo pipefail
cd "$(dirname "$0")/../.."
DEST="${1:-$HOME/keel-public}"
[ -e "$DEST" ] && { echo "ABORT: $DEST exists"; exit 1; }
mkdir -p "$DEST"

# Whitelist: tracked files only (git archive reads the index -- untracked
# secrets/ignored clutter cannot transit even inside these paths).
for p in tools gate .claude infra webchat system CLAUDE.md .gitignore .dockerignore keel.config.json; do
  git archive HEAD -- "$p" | tar -x -C "$DEST"
done
# Drop tracked backup/stale copies git archive carried (index-tracked;
# .dockerignore does not apply to git archive).
find "$DEST" -type f \( -name '*.pre-*' -o -name '*.bak*' \) -delete

# Config flip: fresh repo ships prefix "" (graceful-skip default).
# JSON round-trip (re-serializes indent-2); asserts the expected value.
python3 - "$DEST" << 'PY'
import json, sys
p = f"{sys.argv[1]}/keel.config.json"
cfg = json.load(open(p))
assert cfg.get("SOURCE_KEY_PREFIX") == "NGE", f"unexpected: {cfg.get('SOURCE_KEY_PREFIX')!r}"
cfg["SOURCE_KEY_PREFIX"] = ""
json.dump(cfg, open(p, "w"), indent=2); open(p, "a").write("\n")
print("config flipped: SOURCE_KEY_PREFIX NGE -> \"\"")
PY

# License (Apache-2.0, ruled) + README stub if the tree ships none.
curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt > "$DEST/LICENSE"
grep -q "Apache License" "$DEST/LICENSE" || { echo "ABORT: LICENSE fetch bad"; exit 1; }
[ -f "$DEST/README.md" ] || cat > "$DEST/README.md" << 'MD'
# Keel

Single-operator portfolio management: deterministic Python tools, YAML
state, Excel round-trip review, LLM reserved for semantic judgment only.
Runs as a pinned, hash-verified container -- self-contained via Docker
Compose, or on Azure via the Bicep templates in infra/.

Quickstart and full documentation: see infra/README.md.
(Stub README -- full public README pending.)
MD

# Residue gate: employer terms, people, tailnet IP, live secret shapes.
# (tskey-/sk-ant- require 8+ alnum so the cloud-init scrub regex and
# docs don't false-positive.) Any hit aborts pre-commit.
# Name pattern from knowledge/people/ (+ operator) so the gate fails on
# ANY human name, employer term, tailnet IP, or secret shape.
ROSTER=$(for f in knowledge/people/*.md; do basename "$f" .md | tr '-' ' '; done \
          | awk 'NF>=2' | sort -u | paste -sd'|')
HITS=$( { grep -rniE --exclude=seed-fresh-repo.sh --exclude=smoke-test.sh --exclude=build-image.sh --exclude=README.md --exclude=smoke-test.sh --exclude=README.md \
            "nexgen|nvcc|NGE-[0-9]|marcus|100\.91\.75\.11|\b(${ROSTER})\b" "$DEST" || true; \
          grep -rnE "tskey-[A-Za-z0-9]{8}|sk-ant-[A-Za-z0-9]{8}" "$DEST" || true; } )
HITS=$(printf "%s\n" "$HITS" | grep -v "github.com/marcusmayo" || true)
if [ -n "$HITS" ]; then echo "ABORT: residue in seeded tree:"; echo "$HITS"; exit 1; fi
echo "residue gate: clean"

cd "$DEST"
git init -q -b main
git add -A   # fresh whitelisted tree only; every file just passed the gate
git commit -q -m "Initial commit: Keel -- deterministic portfolio management agent

Seeded from the private build repo via whitelist (tracked code only:
tools, gate, skills, webchat, infra). No data, no history, no secrets.
SOURCE_KEY_PREFIX ships empty; License Apache-2.0."
echo "SEEDED: $DEST  ($(git ls-files | wc -l) files, $(git rev-parse --short HEAD))"
echo "Next: create PUBLIC GitHub repo 'keel-portfolio-management' (no init), then:"
echo "  cd $DEST && git remote add origin https://github.com/marcusmayo/keel-portfolio-management.git && git push -u origin main"
