<#
.SYNOPSIS
    Hyper-V Failover Cluster Complete Setup Script

.DESCRIPTION
    Automates Hyper-V cluster creation, network configuration, and VM enablement
    Supports Windows Server 2016, 2019, 2022

.PARAMETER ClusterName
    Name for the Hyper-V cluster (default: HV-Cluster01)

.PARAMETER ClusterNodes
    Array of server names to join cluster (minimum 2, recommended 3+)

.PARAMETER ClusterIP
    Static IP address for cluster (default: auto-assigned)

.EXAMPLE
    .\Hyper-V-Cluster-Setup.ps1 -ClusterName "PROD-CLUSTER" -ClusterNodes "HVHost01","HVHost02","HVHost03"

.NOTES
    Requirements:
    - Windows Server 2016+ on all nodes
    - Hyper-V role installed on all nodes
    - Failover Clustering feature installed
    - All nodes in same domain
    - Network connectivity on port 3343 (cluster heartbeat)
    - Shared storage accessible to all nodes (SAN/NAS)

    Author: IT Vedas
    Date: 2026-07-04
#>

[CmdletBinding()]
param(
    [string]$ClusterName = "HV-Cluster01",
    [string[]]$ClusterNodes = @("HVHost01", "HVHost02", "HVHost03"),
    [string]$ClusterIP = "",
    [string]$SharedStoragePath = "\\nas-storage\cluster"
)

