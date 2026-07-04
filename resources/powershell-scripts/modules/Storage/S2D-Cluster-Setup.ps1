<#
.SYNOPSIS
    Storage Spaces Direct (S2D) Cluster Complete Setup Script

.DESCRIPTION
    Automates Storage Spaces Direct cluster creation, pool setup, and virtual disk provisioning
    Supports Windows Server 2016, 2019, 2022

.PARAMETER ClusterName
    Name for the S2D cluster (default: S2D-Cluster01)

.PARAMETER ClusterNodes
    Array of server names to join cluster (minimum 3 for production)

.PARAMETER PoolName
    Name for storage pool (default: S2D-Pool)

.PARAMETER VirtualDiskName
    Name for initial virtual disk (default: VD-VM-Storage)

.PARAMETER ResiliencyType
    Resiliency option: Mirror (default) or Parity

.EXAMPLE
    .\S2D-Cluster-Setup.ps1 -ClusterName "S2D-PROD" -ClusterNodes "S2D-Node1","S2D-Node2","S2D-Node3"

.NOTES
    Requirements:
    - Windows Server 2016+ on all nodes
    - Hyper-V and Failover Clustering installed
    - Storage Spaces Direct feature available
    - All nodes in same domain
    - Fast local storage (NVMe/SSD minimum)
    - 10 Gbps network strongly recommended

    Author: IT Vedas
    Date: 2026-07-04
#>

[CmdletBinding()]
param(
    [string]$ClusterName = "S2D-Cluster01",
    [string[]]$ClusterNodes = @("S2D-Node1", "S2D-Node2", "S2D-Node3"),
    [string]$ClusterIP = "",
    [string]$PoolName = "S2D-Pool",
    [string]$VirtualDiskName = "VD-VM-Storage",
    [ValidateSet("Mirror", "Parity")]
    [string]$ResiliencyType = "Mirror",
    [int64]$VirtualDiskSizeGB = 500
)

