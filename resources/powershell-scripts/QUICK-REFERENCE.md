# IT Vedas PowerShell - Quick Reference Cheat Sheet

Essential commands and syntax for rapid script development.

## Load Modules

```powershell
# Load all modules
. C:\Scripts\ITVedas\Import-AllModules.ps1

# View available functions
Get-ITVedasModuleInfo -InformationType Functions

# Get help on function
Get-Help New-ADUserBulkImport -Full
```

## Active Directory Functions

### Create Users

```powershell
# Single user
New-ADUser -Name "John Doe" -SamAccountName "jdoe" `
    -UserPrincipalName "jdoe@contoso.com" -Path "OU=Users,DC=contoso,DC=com" -Enabled $true

# Bulk import from CSV
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Users,DC=contoso,DC=com" `
    -DefaultPassword (ConvertTo-SecureString "Pass@123" -AsPlainText -Force)
```

### Manage Groups

```powershell
# Create security group structure
New-ADSecurityGroupStructure -OrganizationName "Finance" `
    -ParentOU "OU=Groups,DC=contoso,DC=com" -TemplateType Enterprise

# Add member to group
Add-ADGroupMember -Identity "GRP_Finance-Staff" -Members "jdoe"

# Remove member from group
Remove-ADGroupMember -Identity "GRP_Finance-Staff" -Members "jdoe"
```

### Account Management

```powershell
# Unlock account
Resolve-ADAccountLockout -Username "jdoe"

# Unlock and reset password
Resolve-ADAccountLockout -Username "jdoe" -ResetPassword

# Disable account
Disable-ADAccount -Identity "jdoe"

# Enable account
Enable-ADAccount -Identity "jdoe"
```

### Query Users

```powersharp
# Find user
Get-ADUser -Identity "jdoe"

# Find all users in department
Get-ADUser -Filter { Department -eq "Finance" }

# Audit user permissions
Get-ADUserPermissionAudit -Username "jdoe"
```

## DNS Functions

### Create Zones

```powershell
# Create zone with standard records
New-DNSZoneWithRecords -ZoneName "contoso.com" -CreateStandardRecords

# Create zone from CSV records
New-DNSZoneWithRecords -ZoneName "contoso.com" `
    -RecordsCSV "C:\Data\dns-records.csv"
```

### Validate Replication

```powershell
# Check replication
Validate-DNSReplication -ZoneName "contoso.com" `
    -DNSServers @("dns1.contoso.com", "dns2.contoso.com") `
    -SerialNumberCheck -RecordCountCheck
```

## DHCP Functions

### Create Scopes

```powershell
# Create scope
New-DHCPScopeWithSettings -ScopeName "Building-A" `
    -StartRange "192.168.10.100" -EndRange "192.168.10.200" `
    -SubnetMask "255.255.255.0" -DefaultGateway "192.168.10.1" `
    -DNSServers @("8.8.8.8", "8.8.4.4")
```

### Monitor Leases

```powershell
# Monitor DHCP
Monitor-DHCPLeases -DHCPServer "dhcp1.contoso.com"

# Monitor specific scope
Monitor-DHCPLeases -ScopeFilter "Building-A"

# Export report
Monitor-DHCPLeases -OutputFormat CSV | Out-File "report.csv"
```

## File Server Functions

### Set Permissions

```powershell
# Set NTFS permissions
Set-NTFSPermissions -Path "D:\Shares\Finance" `
    -Identity "CONTOSO\Finance-Team" `
    -FileSystemRights "Modify" -Recursive

# Read-only access
Set-NTFSPermissions -Path "D:\Shares\Reports" `
    -Identity "CONTOSO\All-Users" `
    -FileSystemRights "Read"
```

### Audit Server

```powershell
# Audit file server
Get-FileServerAudit -ServerPath "\\fileserver\Finance"

# Audit with large files report
Get-FileServerAudit -ServerPath "\\fileserver" `
    -ReportLargeFiles 500 -OutputFormat HTML

# Export audit
Get-FileServerAudit -ServerPath "\\fileserver" `
    -OutputFormat CSV | Out-File "audit.csv"
```

## Backup Functions

### Schedule Backups

```powershell
# Create automated backup
New-AutomatedBackup -BackupName "FileServer-Daily" `
    -SourcePath "D:\Shares" `
    -DestinationPath "E:\Backups" `
    -ScheduleType Daily -RetentionDays 30

# With compression
New-AutomatedBackup -BackupName "Archive" `
    -SourcePath "D:\Archive" `
    -DestinationPath "E:\Backups" `
    -CompressionEnabled
```

## Security Functions

### Harden System

```powershell
# Apply security hardening
Invoke-WindowsSecurityHardening -Level Standard `
    -ApplyUpdates -ConfigureFirewall -EnableAudit

# Strict hardening
Invoke-WindowsSecurityHardening -Level Strict `
    -ApplyUpdates -ConfigureFirewall -EnableAudit -DisableUnnecessaryServices
```

## Performance Monitoring

### Generate Reports

```powershell
# Server health report
Get-ServerHealthReport -ComputerName "Server1"

# With event logs
Get-ServerHealthReport -ComputerName "Server1" `
    -IncludeEventLogs -IncludeServices

# Export to HTML
Get-ServerHealthReport -ComputerName "Server1" `
    -OutputFormat HTML | Out-File "health.html"
```

## Server Deployment

### Install Roles

```powershell
# Install roles
Install-ServerRoles -Roles @('AD-Domain-Services', 'DNS', 'DHCP') `
    -IncludeManagementTools -ValidateInstallation

