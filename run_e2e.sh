#!/usr/bin/env bash
# run_e2e.sh -- Northwind end-to-end reconciliation demo, one command.
#
# Runs the full pipeline in the PROVEN canonical order and verifies against the
# corpus's ground-truth oracle. Designed to be LOUD: each step is labeled, and if
# any step's prerequisite guard fires (or the step errors), the script STOPS and
# the failing tool's own message -- which names the missing prerequisite and its
# producer -- is left on screen, followed by a clear STEP FAILED banner. It does
# not hide steps or fail opaquely.
#
# Run from the tree root (inside the container, cwd must resolve tools/ + state/):
#   docker exec -w /app keel-webchat bash run_e2e.sh
#
# THREE non-obvious ordering dependencies this script encodes (do not reorder):
#   1. reconcile MUST precede apply   -- apply.py reads state/normalized/reconcile.json
#   2. reconcile MUST follow export   -- export_multisource reruns the jira lane last,
#                                        clobbering reconcile.json; the backlog lane
#                                        must be restored for the semantic + verify steps
#   3. semantic reads the BACKLOG lane -- reconcile_semantic + verify_e2e both expect
#                                        reconcile.json in the backlog lane (step 8 output)

set -uo pipefail

# Guard: this pipeline runs INSIDE the keel container, where the Python deps
# (openpyxl, PyYAML) and the claude CLI resolve. On the host it hits the bare
# system python3 and fails with a misleading "No module named openpyxl". Detect
# the host case and print the correct invocation instead of failing opaquely.
if [ ! -f /.dockerenv ] && [ "${KEEL_DIR:-}" != "/app" ]; then
  echo "ERROR: run_e2e.sh must run INSIDE the keel container, not on the host." >&2
  echo "  It needs the container's Python env (openpyxl, PyYAML) and the claude CLI;" >&2
  echo "  on the host you'll see a misleading 'No module named openpyxl'." >&2
  echo "  Run it like this:" >&2
  echo "    docker exec -w /app keel-webchat bash run_e2e.sh --yes" >&2
  exit 2
fi

STEP=0
run_step () {
  STEP=$((STEP+1))
  local label="$1"; shift
  echo ""
  echo "================================================================"
  echo "STEP ${STEP}: ${label}"
  echo "  \$ $*"
  echo "----------------------------------------------------------------"
  "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo ""
    echo "################################################################"
    echo "STEP ${STEP} FAILED (exit ${rc}): ${label}"
    echo "  The tool's message above explains what was missing or wrong."
    echo "  A prerequisite guard (e.g. 'MISSING: reconcile.json') means an"
    echo "  earlier step did not produce its output -- fix that step, not this one."
    echo "  Pipeline STOPPED at step ${STEP}. Nothing downstream was run."
    echo "################################################################"
    exit "$rc"
  fi
  echo "  [step ${STEP} OK]"
}

# ---- DESTRUCTIVE-DEMO GUARD -------------------------------------------------
if [ "${1:-}" != "--yes" ]; then
  echo "!!! run_e2e.sh runs the FULL DEMO PIPELINE on SYNTHETIC Northwind data."
  echo "!!! DESTRUCTIVE to demo state: regenerates the corpus, OVERWRITES"
  echo "!!! keel.config.json (SOURCE_KEY_PREFIX=NWR), reseeds knowledge/import/raw/,"
  echo "!!! and drafts 25 demo items into state/."
  echo "!!! Do NOT run on a deployment holding real data."
  echo "!!! Suggested use: run once on a FRESH deployment BEFORE loading real data."
  echo "!!! Step 9 (semantic pass) waits on the LLM: ~30-60s cloud / seconds GPU /"
  echo "!!! several minutes CPU. Do not kill it."
  echo "!!!"
  echo "!!! To proceed: bash run_e2e.sh --yes"
  exit 1
fi

echo "### Northwind E2E -- full reconciliation pipeline (10 steps) ###"
echo "### cwd: $(pwd)  |  tools resolve here; LLM steps route via the configured gateway ###"

# 1. Generate the synthetic corpus (CSV jira export + XLSX backlog + expectations oracle).
run_step "generate corpus"            python3 examples/northwind/gen_corpus.py .

# 2-3. Normalize each source into canonical rows.
run_step "normalize jira (CSV)"       python3 tools/normalize_jira.py
run_step "normalize backlog (XLSX)"   python3 tools/normalize_backlog.py

# 4. Reconcile the jira lane FIRST -- produces reconcile.json proposals that apply consumes.
#    (dependency 1: reconcile-before-apply)
run_step "reconcile (jira lane)"      python3 tools/reconcile.py jira

# 5. Draft jira-source items INTO state/ (reads reconcile.json from step 4).
run_step "apply --commit (draft into state)" python3 tools/apply.py --commit

# 6. Reconcile the backlog lane -- state is now populated, so exact-ref matching fires.
run_step "reconcile (backlog lane)"   python3 tools/reconcile.py backlog

# 7. Export the cross-source workbook. NOTE: this reruns the jira lane internally and
#    LEAVES reconcile.json in the jira lane (dependency 2).
run_step "export multisource workbook" python3 tools/export_multisource.py

# 8. RESTORE the backlog lane that export clobbered -- required by steps 9 and 10.
#    (dependency 2: reconcile-after-export)
run_step "reconcile (backlog lane, restore)" python3 tools/reconcile.py backlog

# 9. Semantic pass over the ambiguous bucket via the LLM (routes to the gateway).
#    Reads the backlog-lane reconcile.json from step 8 (dependency 3). Propose-only.
run_step "semantic pass (LLM, ambiguous bucket)" python3 tools/reconcile_semantic.py

# 10. Verify the whole result against the corpus's ground-truth expectations.
run_step "verify against oracle"      python3 tools/verify_e2e.py

echo ""
echo "================================================================"
echo "E2E COMPLETE -- all 10 steps passed, oracle satisfied."
echo "To reset the demo to a clean state: bash clean_demo.sh --yes"
echo "================================================================"
