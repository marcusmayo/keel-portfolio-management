#!/usr/bin/env bash
# First-login bootstrap on a freshly provisioned VM (either profile).
# Injects the two runtime secrets and starts Keel. Run as the admin user.
set -euo pipefail
cd "$(dirname "$0")/../.."
ENV=infra/docker/keel.env
[ -f "$ENV" ] && { echo "ABORT: $ENV exists -- already bootstrapped (delete to redo)"; exit 1; }
sudo docker image inspect keel:latest >/dev/null 2>&1 || { echo "image missing -- building"; ./infra/scripts/build-image.sh; }
echo "== TOTP enrollment =="
SECRET="$(./infra/scripts/gen-totp.sh)"
echo "== Anthropic API key (input hidden) =="
read -rs -p "ANTHROPIC_API_KEY: " APIKEY; echo
umask 177
printf 'TOTP_SECRET=%s\nANTHROPIC_API_KEY=%s\n' "$SECRET" "$APIKEY" > "$ENV"
umask 022
grep -q '^DEPLOY_GATEWAY=true' .provision-flags 2>/dev/null \
  && echo "NOTE: gateway requested; deferred behind the LiteLLM vetting gate (infra/README)"
# Publish address: tailnet IP when joined; loopback otherwise (reach via SSH tunnel).
ADDR=127.0.0.1
command -v tailscale >/dev/null 2>&1 && { ADDR="$(tailscale ip -4 2>/dev/null | head -1)" || ADDR=127.0.0.1; }
[ -n "$ADDR" ] || ADDR=127.0.0.1
echo "publishing webchat on ${ADDR}:8443"
sudo env KEEL_PUBLISH_ADDR="$ADDR" docker compose -f infra/docker/compose.yaml up -d
./infra/scripts/smoke-test.sh keel-webchat "http://${ADDR}:8443"
echo "bootstrap complete -- webchat: http://${ADDR}:8443"
