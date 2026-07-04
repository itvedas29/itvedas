<#
.SYNOPSIS
    Exchange Server Database Availability Group (DAG) Complete Setup Script

.DESCRIPTION
    Automates Exchange DAG creation, adds mailbox servers, creates replicated databases
    Supports Exchange 2016, 2019, and 2022

.PARAMETER DAGName
    Name for the Database Availability Group (default: DAG01)

.PARAMETER PrimaryServer
    Primary mailbox server name (default: MBX01)

.PARAMETER SecondaryServers
    Array of additional mailbox servers (default: MBX02, MBX03)

.PARAMETER WitnessServer
    Server hosting DAG witness (default: WITNESS01)

.PARAMETER DatabaseName
    Name for mailbox database (default: DB01)

.EXAMPLE
    .\Exchange-DAG-Setup.ps1 -DAGName "PROD-DAG" -PrimaryServer "MBX01" -SecondaryServers "MBX02","MBX03"

.NOTES
    Requirements:
    - Exchange Server 2016+ installed and running
    - All servers must be in same domain
    - Network connectivity on port 64327 (DAG cluster communication)
    - Run in Exchange Management Shell as Exchange Organization Administrator

    Author: IT Vedas
    Date: 2026-07-04
#>

[CmdletBinding()]
param(
    [string]$DAGName = "DAG01",
    [string]$PrimaryServer = "MBX01",
    [string[]]$SecondaryServers = @("MBX02", "MBX03"),
    [string]$WitnessServer = "WITNESS01",
    [string]$DatabaseName = "DB01",
    [ValidateSet("D", "E")]
    [string]$DriveLetterDatabase = "D",
    [ValidateSet("E", "F")]
    [string]$DriveLetterLogs = "E"
)

# Import Exchange Module
Write-Host "Loading Exchange Management Shell..." -ForegroundColor Green
Add-PSSnapin Microsoft.Exchange.Management.PowerShell.SnapIn -ErrorAction SilentlyContinue

