// Personal profile: tailnet-joined, zero inbound. Deploy via
// infra/scripts/deploy.sh personal  (reads env: TAILSCALE_AUTH_KEY,
// KEEL_SSH_PUBKEY; optional KEEL_RG, KEEL_LOCATION, KEEL_REPO_URL).
using '../main.bicep'

param resourceGroupName = readEnvironmentVariable('KEEL_RG', 'keel-personal-rg')
param location = readEnvironmentVariable('KEEL_LOCATION', 'eastus2')
param enableTailscale = true
param tailscaleAuthKey = readEnvironmentVariable('TAILSCALE_AUTH_KEY', '')
param allowedSshSourceCidr = ''
param sshPublicKey = readEnvironmentVariable('KEEL_SSH_PUBKEY', '')
param repoUrl = readEnvironmentVariable('KEEL_REPO_URL', 'https://github.com/marcusmayo/keel-portfolio-management.git')