# Single role
Install-ServerRoles -Roles @('DHCP') `
    -ValidateInstallation
```

## Common Patterns

### Error Handling

```powershell
try {
    New-ADUserBulkImport -CSVPath "C:\Data\users.csv" `
        -TargetOU "OU=Users,DC=contoso,DC=com" `
        -DefaultPassword $pass
}
catch {
    Write-Error "Operation failed: $_"
}
```

### Enable Verbose Output

```powershell
$VerbosePreference = "Continue"
# Run function
$VerbosePreference = "SilentlyContinue"  # Reset
```

### Pipeline Operations

```powershell
# Get all enabled users in Finance
Get-ADUser -Filter { Department -eq "Finance" -and Enabled -eq $true } | `
    ForEach-Object { Get-ADUserPermissionAudit -Username $_.SamAccountName }

# Export multiple audits
Get-ADUser -Filter * | ForEach-Object {
    Get-ADUserPermissionAudit -Username $_.SamAccountName
} | Export-Csv "users_audit.csv" -NoTypeInformation
```

### Save Results

```powershell
# Save to variable
$result = New-ADUserBulkImport -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass

# Access results
$result.SuccessCount
$result.Users | Format-Table
$result.LogPath
```

### Batch Operations

```powershell
# Process in batches
$users = Import-Csv "C:\Data\users.csv"
$batch = @()
$batchSize = 50

foreach ($user in $users) {
    $batch += $user
    if ($batch.Count -eq $batchSize) {
        # Process batch
        $batch = @()
    }
}
```

## Parameter Shortcuts

```powershell
# Use -? for quick help
New-ADUserBulkImport -?

# Use shorthand for common parameters
# -ErrorAction = -EA
# -WarningAction = -WA
# -Verbose = -V
# -Force = -F

New-ADUserBulkImport -CSVPath $path -TargetOU $ou -DefaultPassword $pass -V
```

## Output Formatting

```powershell
# Format as table
$result | Format-Table

# Format as list
$result | Format-List

# Format as wide
$result | Format-Wide

# Custom formatting
$result | Select-Object -Property Name, Email, Department | Format-Table

# Sort results
$result | Sort-Object -Property Department, Name | Format-Table

# Filter results
$result | Where-Object { $_.Status -eq "OK" }
```

## Convert Data

```powershell
# Import CSV
$data = Import-Csv "C:\Data\file.csv"

# Export to CSV
$data | Export-Csv "C:\Reports\file.csv" -NoTypeInformation

# Convert to JSON
$data | ConvertTo-Json

# Convert from JSON
$json = Get-Content "file.json" | ConvertFrom-Json
```

## File Operations

```powershell
# Test if path exists
Test-Path "C:\Path"

# Get file/folder
Get-Item "C:\Path"
Get-ChildItem "C:\Path"

# Create directory
New-Item -Path "C:\Path" -ItemType Directory -Force

# Copy files
Copy-Item -Path "C:\Source" -Destination "C:\Dest" -Recurse

# Remove files
Remove-Item -Path "C:\Path" -Force -Recurse
```

## Time Operations

```powershell
# Current date/time
Get-Date

# Format date
Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Date arithmetic
(Get-Date).AddDays(-30)
(Get-Date).AddHours(-24)
(Get-Date).AddMonths(-1)

# Time span
New-TimeSpan -Days 8
New-TimeSpan -Hours 24
```

## Variable Usage

```powershell
# Define variable
$variable = "value"

# String interpolation
Write-Host "Value is $variable"

# Array
$array = @("item1", "item2", "item3")
$array[0]  # First item
$array.Count  # Count items

# Hash table
$hash = @{Key1 = "Value1"; Key2 = "Value2"}
$hash['Key1']

# Secure string for passwords
$password = ConvertTo-SecureString "Pass@123" -AsPlainText -Force
```

## Quick Commands

```powershell
# Clear screen
Clear-Host

# Get current directory
Get-Location

# Change directory
cd C:\Scripts

# Get module info
Get-ITVedasModuleInfo

# List all commands
Get-Command

# Search commands
Get-Command -Name "*DHCP*"
```

## Common Parameters

| Parameter | Shorthand | Purpose |
|-----------|-----------|---------|
| -ErrorAction | -EA | How to handle errors (Stop, Continue, SilentlyContinue) |
| -Verbose | -V | Display detailed output |
| -Force | -F | Skip confirmation prompts |
| -WhatIf | -W | Show what would happen (read-only preview) |
| -Confirm | -C | Prompt before executing |
| -OutVariable | -OV | Save output to variable |
| -OutBuffer | -OB | Buffer output |

## Function Syntax

```powershell
# Mandatory parameter
-ParameterName "value"

# Optional parameter
-ParameterName "value"

# Switch parameter
-EnableFeature

# Array parameter
-List @("item1", "item2")

# Hashtable parameter
-Options @{Key = "Value"}
```

## Tips & Best Practices

1. **Always test in lab first** before production
2. **Use verbose logging** for debugging
3. **Save results to variables** for further processing
4. **Include error handling** in scripts
5. **Document your parameters** with help text
6. **Use SecureString** for passwords
7. **Backup before major changes** to AD/DNS/DHCP
8. **Monitor operations** with comprehensive logging
9. **Validate inputs** with ValidateScript
10. **Use pipeline** for chaining operations

---

**Last Updated**: 2026-07-04
**Version**: 1.0