$ErrorActionPreference = "Stop"
trap {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Function to validate S2D prerequisites
function Test-S2DPrerequisites {
    param([string[]]$Nodes)

    Write-Host "Validating S2D prerequisites..." -ForegroundColor Yellow

    foreach ($node in $Nodes) {
        Write-Host "  Checking $node..." -ForegroundColor Cyan

        # Check OS version
        try {
            $osInfo = Invoke-Command -ComputerName $node -ScriptBlock {
                [System.Environment]::OSVersion.Version
            }

            if ($osInfo.Major -ge 10) {
                Write-Host "    ✓ OS version compatible (Build $($osInfo.Major).$($osInfo.Minor))" -ForegroundColor Green
            } else {
                Write-Host "    ✗ OS version too old" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "    ✗ Could not check OS version: $_" -ForegroundColor Red
            return $false
        }

        # Check storage
        try {
            $disks = Invoke-Command -ComputerName $node -ScriptBlock {
                Get-PhysicalDisk | Where-Object { $_.CanPool -eq $true } | Measure-Object
            }

            if ($disks.Count -ge 3) {
                Write-Host "    ✓ Found $($disks.Count) poolable disks" -ForegroundColor Green
            } else {
                Write-Host "    ⚠ Only $($disks.Count) poolable disks (minimum 3 recommended)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    ✗ Could not check storage: $_" -ForegroundColor Red
            return $false
        }
    }

    return $true
}

# Function to check storage media types
function Get-StorageMediaInfo {
    param([string]$ComputerName)

    try {
        $mediaInfo = Invoke-Command -ComputerName $ComputerName -ScriptBlock {
            Get-PhysicalDisk | Where-Object { $_.CanPool -eq $true } |
                Select-Object FriendlyName, MediaType, Size |
                Group-Object MediaType
        }

        return $mediaInfo
    } catch {
        Write-Host "Error getting storage info: $_" -ForegroundColor Red
        return $null
    }
}

# Main execution
Write-Host "=" * 70
Write-Host "Storage Spaces Direct (S2D) Cluster Setup Script" -ForegroundColor Cyan
Write-Host "=" * 70

# Validate prerequisites
Write-Host "`nStep 1: Validating prerequisites..." -ForegroundColor Cyan

if (-not (Test-S2DPrerequisites -Nodes $ClusterNodes)) {
    Write-Host "Prerequisites check failed" -ForegroundColor Red
    exit 1
}

# Check storage configuration
Write-Host "`nStep 2: Analyzing storage configuration..." -ForegroundColor Cyan

foreach ($node in $ClusterNodes) {
    Write-Host "  Storage on $node:" -ForegroundColor Yellow

    $mediaInfo = Get-StorageMediaInfo -ComputerName $node

    foreach ($media in $mediaInfo) {
        Write-Host "    $($media.Name): $($media.Count) drives" -ForegroundColor Green
    }
}

# Create failover cluster
Write-Host "`nStep 3: Creating Failover Cluster..." -ForegroundColor Cyan

try {
    $existingCluster = Get-Cluster -Name $ClusterName -ErrorAction SilentlyContinue

    if ($existingCluster) {
        Write-Host "✓ Cluster '$ClusterName' already exists" -ForegroundColor Green
    } else {
        Write-Host "  Creating cluster with first node..." -ForegroundColor Yellow

        if ($ClusterIP) {
            $cluster = New-Cluster -Name $ClusterName -Node $ClusterNodes[0] -StaticAddress $ClusterIP -Confirm:$false
        } else {
            $cluster = New-Cluster -Name $ClusterName -Node $ClusterNodes[0] -Confirm:$false
        }

        Write-Host "✓ Initial cluster created" -ForegroundColor Green
        Start-Sleep -Seconds 5

        # Add remaining nodes
        for ($i = 1; $i -lt $ClusterNodes.Count; $i++) {
            Write-Host "  Adding $($ClusterNodes[$i])..." -ForegroundColor Yellow
            Add-ClusterNode -Cluster $ClusterName -Name $ClusterNodes[$i] -NoStorage -Confirm:$false
            Write-Host "✓ $($ClusterNodes[$i]) added" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ Failed to create cluster: $_" -ForegroundColor Red
    exit 1
}

# Enable Storage Spaces Direct
Write-Host "`nStep 4: Enabling Storage Spaces Direct..." -ForegroundColor Cyan

try {
    Write-Host "  This may take several minutes..." -ForegroundColor Yellow

    Enable-ClusterS2D -PoolFriendlyName $PoolName -Confirm:$false -Verbose

    Write-Host "✓ Storage Spaces Direct enabled" -ForegroundColor Green
    Start-Sleep -Seconds 10
} catch {
    Write-Host "✗ Failed to enable S2D: $_" -ForegroundColor Red
    exit 1
}

# Verify storage pool
Write-Host "`nStep 5: Verifying storage pool..." -ForegroundColor Cyan

try {
    $pool = Get-StoragePool -FriendlyName $PoolName

    if ($pool) {
        Write-Host "✓ Storage pool '$PoolName' created" -ForegroundColor Green
        Write-Host "  Health Status: $($pool.HealthStatus)" -ForegroundColor Green
        Write-Host "  Total Capacity: $([math]::Round($pool.TotalSize / 1TB, 2)) TB" -ForegroundColor Green
        Write-Host "  Free Space: $([math]::Round($pool.FreeSpace / 1TB, 2)) TB" -ForegroundColor Green
    } else {
        Write-Host "✗ Storage pool not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Error verifying pool: $_" -ForegroundColor Red
}

# Create virtual disk
Write-Host "`nStep 6: Creating virtual disk..." -ForegroundColor Cyan

try {
    $existingVD = Get-VirtualDisk -FriendlyName $VirtualDiskName -ErrorAction SilentlyContinue

    if ($existingVD) {
        Write-Host "✓ Virtual disk '$VirtualDiskName' already exists" -ForegroundColor Green
    } else {
        Write-Host "  Creating $ResiliencyType virtual disk (${VirtualDiskSizeGB} GB)..." -ForegroundColor Yellow

        $vd = New-VirtualDisk -StoragePoolFriendlyName $PoolName `
            -FriendlyName $VirtualDiskName `
            -Size ($VirtualDiskSizeGB * 1GB) `
            -ResiliencySettingName $ResiliencyType `
            -Confirm:$false

        Write-Host "✓ Virtual disk created" -ForegroundColor Green
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "✗ Failed to create virtual disk: $_" -ForegroundColor Red
    exit 1
}

# Initialize and format virtual disk
Write-Host "`nStep 7: Initializing and formatting virtual disk..." -ForegroundColor Cyan

try {
    $vd = Get-VirtualDisk -FriendlyName $VirtualDiskName
    $disk = Get-Disk | Where-Object { $_.OperationalStatus -eq "Offline" } | Select-Object -First 1

    if ($disk) {
        Write-Host "  Initializing disk..." -ForegroundColor Yellow
        Initialize-Disk -Number $disk.Number -PartitionStyle GPT -Confirm:$false

        Write-Host "  Creating partition..." -ForegroundColor Yellow
        $partition = New-Partition -DiskNumber $disk.Number -UseMaximumSize -AssignDriveLetter

        Write-Host "  Formatting with ReFS..." -ForegroundColor Yellow
        Format-Volume -DriveLetter $partition.DriveLetter -FileSystem CSVFS_ReFS -NewFileSystemLabel $VirtualDiskName -Confirm:$false

        Write-Host "✓ Virtual disk formatted and ready" -ForegroundColor Green
        Write-Host "  Drive letter: $($partition.DriveLetter)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Could not find disk to format (may need manual initialization)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Error formatting disk: $_" -ForegroundColor Red
}

# Create CSV (Cluster Shared Volume)
Write-Host "`nStep 8: Creating Cluster Shared Volume..." -ForegroundColor Cyan

try {
    $csv = Add-ClusterSharedVolume -Cluster $ClusterName -InputObject (Get-ClusterResource -Cluster $ClusterName -Name "Cluster Virtual Disk*" | Select-Object -First 1)

    if ($csv) {
        Write-Host "✓ Cluster Shared Volume created" -ForegroundColor Green
        Start-Sleep -Seconds 3
    }
} catch {
    Write-Host "⚠ CSV creation may have already happened during S2D enablement" -ForegroundColor Yellow
}

# Display final configuration
Write-Host "`nStep 9: Final configuration summary..." -ForegroundColor Cyan

try {
    Write-Host "`nCluster Status:" -ForegroundColor Green
    Get-Cluster -Name $ClusterName | Select-Object Name, State | Format-Table

    Write-Host "Cluster Nodes:" -ForegroundColor Green
    Get-ClusterNode -Cluster $ClusterName | Select-Object Name, State, NodeWeight | Format-Table

    Write-Host "Storage Pool Status:" -ForegroundColor Green
    Get-StoragePool -FriendlyName $PoolName | Select-Object FriendlyName, HealthStatus, OperationalStatus | Format-Table

    Write-Host "Physical Disks:" -ForegroundColor Green
    Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size, HealthStatus | Format-Table

    Write-Host "Virtual Disks:" -ForegroundColor Green
    Get-VirtualDisk | Select-Object FriendlyName, ResiliencySettingName, Size, HealthStatus | Format-Table

    Write-Host "Cluster Shared Volumes:" -ForegroundColor Green
    Get-ClusterSharedVolume -Cluster $ClusterName | Select-Object Name, State | Format-Table

} catch {
    Write-Host "✗ Error retrieving status: $_" -ForegroundColor Red
}

Write-Host "`n" + "=" * 70
Write-Host "Storage Spaces Direct Setup Complete!" -ForegroundColor Green
Write-Host "=" * 70
Write-Host "
Next Steps:

1. Create additional virtual disks for different workloads:
   New-VirtualDisk -StoragePoolFriendlyName '$PoolName' `
     -FriendlyName 'VD-Database' -Size 1TB -ResiliencySettingName 'Mirror'

2. Configure tiered storage (if mixed media available):
   New-StorageTier -StoragePoolFriendlyName '$PoolName' `
     -FriendlyName 'Performance-Tier' -MediaType SSD

3. Create Hyper-V VMs using the CSV storage:
   New-VM -Name 'VM01' -MemoryStartupBytes 4GB `
     -Path 'C:\ClusterStorage\Volume1' -SwitchName 'ExternalSwitch'

4. Deploy Hyper-V Virtual Machine roles:
   Add-ClusterVirtualMachineRole -VirtualMachine 'VM01'

5. Setup monitoring and alerts:
   - System Center Virtual Machine Manager (SCVMM)
   - Windows Admin Center (WAC)
   - Network monitoring for 10Gbps utilization

6. Monitor cluster health continuously:
   Get-ClusterHealth -Cluster '$ClusterName'
   Test-Cluster -Cluster '$ClusterName' -Include 'Physical Disk'

7. Plan backup strategy for VMs:
   - Use VSS-aware backup solutions (VEEAM, CommVault)
   - Backup to separate storage outside S2D cluster

Important:
- Keep 20-30% storage capacity free for operations
- Monitor rebuild time after disk failures
- Plan expansion when reaching 80% capacity
- Maintain network performance (10Gbps minimum)
- Test failover scenarios monthly
" -ForegroundColor Yellow