# Error handling
$ErrorActionPreference = "Stop"
trap {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Function to test server connectivity
function Test-ServerConnectivity {
    param([string]$ServerName)

    Write-Host "Testing connectivity to $ServerName..." -ForegroundColor Yellow

    if (Test-NetConnection -ComputerName $ServerName -Port 5985 -WarningAction SilentlyContinue) {
        Write-Host "✓ $ServerName is reachable" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ Cannot reach $ServerName" -ForegroundColor Red
        return $false
    }
}

# Function to validate Exchange installation
function Test-ExchangeInstallation {
    param([string]$ServerName)

    Write-Host "Validating Exchange installation on $ServerName..." -ForegroundColor Yellow

    try {
        $server = Get-ExchangeServer -Identity $ServerName -ErrorAction Stop
        Write-Host "✓ Exchange $($server.AdminDisplayVersion) found" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Exchange not found on $ServerName" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "=" * 60
Write-Host "Exchange Server DAG Setup Script" -ForegroundColor Cyan
Write-Host "=" * 60

# Validate all servers
Write-Host "`nValidating servers..." -ForegroundColor Cyan
$allServers = @($PrimaryServer) + $SecondaryServers + @($WitnessServer)

foreach ($server in $allServers) {
    if (-not (Test-ServerConnectivity -ServerName $server)) {
        Write-Host "Cannot proceed - required server offline" -ForegroundColor Red
        exit 1
    }

    if ($server -ne $WitnessServer) {
        if (-not (Test-ExchangeInstallation -ServerName $server)) {
            Write-Host "Cannot proceed - Exchange not installed" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 1: Create DAG
Write-Host "`nStep 1: Creating Database Availability Group..." -ForegroundColor Cyan

try {
    $existingDAG = Get-DatabaseAvailabilityGroup -Identity $DAGName -ErrorAction SilentlyContinue
    if ($existingDAG) {
        Write-Host "DAG '$DAGName' already exists. Skipping creation." -ForegroundColor Yellow
    } else {
        $dag = New-DatabaseAvailabilityGroup -Name $DAGName `
            -WitnessServer $WitnessServer `
            -WitnessDirectory "C:\DAG\Witness" `
            -DatabaseAvailabilityGroupIPAddresses @() `
            -Confirm:$false

        Write-Host "✓ DAG '$DAGName' created successfully" -ForegroundColor Green
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "✗ Failed to create DAG: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Add mailbox servers to DAG
Write-Host "`nStep 2: Adding mailbox servers to DAG..." -ForegroundColor Cyan

foreach ($server in ($PrimaryServer, $SecondaryServers)) {
    try {
        $dagMember = Get-DatabaseAvailabilityGroupNetwork -Identity $DAGName -ErrorAction SilentlyContinue |
            Where-Object {$_.MailboxServers -contains $server}

        if ($dagMember) {
            Write-Host "✓ $server already in DAG" -ForegroundColor Green
        } else {
            Add-DatabaseAvailabilityGroupServer -Identity $DAGName `
                -MailboxServer $server `
                -Confirm:$false

            Write-Host "✓ $server added to DAG" -ForegroundColor Green
            Start-Sleep -Seconds 3
        }
    } catch {
        Write-Host "✗ Failed to add $server : $_" -ForegroundColor Red
    }
}

# Step 3: Create mailbox database
Write-Host "`nStep 3: Creating mailbox database..." -ForegroundColor Cyan

try {
    $existingDB = Get-MailboxDatabase -Identity $DatabaseName -ErrorAction SilentlyContinue

    if ($existingDB) {
        Write-Host "✓ Database '$DatabaseName' already exists" -ForegroundColor Green
    } else {
        New-MailboxDatabase -Name $DatabaseName `
            -Server $PrimaryServer `
            -EdbFilePath "$($DriveLetterDatabase):\Database\$DatabaseName\$DatabaseName.edb" `
            -LogFolderPath "$($DriveLetterLogs):\Database\$DatabaseName\Logs" `
            -Confirm:$false

        Write-Host "✓ Database '$DatabaseName' created" -ForegroundColor Green
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "✗ Failed to create database: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Mount database
Write-Host "`nStep 4: Mounting database..." -ForegroundColor Cyan

try {
    $db = Get-MailboxDatabase -Identity $DatabaseName
    if ($db.Mounted) {
        Write-Host "✓ Database already mounted" -ForegroundColor Green
    } else {
        Mount-Database -Identity $DatabaseName -Confirm:$false
        Write-Host "✓ Database mounted successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to mount database: $_" -ForegroundColor Red
}

# Step 5: Create database copies
Write-Host "`nStep 5: Creating database copies for HA..." -ForegroundColor Cyan

$activationPreference = 2
foreach ($server in $SecondaryServers) {
    try {
        $existingCopy = Get-MailboxDatabaseCopyStatus -Identity "$DatabaseName\$server" -ErrorAction SilentlyContinue

        if ($existingCopy) {
            Write-Host "✓ Copy already exists on $server" -ForegroundColor Green
        } else {
            Add-MailboxDatabaseCopy -Identity $DatabaseName `
                -MailboxServer $server `
                -ActivationPreference $activationPreference `
                -ReplayLagTime 0:00:00 `
                -TruncationLagTime 0:00:00 `
                -Confirm:$false

            Write-Host "✓ Database copy added to $server (Preference: $activationPreference)" -ForegroundColor Green
            $activationPreference++
            Start-Sleep -Seconds 3
        }
    } catch {
        Write-Host "✗ Failed to add copy on $server : $_" -ForegroundColor Red
    }
}

# Step 6: Verify setup
Write-Host "`nStep 6: Verifying DAG configuration..." -ForegroundColor Cyan

try {
    $dagStatus = Get-DatabaseAvailabilityGroup -Identity $DAGName | Select-Object Name,Servers,WitnessServer
    Write-Host "`nDAG Status:" -ForegroundColor Green
    $dagStatus | Format-Table

    $dbStatus = Get-MailboxDatabaseCopyStatus -Identity "$DatabaseName*" |
        Select-Object Identity,Status,CopyQueueLength,ReplayQueueLength
    Write-Host "`nDatabase Copy Status:" -ForegroundColor Green
    $dbStatus | Format-Table

    Write-Host "`nDAG Health Check:" -ForegroundColor Green
    Test-ReplicationHealth | Format-Table

} catch {
    Write-Host "✗ Failed to retrieve status: $_" -ForegroundColor Red
}

Write-Host "`n" + "=" * 60
Write-Host "DAG Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "
Next Steps:
1. Wait 30-60 minutes for initial replication to complete
2. Monitor replication with: Get-MailboxDatabaseCopyStatus
3. Monitor DAG health with: Test-ReplicationHealth
4. Create mailboxes: New-Mailbox -Database $DatabaseName
5. Set retention policies and backups

For production validation:
- Run: Test-ServiceHealth
- Run: Test-OutlookConnectivity
- Monitor Exchange logs for errors
" -ForegroundColor Yellow
