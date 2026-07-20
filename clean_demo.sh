#!/usr/bin/env bash
# clean_demo.sh -- reset the Northwind DEMO to a clean state.
# Removes ONLY demo-generated artifacts (corpus, drafted state, normalized data,
# exports, people-pages, semantic verdicts) and restores keel.config.json.
# Does NOT touch secrets (keel.env), code, or the container. Scoped -- never a
# blanket git clean.  After this, `bash run_e2e.sh --yes` regenerates everything.
#
#   bash clean_demo.sh --yes
set -uo pipefail
if [ "${1:-}" != "--yes" ]; then
  echo "clean_demo.sh removes DEMO-GENERATED artifacts and restores keel.config.json."
  echo "It does NOT delete secrets, code, or the container."
  echo "To proceed: bash clean_demo.sh --yes"
  exit 1
fi
echo "=== removing demo-generated artifacts ==="
rm -rf knowledge/import/raw/* 2>/dev/null && echo "  cleared knowledge/import/raw/"
rm -f  knowledge/people/*.md 2>/dev/null && echo "  cleared knowledge/people/"
rm -rf knowledge/inbox/* 2>/dev/null && echo "  cleared knowledge/inbox/"
rm -f  state/*.yaml state/*.yml 2>/dev/null && echo "  cleared drafted state/ items"
rm -rf state/normalized/* 2>/dev/null && echo "  cleared state/normalized/"
rm -rf exports/* 2>/dev/null && echo "  cleared exports/"
rm -f  expectations.json 2>/dev/null && echo "  removed expectations.json"
echo "=== restoring keel.config.json from git (undo the NWR overwrite) ==="
if git rev-parse --git-dir >/dev/null 2>&1; then
  git checkout -- keel.config.json 2>/dev/null && echo "  restored keel.config.json" || echo "  (keel.config.json not tracked/changed -- skipped)"
else
  echo "  (not a git repo -- cannot restore keel.config.json automatically)"
fi
echo "=== clean. Re-run the demo with: bash run_e2e.sh --yes ==="
