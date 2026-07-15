// Keel — infrastructure entrypoint (subscription scope).
// Creates the resource group and deploys the Keel VM module.
// Profile selection happens in params/*.bicepparam — see infra/README.md.
// Guards that Bicep cannot express (e.g. tailscaleAuthKey required when
// enableTailscale) are enforced by scripts/deploy.sh before submission.
targetScope = 'subscription'

@description('Resource group created for this Keel instance.')
param resourceGroupName string

@description('Azure region.')
param location string = 'eastus2'

@description('VM size. Default B2s_v2: 2 vCPU / 8 GiB burstable — fits the spiky claude -p + Node workload.')
param vmSize string = 'Standard_B2s_v2'

@description('Admin username on the VM.')
param adminUsername string = 'keeladmin'

@description('SSH public key for the admin user. Public material, not a secret.')
param sshPublicKey string

@description('true = personal profile: VM joins your tailnet, NSG denies all inbound. false = employer profile: no Tailscale; SSH reachable only from allowedSshSourceCidr.')
param enableTailscale bool

@description('Tailscale pre-auth key (single-use, short expiry, ephemeral=no). Required when enableTailscale is true. Injected into cloud-init, scrubbed after join.')
@secure()
param tailscaleAuthKey string = ''

@description('CIDR allowed to reach SSH when enableTailscale is false (employer profile). Ignored on the personal profile.')
param allowedSshSourceCidr string = ''

@description('Provision the optional LiteLLM gateway (OFF by default; ships only behind the supply-chain gate documented in infra/README.md).')
param deployGateway bool = false

@description('Git URL cloned by cloud-init (anonymous https; the public keel repo).')
param repoUrl string = 'https://github.com/marcusmayo/keel-portfolio-management.git'

var deploymentProfile = enableTailscale ? 'personal-tailnet' : 'employer'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    app: 'keel'
    profile: deploymentProfile
  }
}

module keelVm 'modules/vm.bicep' = {
  scope: rg
  name: 'keel-vm-deploy'
  params: {
    location: location
    vmSize: vmSize
    adminUsername: adminUsername
    sshPublicKey: sshPublicKey
    enableTailscale: enableTailscale
    tailscaleAuthKey: tailscaleAuthKey
    allowedSshSourceCidr: allowedSshSourceCidr
    deployGateway: deployGateway
    repoUrl: repoUrl
  }
}

output resourceGroupName string = rg.name
output profile string = deploymentProfile
