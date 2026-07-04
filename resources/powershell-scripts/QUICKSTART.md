# Quick Start Guide - IT Vedas PowerShell Script Library

Get started with IT Vedas scripts in 5 minutes.

## 1. Install & Load (2 minutes)

```powershell
# Navigate to script directory
cd C:\Scripts\ITVedas

# Load all modules
. .\Import-AllModules.ps1

# Verify loading
Get-ITVedasModuleInfo -InformationType Summary
```

## 2. View Available Functions (1 minute)

```powershell
# List all functions
Get-ITVedasModuleInfo -InformationType Functions

# View by module
Get-Command -Module ActiveDirectory | Format-Table Name, Verb, Noun
```

## 3. Get Help (1 minute)

```powershell
# Full help for a function
Get-Help New-ADUserBulkImport -Full

# Quick help
New-ADUserBulkImport -?

# Examples
Get-Help New-ADUserBulkImport -Examples
```

## 4. Run Your First Script (1 minute)

### Option A: Active Directory - Create a User

```powershell
# Create single user
New-ADUser -Name "John Smith" -SamAccountName "jsmith" `
    -UserPrincipalName "jsmith@contoso.com" -GivenName "John" `
    -Surname "Smith" -Enabled $true -Path "OU=Users,DC=contoso,DC=com"
```

### Option B: DHCP - Monitor Scope

```powershell
# Monitor DHCP leases
Monitor-DHCPLeases -DHCPServer "dhcp1.contoso.com"
```

### Option C: Active Directory - Audit Permissions

```powershell
# Audit user's group memberships
Get-ADUserPermissionAudit -Username "jsmith"
```

### Option D: File Server - Audit Permissions

```powershell
# Audit file server
Get-FileServerAudit -ServerPath "\\fileserver\Finance"
```

### Option E: Server Health - Generate Report

```powershell
# Get server health report
$health = Get-ServerHealthReport -ComputerName "Server1"
$health
```

## Common Tasks

### Create Multiple AD Users from CSV

```powershell
# 1. Create CSV file at C:\Data\users.csv with columns:
#    FirstName, LastName, Username, Email, Department, Title

# 2. Run bulk import
$result = New-ADUserBulkImport `
    -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Staff,DC=contoso,DC=com" `
    -DefaultPassword (ConvertTo-SecureString "TempPass@123" -AsPlainText -Force)

# 3. Check results
$result.Users | Format-Table
```

### Create Security Groups

```powershell
# Create group structure for Finance department
New-ADSecurityGroupStructure `
    -OrganizationName "Finance" `
    -ParentOU "OU=Groups,DC=contoso,DC=com" `
    -TemplateType Enterprise
```

### Create DHCP Scope

```powershell
# Create scope for building
New-DHCPScopeWithSettings `
    -ScopeName "Building-A" `
    -StartRange "192.168.10.100" `
    -EndRange "192.168.10.200" `
    -SubnetMask "255.255.255.0" `
    -DefaultGateway "192.168.10.1" `
    -DNSServers @("8.8.8.8", "8.8.4.4")
```

### Create DNS Zone

```powershell
# Create zone with standard records
New-DNSZoneWithRecords `
    -ZoneName "contoso.com" `
    -CreateStandardRecords
```

### Set File Permissions

```powershell
# Give group permissions to share
Set-NTFSPermissions `
    -Path "D:\Shares\Finance" `
    -Identity "CONTOSO\Finance-Team" `
    -FileSystemRights "Modify" `
    -Recursive
```

### Audit File Server

```powershell
# Audit file server and generate report
Get-FileServerAudit `
    -ServerPath "\\fileserver\Archive" `
    -OutputFormat CSV `
    -OutputPath "C:\Reports\audit.csv"
```

### Schedule Backups

```powershell
# Schedule daily backup
New-AutomatedBackup `
    -BackupName "FileServer-Daily" `
    -SourcePath "D:\Shares" `
    -DestinationPath "E:\Backups" `
    -ScheduleType Daily `
    -RetentionDays 30
```

