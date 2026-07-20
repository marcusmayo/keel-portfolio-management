#!/usr/bin/env bash
# Daily digest generator, run by cron at 4:30pm ET. Same bare-environment handling as the
# weekly wrapper: sets PATH and sources the API key. Writes a ready-marker on success so the
# in-Keel banner can surface it; failure writes a failed-marker + logs. Never silent.
# Respects the banner mute switch (see below) - when muted, still generates, just no banner.

set -o pipefail

KEEL_DIR="${KEEL_DIR:-$HOME/keel}"
PATH="$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin"
export PATH

LOG="$KEEL_DIR/logs/digest-cron.log"
DIGESTS="$KEEL_DIR/state/daily-digests"
mkdir -p "$DIGESTS" "$KEEL_DIR/logs"

# Today in ET (the digest covers today; the skill defaults to today with no argument).
TODAY=$(TZ=America/New_York date +%F)
TS=$(TZ=America/New_York date '+%Y-%m-%d %H:%M ET')

rm -f "$DIGESTS/.ready-$TODAY" "$DIGESTS/.failed-$TODAY"

if [ -f "$KEEL_DIR/webchat/service.env" ]; then
  ANTHROPIC_API_KEY=$(grep -E '^ANTHROPIC_API_KEY=' "$KEEL_DIR/webchat/service.env" | head -1 | cut -d= -f2-)
  export ANTHROPIC_API_KEY
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "$TS | FAILED: ANTHROPIC_API_KEY not found" >> "$LOG"
  echo "Daily digest FAILED ($TS): API key not available." > "$DIGESTS/.failed-$TODAY"
  exit 1
fi

cd "$KEEL_DIR" || { echo "$TS | FAILED: cannot cd to $KEEL_DIR" >> "$LOG"; exit 1; }

echo "$TS | starting /digest for $TODAY" >> "$LOG"
# Capture the digest text to a dated file so the banner can show it / you can pull it later.
if claude -p "/digest" > "$DIGESTS/$TODAY.md" 2>> "$LOG"; then
  if [ -s "$DIGESTS/$TODAY.md" ]; then
    echo "Daily digest for $TODAY is ready." > "$DIGESTS/.ready-$TODAY"
    echo "$TS | SUCCESS: digest saved, ready-marker written" >> "$LOG"
  else
    echo "Daily digest generated but was empty ($TS)." > "$DIGESTS/.failed-$TODAY"
    echo "$TS | FAILED: digest output empty" >> "$LOG"
    exit 1
  fi
else
  echo "Daily digest FAILED ($TS)." > "$DIGESTS/.failed-$TODAY"
  echo "$TS | FAILED: claude -p exited non-zero" >> "$LOG"
  exit 1
fi
