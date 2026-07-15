// Employer profile: NO tailnet -- hard-set '' below is the visible
// statement of the boundary (an employer VM never joins a personal
// tailnet); deploy.sh additionally aborts if TAILSCALE_AUTH_KEY is
// even present in the environment. Reachability = employer private
// network; SSH allowed only from KEEL_SSH_CIDR.
using '../main.bicep'

param resourceGroupName = readEnvironmentVariable('KEEL_RG', 'keel-rg')
param location = readEnvironmentVariable('KEEL_LOCATION', 'eastus2')
param enableTailscale = false
param tailscaleAuthKey = ''
param allowedSshSourceCidr = readEnvironmentVariable('KEEL_SSH_CIDR', '')
param sshPublicKey = readEnvironmentVariable('KEEL_SSH_PUBKEY', '')
param repoUrl = readEnvironmentVariable('KEEL_REPO_URL', 'https://github.com/marcusmayo/keel-portfolio-management.git')
