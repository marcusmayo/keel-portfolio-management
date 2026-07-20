#!/usr/bin/env bash
# Friday weekly-report generator, run by cron. Cron has a bare environment, so this script
# sets PATH and sources the API key explicitly (same reason the systemd unit does).
# On success: writes a ready-marker. On failure: writes a failed-marker + logs. Best-effort,
# never silent - the in-Keel banner reads these markers so a missed/failed run is visible.

set -o pipefail

KEEL_DIR="${KEEL_DIR:-$HOME/keel}"
PATH="$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin"
export PATH

LOG="$KEEL_DIR/logs/weekly-cron.log"
REPORTS="$KEEL_DIR/state/weekly-reports"
mkdir -p "$REPORTS" "$KEEL_DIR/logs"

# ET-aware week-ending FRIDAY date - MUST match what the /weekly skill names the report.
# The skill uses the Friday of the current week. Compute that Friday in ET:
#   day-of-week: Mon=1...Sun=7; days until Friday = (5 - dow + 7) % 7, but if already past
#   Friday in the week we still want THIS week's Friday, so anchor on ISO week.
DOW=$(TZ=America/New_York date +%u)          # 1=Mon .. 7=Sun
DELTA=$(( 5 - DOW ))                          # days from today to Friday (negative if Sat/Sun)
FRIDAY=$(TZ=America/New_York date -d "$DELTA days" +%F)
TS=$(TZ=America/New_York date '+%Y-%m-%d %H:%M ET')

# Clear any stale markers for this run.
rm -f "$REPORTS/.ready-$FRIDAY" "$REPORTS/.failed-$FRIDAY"

# Source the API key (only that line; avoid pulling in anything unexpected).
if [ -f "$KEEL_DIR/webchat/service.env" ]; then
  ANTHROPIC_API_KEY=$(grep -E '^ANTHROPIC_API_KEY=' "$KEEL_DIR/webchat/service.env" | head -1 | cut -d= -f2-)
  export ANTHROPIC_API_KEY
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "$TS | FAILED: ANTHROPIC_API_KEY not found" >> "$LOG"
  echo "Weekly report generation FAILED ($TS): API key not available. Run /weekly manually." > "$REPORTS/.failed-$FRIDAY"
  exit 1
fi

cd "$KEEL_DIR" || { echo "$TS | FAILED: cannot cd to $KEEL_DIR" >> "$LOG"; exit 1; }

echo "$TS | starting /weekly" >> "$LOG"
# Run the skill. Capture output for the log; the skill auto-saves the report itself.
if claude -p "/weekly" >> "$LOG" 2>&1; then
  if [ -f "$REPORTS/$FRIDAY.md" ]; then
    echo "Weekly report for $FRIDAY is ready for review." > "$REPORTS/.ready-$FRIDAY"
    echo "$TS | SUCCESS: report saved, ready-marker written" >> "$LOG"
  else
    # Skill returned 0 but no file landed - treat as failure so it's visible.
    echo "Weekly report generation completed but no file was saved ($TS). Run /weekly manually." > "$REPORTS/.failed-$FRIDAY"
    echo "$TS | FAILED: claude exited 0 but $FRIDAY.md missing" >> "$LOG"
    exit 1
  fi
else
  echo "Weekly report generation FAILED ($TS). Run /weekly manually." > "$REPORTS/.failed-$FRIDAY"
  echo "$TS | FAILED: claude -p exited non-zero" >> "$LOG"
  exit 1
fi
