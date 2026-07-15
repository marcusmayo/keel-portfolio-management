#!/usr/bin/env bash
# Submit a Keel deployment. Usage: deploy.sh personal|employer
# Enforces profile guards Bicep cannot express, then: az deployment sub create
set -euo pipefail
cd "$(dirname "$0")/.."
PROFILE="${1:?usage: deploy.sh personal|employer}"
case "$PROFILE" in
  personal)
    [ -n "${TAILSCALE_AUTH_KEY:-}" ] || { echo "ABORT: personal profile requires TAILSCALE_AUTH_KEY (single-use, ~1h expiry, ephemeral=no)"; exit 1; }
    ;;
  employer)
    # Structural boundary: an employer VM never joins a personal tailnet.
    # Abort if the key exists in the environment at all.
    [ -z "${TAILSCALE_AUTH_KEY:-}" ] || { echo "ABORT: TAILSCALE_AUTH_KEY is set in the environment; unset it -- employer VMs never join a personal tailnet"; exit 1; }
    [ -n "${KEEL_SSH_CIDR:-}" ] || { echo "ABORT: employer profile requires KEEL_SSH_CIDR (e.g. 10.0.0.0/8 or your.ip/32)"; exit 1; }
    ;;
  *) echo "ABORT: unknown profile '$PROFILE'"; exit 1 ;;
esac
[ -n "${KEEL_SSH_PUBKEY:-}" ] || { echo "ABORT: KEEL_SSH_PUBKEY required (contents of your .pub file)"; exit 1; }
command -v az >/dev/null || { echo "ABORT: az CLI not found"; exit 1; }
STAMP="keel-${PROFILE}-$(date +%Y%m%d%H%M%S)"
echo "submitting ${STAMP} (profile: ${PROFILE}, location: ${KEEL_LOCATION:-eastus2})"
az deployment sub create \
  --name "$STAMP" \
  --location "${KEEL_LOCATION:-eastus2}" \
  --parameters "params/${PROFILE}.bicepparam"
echo "deployed. Next: SSH in (tailnet / allowed CIDR), tail /var/log/keel-image-build.log, then run infra/scripts/bootstrap.sh"