### Unlock Locked Account

```powershell
# Unlock user account
Resolve-ADAccountLockout -Username "jsmith"

# Unlock and reset password
Resolve-ADAccountLockout -Username "jsmith" -ResetPassword
```

### Apply Security Hardening

```powershell
# Apply security hardening
Invoke-WindowsSecurityHardening `
    -Level Standard `
    -ApplyUpdates `
    -ConfigureFirewall `
    -EnableAudit
```

### Install Server Roles

```powershell
# Install AD, DNS, DHCP roles
Install-ServerRoles `
    -Roles @('AD-Domain-Services', 'DNS', 'DHCP') `
    -IncludeManagementTools
```

## Tips & Tricks

### Enable Verbose Output
```powershell
$VerbosePreference = "Continue"
# Run your function
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass
$VerbosePreference = "SilentlyContinue"  # Reset
```

### Pipe Results to Export
```powershell
# Export results to CSV
Get-ADUserPermissionAudit -DepartmentFilter "Finance" | Export-Csv "C:\Reports\finance.csv" -NoTypeInformation

# Export to HTML
Get-ServerHealthReport -ComputerName "Server1" -OutputFormat HTML | Out-File "C:\Reports\health.html"
```

### Chain Multiple Commands
```powershell
# Get all users in group and audit them
Get-ADGroupMember -Identity "Finance-Team" | ForEach-Object {
    Get-ADUserPermissionAudit -Username $_.SamAccountName
}
```

### Save Results to Variable
```powershell
# Save for later use
$result = New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass

# Access results
$result.SuccessCount
$result.Users | Format-Table
Get-Content $result.LogPath
```

### Create Custom Function Combinations
```powershell
# Combine operations
function New-EmployeeSetup {
    param ($FirstName, $LastName, $Department)
    
    # Create user
    $user = New-ADUser -Name "$FirstName $LastName" -SamAccountName $($FirstName.Substring(0,1) + $LastName).ToLower() -GivenName $FirstName -Surname $LastName -Enabled $true
    
    # Add to group
    Add-ADGroupMember -Identity "GRP_$Department-Users" -Members $user
    
    # Log result
    Write-Host "User created: $user"
}

# Use custom function
New-EmployeeSetup -FirstName "John" -LastName "Doe" -Department "Finance"
```

## Output Formats

Most functions support multiple output formats:

```powershell
# Table format (default)
Get-FileServerAudit -ServerPath "\\fileserver" -OutputFormat Table

# CSV format
Get-FileServerAudit -ServerPath "\\fileserver" -OutputFormat CSV | Out-File "report.csv"

# JSON format
Get-ServerHealthReport -OutputFormat JSON | Out-File "report.json"

# HTML format
Get-ServerHealthReport -OutputFormat HTML | Out-File "report.html"
```

## Error Handling

All functions include error handling. Here's how to handle errors:

```powershell
# Catch and display errors
try {
    New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass
}
catch {
    Write-Error "Operation failed: $_"
    # Handle error
}

# Using error action
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass -ErrorAction Stop
```

## Next Steps

1. **Explore Examples**: Check `examples/` folder for detailed scenarios
2. **Read Full Documentation**: See `README.md` for comprehensive guide
3. **Troubleshooting**: Check `TROUBLESHOOTING.md` if issues arise
4. **Custom Setup**: Modify templates in `config/` for your environment

## Keyboard Shortcuts

```powershell
# Clear screen
Clear-Host  # or cls

# Get command history
Get-History

# Run previous command
Invoke-History -Id <number>

# Tab completion
# Type partial name and press Tab

# Show all commands
Get-Command -Module *
```

## Getting More Help

```powershell
# Help for all functions
Get-Command | Get-Help | Out-Host

# Search for functions
Get-Command -Name "*DHCP*" | Format-Table

# Browse examples
Get-Help New-ADUserBulkImport -Examples | More
```

---

**Remember**: Always test in a lab environment first before running in production!

**Last Updated**: 2026-07-04
