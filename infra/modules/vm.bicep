// Keel VM module — network + compute for one instance. Called by main.bicep.
// Posture: no public IP on either profile. Personal = reached over tailnet
// (outbound WireGuard, zero inbound rules). Employer = private reachability
// assumed (VPN/peering/Bastion); SSH opened only from allowedSshSourceCidr.

param location string
param vmSize string
param adminUsername string
param sshPublicKey string
param enableTailscale bool
@secure()
param tailscaleAuthKey string
param allowedSshSourceCidr string
param deployGateway bool
param repoUrl string

var vmName = 'keel-vm'

// Cloud-init: loadTextContent needs literal paths, so both profiles load;
// ternary picks one. Placeholders replaced at deploy time. The pre-auth key
// is the ONLY secret that transits customData (not an encrypted channel):
// single-use, short-expiry, scrubbed by cloud-init after the tailnet join.
var ciTailnet = loadTextContent('../cloud-init/keel-tailnet.yaml')
var ciEmployer = loadTextContent('../cloud-init/keel-employer.yaml')
var ciRaw = enableTailscale ? ciTailnet : ciEmployer
var ciFinal = replace(replace(replace(replace(ciRaw, '__TAILSCALE_AUTH_KEY__',
  tailscaleAuthKey), '__DEPLOY_GATEWAY__', string(deployGateway)),
  '__ADMIN_USER__', adminUsername), '__KEEL_REPO_URL__', repoUrl)

// Employer-only SSH allow; explicit deny-all sits under everything at 4096
// (doctrine: the deny is visible, not implied by platform defaults).
var sshAllowRule = [{
  name: 'allow-ssh-employer-cidr'
  properties: {
    priority: 1000, direction: 'Inbound', access: 'Allow', protocol: 'Tcp'
    sourceAddressPrefix: allowedSshSourceCidr, sourcePortRange: '*'
    destinationAddressPrefix: '*', destinationPortRange: '22'
  }
}]
var denyAllRule = [{
  name: 'deny-all-inbound'
  properties: {
    priority: 4096, direction: 'Inbound', access: 'Deny', protocol: '*'
    sourceAddressPrefix: '*', sourcePortRange: '*'
    destinationAddressPrefix: '*', destinationPortRange: '*'
  }
}]

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'keel-nsg'
  location: location
  properties: {
    securityRules: concat(enableTailscale ? [] : sshAllowRule, denyAllRule)
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: 'keel-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.20.0.0/24'] }
    subnets: [{
      name: 'keel-subnet'
      properties: {
        addressPrefix: '10.20.0.0/24'
        networkSecurityGroup: { id: nsg.id }
      }
    }]
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-11-01' = {
  name: 'keel-nic'
  location: location
  properties: {
    ipConfigurations: [{
      name: 'ipcfg'
      properties: {
        subnet: { id: vnet.properties.subnets[0].id }
        privateIPAllocationMethod: 'Dynamic'
        // no publicIPAddress on any profile — by construction
      }
    }]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' = {
  name: vmName
  location: location
  properties: {
    hardwareProfile: { vmSize: vmSize }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      customData: base64(ciFinal)
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [{
            path: '/home/${adminUsername}/.ssh/authorized_keys'
            keyData: sshPublicKey
          }]
        }
      }
    }
    storageProfile: {
      imageReference: {
        // 'latest' is deliberate for the OS image: publisher point-versions
        // rotate/deprecate. Enforceable pinning lives in versions.lock at the
        // package layer, where hash verification is possible.
        publisher: 'Canonical'
        offer: 'ubuntu-24_04-lts'
        sku: 'server'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: { storageAccountType: 'StandardSSD_LRS' }
      }
    }
    networkProfile: { networkInterfaces: [{ id: nic.id }] }
    diagnosticsProfile: {
      // Serial log is where cloud-init failures and hash-mismatch aborts
      // surface (silent-failure doctrine) — managed boot diagnostics on.
      bootDiagnostics: { enabled: true }
    }
  }
}

output privateIp string = nic.properties.ipConfigurations[0].properties.privateIPAddress
