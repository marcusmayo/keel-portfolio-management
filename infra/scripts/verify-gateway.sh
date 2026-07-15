#!/usr/bin/env bash
# Verify which provider the gateway ACTUALLY routes to, and that a real call
# succeeds. Ground truth is the proxy's routing table -- NOT the model's
# self-report (every model answers "I am Claude" because the CLI system
# prompt says so) and NOT response cost (reasoning models can price at 0).
set -euo pipefail
cd "$(dirname "$0")/.."
C="${1:-keel-webchat}"
KEY=$(sudo docker exec "$C" printenv ANTHROPIC_API_KEY)
echo "== routing table (from the running proxy) =="
OUT=$(sudo docker exec "$C" sh -c "curl -s --max-time 20 http://gateway:4000/v1/model/info -H 'Authorization: Bearer $KEY'" | python3 scripts/_gwinfo.py)
echo "$OUT" | grep -v '^PROVIDERS='
PROVS=$(echo "$OUT" | sed -n 's/^PROVIDERS=//p')
echo "== live call (must return content, not just 200) =="
BODY=$(sudo docker exec "$C" sh -c "curl -s --max-time 180 http://gateway:4000/v1/messages \
  -H 'x-api-key: $KEY' -H 'anthropic-version: 2023-06-01' -H 'content-type: application/json' \
  -d '{\"model\":\"claude-sonnet-4-5\",\"max_tokens\":256,\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}]}'")
TXT=$(printf '%s' "$BODY" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read() or '{}')
if 'error' in d: print('ERROR: '+str(d['error'])[:140]); raise SystemExit(1)
print(''.join(b.get('text','') for b in d.get('content',[])).strip()[:60] or '(empty content)')
") || { echo "  $TXT"; echo "FAIL: provider rejected the call"; exit 1; }
echo "  response: $TXT"
echo "ROUTING VERIFIED: upstream provider(s) = ${PROVS}"