$ErrorActionPreference = "Stop"
trap {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Function to test prerequisites
function Test-ClusterPrerequisites {
    param([string[]]$Nodes)

    Write-Host "Testing cluster prerequisites..." -ForegroundColor Yellow

    foreach ($node in $Nodes) {
        Write-Host "  Testing $node..." -ForegroundColor Cyan

        # Test network connectivity
        if (-not (Test-NetConnection -ComputerName $node -WarningAction SilentlyContinue).PingSucceeded) {
            Write-Host "    ✗ Cannot ping $node" -ForegroundColor Red
            return $false
        }

        # Test Hyper-V installation
        try {
            $vmhost = Invoke-Command -ComputerName $node -ScriptBlock { Get-VMHost } -ErrorAction SilentlyContinue
            if ($vmhost) {
                Write-Host "    ✓ Hyper-V installed" -ForegroundColor Green
            } else {
                Write-Host "    ✗ Hyper-V not installed" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "    ✗ Could not verify Hyper-V: $_" -ForegroundColor Red
            return $false
        }

        # Test Failover Clustering
        try {
            $feature = Invoke-Command -ComputerName $node -ScriptBlock {
                Get-WindowsFeature -Name "Failover-Clustering" | Select-Object -ExpandProperty Installed
            }
            if ($feature) {
                Write-Host "    ✓ Failover Clustering installed" -ForegroundColor Green
            } else {
                Write-Host "    ✗ Failover Clustering not installed" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "    ✗ Could not verify Failover Clustering: $_" -ForegroundColor Red
            return $false
        }
    }

    return $true
}

# Function to test cluster compatibility
function Test-ClusterCompatibility {
    param([string[]]$Nodes)

    Write-Host "Running cluster compatibility tests..." -ForegroundColor Yellow

    try {
        Test-Cluster -Node $Nodes -Include "Inventory","Network","Storage","System Configuration" -Verbose

        Write-Host "✓ Cluster compatibility tests passed" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Cluster tests failed: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "=" * 70
Write-Host "Hyper-V Failover Cluster Setup Script" -ForegroundColor Cyan
Write-Host "=" * 70

# Validate prerequisites
Write-Host "`nStep 1: Validating prerequisites..." -ForegroundColor Cyan

if (-not (Test-ClusterPrerequisites -Nodes $ClusterNodes)) {
    Write-Host "Prerequisites validation failed" -ForegroundColor Red
    exit 1
}

# Test cluster compatibility
Write-Host "`nStep 2: Testing cluster compatibility..." -ForegroundColor Cyan

if (-not (Test-ClusterCompatibility -Nodes $ClusterNodes)) {
    Write-Host "Cluster compatibility tests failed - review results above" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (Y/N)"
    if ($response -ne "Y") { exit 1 }
}

# Create cluster
Write-Host "`nStep 3: Creating Hyper-V cluster..." -ForegroundColor Cyan

try {
    $existingCluster = Get-Cluster -Name $ClusterName -ErrorAction SilentlyContinue

    if ($existingCluster) {
        Write-Host "✓ Cluster '$ClusterName' already exists" -ForegroundColor Green
    } else {
        if ($ClusterIP) {
            $cluster = New-Cluster -Name $ClusterName -Node $ClusterNodes[0] -StaticAddress $ClusterIP
        } else {
            $cluster = New-Cluster -Name $ClusterName -Node $ClusterNodes[0]
        }

        Write-Host "✓ Cluster '$ClusterName' created" -ForegroundColor Green
        Start-Sleep -Seconds 5

        # Add remaining nodes
        for ($i = 1; $i -lt $ClusterNodes.Count; $i++) {
            Add-ClusterNode -Cluster $ClusterName -Name $ClusterNodes[$i]
            Write-Host "✓ Added $($ClusterNodes[$i]) to cluster" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ Failed to create cluster: $_" -ForegroundColor Red
    exit 1
}

# Configure cluster networks
Write-Host "`nStep 4: Configuring cluster networks..." -ForegroundColor Cyan

try {
    $networks = Get-ClusterNetwork -Cluster $ClusterName

    foreach ($network in $networks) {
        if ($network.Address -match "192\.168\.1\." -or $network.Name -like "*Cluster*") {
            Set-ClusterNetwork -Cluster $ClusterName -Name $network.Name -Role "ClusterAndClient"
            Write-Host "✓ Set $($network.Name) for cluster use" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ Failed to configure networks: $_" -ForegroundColor Red
}

# Configure quorum
Write-Host "`nStep 5: Configuring cluster quorum..." -ForegroundColor Cyan

try {
    if ($ClusterNodes.Count -ge 3) {
        # Use Node and File Share Majority for odd-numbered clusters
        Set-ClusterQuorum -Cluster $ClusterName -NoStorage
        Write-Host "✓ Quorum set to Node Majority" -ForegroundColor Green
    } else {
        Write-Host "⚠ Only $($ClusterNodes.Count) nodes - consider adding witness" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed to configure quorum: $_" -ForegroundColor Red
}

# Verify cluster status
Write-Host "`nStep 6: Verifying cluster status..." -ForegroundColor Cyan

try {
    $clusterInfo = Get-Cluster -Name $ClusterName
    Write-Host "`nCluster Information:" -ForegroundColor Green
    $clusterInfo | Select-Object Name,State,@{n='NodeCount';e={$_.Nodes.Count}} | Format-Table

    $nodeStatus = Get-ClusterNode -Cluster $ClusterName
    Write-Host "`nNode Status:" -ForegroundColor Green
    $nodeStatus | Select-Object Name,State,NodeWeight | Format-Table

    $networkStatus = Get-ClusterNetwork -Cluster $ClusterName
    Write-Host "`nNetwork Status:" -ForegroundColor Green
    $networkStatus | Select-Object Name,Address,Role,State | Format-Table

} catch {
    Write-Host "✗ Failed to retrieve status: $_" -ForegroundColor Red
}

# Optional: Configure shared storage
if ($SharedStoragePath) {
    Write-Host "`nStep 7: Testing shared storage access..." -ForegroundColor Cyan

    try {
        if (Test-Path -Path $SharedStoragePath) {
            Write-Host "✓ Shared storage accessible at $SharedStoragePath" -ForegroundColor Green

            foreach ($node in $ClusterNodes) {
                $testPath = "\\$node\C$\temp"
                if (Test-Path $testPath) {
                    Write-Host "  ✓ $node accessible" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "✗ Shared storage not accessible" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Error testing storage: $_" -ForegroundColor Red
    }
}

Write-Host "`n" + "=" * 70
Write-Host "Hyper-V Cluster Setup Complete!" -ForegroundColor Green
Write-Host "=" * 70
Write-Host "
Next Steps:
1. Create cluster shared volumes (CSV):
   - Add-ClusterSharedVolume -Name 'Cluster Disk 1'

2. Configure VM settings:
   - Set-VM -Name 'VMName' -MemoryStartupBytes 4GB
   - Add-VMNetworkAdapter -VM \$vm -SwitchName 'ClusterSwitch'

3. Add VMs to cluster role:
   - Add-ClusterVirtualMachineRole -VirtualMachine 'VMName'

4. Monitor cluster health:
   - Get-ClusterHealth
   - Test-Cluster -Continuous

5. Configure live migration:
   - Set-VMHost -VirtualMachineMigrationEnabled \$true
   - Test-VMResiliency -ComputerName 'HVHost01'

6. Setup monitoring:
   - System Center Virtual Machine Manager (SCVMM)
   - Windows Admin Center
   - Azure Stack HCI if applicable
" -ForegroundColor Yellow
