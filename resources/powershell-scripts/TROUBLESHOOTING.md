# Troubleshooting Guide - IT Vedas PowerShell Script Library

Common issues and solutions for the IT Vedas PowerShell Script Library.

## Installation Issues

### Issue: "The system cannot find the path"

**Symptoms**: Error when accessing scripts directory

**Cause**: Scripts not in expected location or path is incorrect

**Solution**:
```powershell
# Find actual location
Get-ChildItem -Path "C:\" -Filter "powershell-scripts" -Recurse -Directory

# Navigate to correct location
cd "C:\Your\Actual\Path\powershell-scripts"

# Verify structure
Get-ChildItem -Path ".\modules"
```

---

### Issue: "The file cannot be loaded because running scripts is disabled"

**Symptoms**: Script execution fails with security error

**Cause**: PowerShell execution policy is too restrictive

**Solution**:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to RemoteSigned (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Or for all users (requires admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

# Bypass for current session only
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Verify
Get-ExecutionPolicy
```

---

### Issue: "Access denied" creating directories

**Symptoms**: Cannot create C:\Logs or C:\Data directories

**Cause**: Insufficient permissions

**Solution**:
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell > "Run as Administrator"

# Or check current permissions
Get-Acl -Path "C:\" | Format-List

# Create directory with admin rights
New-Item -Path "C:\Logs\ITVedas" -ItemType Directory -Force
```

---

## Module Loading Issues

### Issue: "The term 'New-ADUserBulkImport' is not recognized"

**Symptoms**: Function not found after loading modules

**Cause**: Modules not properly loaded or have errors

**Solution**:
```powershell
# Verify module loading completed
Get-ITVedasModuleInfo -InformationType Summary

# Check for failed modules
Get-ITVedasModuleInfo -InformationType Failed

# Reload modules
Remove-Module * -ErrorAction SilentlyContinue
. "C:\Scripts\ITVedas\Import-AllModules.ps1" -ListFunctions

# Validate module syntax
. "C:\Scripts\ITVedas\Import-AllModules.ps1" -ValidateOnly
```

---

### Issue: "Active Directory module not found"

**Symptoms**: AD functions not available

**Cause**: RSAT tools not installed

**Solution**:
```powershell
# Check if module is available
Get-Module -Name ActiveDirectory -ListAvailable

# Install RSAT tools (requires admin)
Add-WindowsFeature RSAT-AD-PowerShell

# Restart PowerShell after installation
# Exit PowerShell and open new window

# Verify installation
Import-Module ActiveDirectory
Get-Command -Module ActiveDirectory | Measure-Object
```

---

### Issue: "Cannot load module - syntax error on line X"

**Symptoms**: Specific script file has errors

**Cause**: Corrupted file or syntax error

**Solution**:
```powershell
# Check for file corruption
Test-Path "C:\Scripts\ITVedas\modules\ActiveDirectory\New-ADUserBulkImport.ps1"

# Validate syntax
$tokens = @()
$errors = @()
$null = [System.Management.Automation.PSParser]::Tokenize(
    (Get-Content "C:\Scripts\ITVedas\modules\ActiveDirectory\New-ADUserBulkImport.ps1"), 
    [ref]$errors
)

if ($errors) {
    Write-Error "Syntax errors found:"
    $errors | Format-Table -AutoSize
}

# Reinstall modules if needed
# Delete and re-extract/copy scripts
```

---

## Active Directory Issues

### Issue: "The specified account already exists"

**Symptoms**: User creation fails with duplicate account error

**Cause**: User already exists in Active Directory

**Solution**:
```powershell
# Check if user exists
Get-ADUser -Filter { SamAccountName -eq "jsmith" } -ErrorAction SilentlyContinue

# If user exists, use different username
# Or delete existing user (carefully!)
# Remove-ADUser -Identity "jsmith" -Confirm:$false

# Verify all users from CSV exist
$users = Import-Csv "C:\Data\users.csv"
foreach ($user in $users) {
    $exists = Get-ADUser -Filter { SamAccountName -eq $user.Username } -ErrorAction SilentlyContinue
    if ($exists) {
        Write-Warning "User already exists: $($user.Username)"
    }
}
```

---

### Issue: "The target organizational unit does not exist"

**Symptoms**: OU validation fails

**Cause**: Incorrect OU distinguished name

**Solution**:
```powershell
# Find correct OU
Get-ADOrganizationalUnit -Filter * | Select-Object DistinguishedName | Format-Table

# Find specific OU
Get-ADOrganizationalUnit -Filter { Name -like "*Staff*" }

# Build correct DN
# Example: OU=Staff,OU=Users,DC=contoso,DC=com

# Verify OU
Get-ADOrganizationalUnit -Identity "OU=Staff,DC=contoso,DC=com"
```

---

### Issue: "User cannot be unlocked - account not locked"

**Symptoms**: Unlock operation shows account not locked

**Cause**: Account is not actually locked out

**Solution**:
```powershell
# Check account status
Get-ADUser -Identity "jsmith" -Properties LockedOut, AccountLockoutTime | Format-Table

# If not locked, message is informational
# Account lockout is temporary and may auto-unlock

# View lockout policy
Get-ADDefaultDomainPasswordPolicy | Select-Object LockoutDuration, LockoutThreshold
```

---

### Issue: "Permission denied accessing AD"

**Symptoms**: AD operations fail with access errors

**Cause**: Insufficient permissions

**Solution**:
```powershell
# Check current user permissions
$principal = [System.Security.Principal.WindowsIdentity]::GetCurrent()
Write-Output $principal.Name

# Verify admin status
([Security.Principal.WindowsPrincipal] $principal).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

# Run as domain admin or delegated account
# Right-click PowerShell > "Run as Administrator"
# Or use Run As:
# runas /user:CONTOSO\admin powershell
```

---

## DNS Issues

### Issue: "Cannot connect to DNS server"

**Symptoms**: DNS functions timeout

**Cause**: DNS server not accessible

**Solution**:
```powershell
# Test connectivity
Test-NetConnection -ComputerName "dns1.contoso.com" -Port 53

# Verify DNS service running
Get-Service -ComputerName "dns1.contoso.com" -Name DNS | Format-Table

# Start DNS service
Start-Service -Name DNS -ComputerName "dns1.contoso.com"

# Verify DNS is responding
Resolve-DnsName "contoso.com" -Server "dns1.contoso.com"
```

---

### Issue: "Zone already exists"

**Symptoms**: Zone creation fails

**Cause**: Zone already created

**Solution**:
```powershell
# List existing zones
Get-DnsServerZone -ComputerName "dns1.contoso.com" | Format-Table Name

# Delete existing zone (carefully!)
Remove-DnsServerZone -Name "contoso.com" -ComputerName "dns1.contoso.com" -Force

# Use different zone name
New-DNSZoneWithRecords -ZoneName "subdomain.contoso.com"
```

---

### Issue: "DNS replication shows inconsistencies"

**Symptoms**: Serial numbers or record counts differ

**Cause**: Zone not fully replicated

**Solution**:
```powershell
# Force replication
Start-DnsServerZoneTransfer -ZoneName "contoso.com" -ComputerName "dns1.contoso.com"

# Wait for replication
Start-Sleep -Seconds 30

# Re-validate
Validate-DNSReplication -ZoneName "contoso.com" `
    -DNSServers @("dns1.contoso.com", "dns2.contoso.com") `
    -SerialNumberCheck -RecordCountCheck

# Check replication status
repadmin /showrepl /errorsonly
```

---

## DHCP Issues

### Issue: "DHCP server is not operational"

**Symptoms**: DHCP functions fail to connect

**Cause**: DHCP service not running

**Solution**:
```powershell
# Check service status
Get-Service -Name DHCPServer | Format-Table

# Start DHCP service
Start-Service -Name DHCPServer

# Enable auto-start
Set-Service -Name DHCPServer -StartupType Automatic

# Verify status
Get-Service -Name DHCPServer
```

---

### Issue: "The scope already exists"

**Symptoms**: Scope creation fails with existing scope error

**Cause**: Scope already created

**Solution**:
```powershell
# List existing scopes
Get-DhcpServerv4Scope | Format-Table ScopeId, Name

# Delete existing scope (carefully!)
Remove-DhcpServerv4Scope -ScopeId "192.168.1.0" -Force

# Use different IP range
New-DHCPScopeWithSettings `
    -ScopeName "Building-B" `
    -StartRange "192.168.20.100" `
    -EndRange "192.168.20.200"
```

---

### Issue: "No leases detected in DHCP scope"

**Symptoms**: Monitoring shows zero leases

**Cause**: Clients not connected or scope disabled

**Solution**:
```powershell
# Check scope state
Get-DhcpServerv4Scope -ScopeId "192.168.1.0" | Select-Object State

# Enable scope
Set-DhcpServerv4Scope -ScopeId "192.168.1.0" -State Active

# Wait for clients to connect
Start-Sleep -Seconds 60

# Re-monitor
Monitor-DHCPLeases
```

---

## File Server Issues

### Issue: "Path does not exist"

**Symptoms**: File server functions fail to access path

**Cause**: Share path incorrect or unavailable

**Solution**:
```powershell
# Verify path
Test-Path -Path "\\fileserver\Finance"

# List available shares
Get-SMBShare -Name "*Finance*"

# Map drive temporarily
New-PSDrive -Name "Z" -PSProvider FileSystem -Root "\\fileserver\Finance"

# Check permissions
Get-Acl -Path "\\fileserver\Finance" | Format-List
```

---

### Issue: "Access denied on file operations"

**Symptoms**: Permission errors accessing files

**Cause**: Insufficient permissions

**Solution**:
```powershell
# Check current user
[System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Check file permissions
Get-Acl -Path "D:\Shares\Finance" | Format-List

# Run as different user
$cred = Get-Credential
Invoke-Command -ComputerName "fileserver" -ScriptBlock {
    Set-NTFSPermissions -Path "D:\Shares" -Identity "CONTOSO\Group" -FileSystemRights "Modify"
} -Credential $cred
```

---

### Issue: "Cannot set permissions - invalid identity"

**Symptoms**: NTFS permission fails with invalid user/group

**Cause**: User or group doesn't exist

**Solution**:
```powershell
# Verify identity exists
Get-ADUser -Identity "jsmith" -ErrorAction SilentlyContinue
Get-ADGroup -Identity "Finance-Team" -ErrorAction SilentlyContinue

# Create group if missing
New-ADGroup -Name "Finance-Team" -GroupScope Global `
    -Path "OU=Groups,DC=contoso,DC=com"

# Use full domain name
Set-NTFSPermissions `
    -Path "D:\Shares\Finance" `
    -Identity "CONTOSO\Finance-Team" `
    -FileSystemRights "Modify"
```

---

## Backup Issues

### Issue: "Backup destination full"

**Symptoms**: Backup job fails with disk space error

**Cause**: Insufficient space at destination

**Solution**:
```powershell
# Check disk space
Get-Volume -DriveLetter E | Select-Object SizeRemaining

# Reduce retention
New-AutomatedBackup `
    -BackupName "FileServer-Daily" `
    -SourcePath "D:\Shares" `
    -DestinationPath "E:\Backups" `
    -RetentionDays 14  # Reduced from 30

# Add additional disk space
# Or use different destination
```

---

### Issue: "Backup scheduled task not executing"

**Symptoms**: Scheduled backup never runs

**Cause**: Task disabled or wrong credentials

**Solution**:
```powershell
# Check task status
Get-ScheduledTask -TaskName "Backup_*" | Format-Table

# Enable task if disabled
Enable-ScheduledTask -TaskName "Backup_FileServer-Daily"

# Run task manually to test
Start-ScheduledTask -TaskName "Backup_FileServer-Daily"

# Check task results
Get-ScheduledTaskInfo -TaskName "Backup_FileServer-Daily"

# View logs
Get-ScheduledTask -TaskName "Backup_FileServer-Daily" | Get-ScheduledTaskInfo
```

---

## Performance & Monitoring Issues

### Issue: "Server health report shows high CPU usage"

**Symptoms**: CPU usage above threshold

**Cause**: Legitimate high load or runaway process

**Solution**:
```powershell
# Get detailed CPU info
Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 | Format-Table

# Get performance metrics
Get-WmiObject -Class Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" `
    | Select-Object PercentProcessorTime, PercentUserTime, PercentPrivilegedTime

# Investigate specific process
Get-Process -Name "ProcessName" | Format-List

# Kill problematic process if needed
Stop-Process -Name "ProcessName" -Force
```

---

### Issue: "Memory usage shows as 0 or incorrect"

**Symptoms**: Memory metrics inaccurate

**Cause**: WMI query issue

**Solution**:
```powershell
# Refresh WMI data
Get-WmiObject -List | Where-Object { $_.Name -like "*Memory*" }

# Get memory info alternative way
[System.GC]::GetTotalMemory($true)

# Check WMI service
Get-Service -Name WinRmRemoteWMIUser | Format-Table

# Restart WMI service
Restart-Service -Name WinRM -Force
```

---

## Security Hardening Issues

### Issue: "Cannot apply group policy"

**Symptoms**: Security settings not applied

**Cause**: Group policy not processing

**Solution**:
```powershell
# Force group policy update
gpupdate /force

# Check group policy results
gpresult /h report.html

# Verify policies applied
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\*"

# Apply settings manually if needed
Invoke-WindowsSecurityHardening -Level Standard -ApplyUpdates
```

---

### Issue: "Firewall blocking legitimate traffic"

**Symptoms**: Applications fail after firewall hardening

**Cause**: Too restrictive firewall rules

**Solution**:
```powershell
# Review firewall rules
Get-NetFirewallRule | Format-Table Name, Direction, Action

# Disable rule temporarily to test
Disable-NetFirewallRule -DisplayName "Rule Name"

# Add exception for specific port
New-NetFirewallRule -DisplayName "Allow RDP" -Direction Inbound `
    -Protocol TCP -LocalPort 3389 -Action Allow

# Check inbound default action
Get-NetFirewallProfile | Select-Object DefaultInboundAction
```

---

## General Troubleshooting Steps

### 1. Enable Verbose Logging
```powershell
$VerbosePreference = "Continue"
# Run your function
$VerbosePreference = "SilentlyContinue"  # Reset
```

### 2. Test with Simplified Parameters
```powershell
# Instead of complex parameters
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Users,DC=contoso,DC=com" -DefaultPassword $pass

# Test individual operations first
Get-ADOrganizationalUnit -Identity "OU=Users,DC=contoso,DC=com"
Import-Csv "C:\Data\users.csv" | Select-Object -First 1
```

### 3. Check Event Logs
```powershell
# Get relevant errors
Get-EventLog -LogName System -EntryType Error -Newest 20 | Format-Table TimeGenerated, Source, Message

# Get specific service errors
Get-EventLog -LogName "Directory Service" -EntryType Error -Newest 10

# Export to file
Get-EventLog -LogName System -Newest 100 | Export-Csv "C:\Logs\system_errors.csv" -NoTypeInformation
```

### 4. Test Connectivity
```powershell
# Test computer connectivity
Test-Connection -ComputerName "Server1"

# Test service ports
Test-NetConnection -ComputerName "Server1" -Port 389  # LDAP
Test-NetConnection -ComputerName "dns1" -Port 53      # DNS
Test-NetConnection -ComputerName "dhcp1" -Port 67     # DHCP
```

### 5. Verify Prerequisites
```powershell
# Check Windows version
[System.Environment]::OSVersion.VersionString

# Check PowerShell version
$PSVersionTable.PSVersion

# Check required features installed
Get-WindowsFeature -Name "RSAT-*" | Where-Object { $_.Installed } | Format-Table
```

### 6. Clear and Reload
```powershell
# Clear module cache
Remove-Module -Name * -ErrorAction SilentlyContinue

# Clear command cache
[System.Management.Automation.CommandDiscovery]::ClearCache()

# Reload modules
. "C:\Scripts\ITVedas\Import-AllModules.ps1"
```

## Getting Help

- **Get-Help**: `Get-Help Function-Name -Full`
- **Examples**: `Get-Help Function-Name -Examples`
- **Online**: `Get-Help Function-Name -Online`
- **See Also**: Check function comments for related functions

## Still Having Issues?

1. Check system event logs
2. Enable verbose logging
3. Verify all prerequisites are installed
4. Review function documentation
5. Test individual components separately
6. Check for typos in parameters
7. Verify credentials and permissions

---

**Last Updated**: 2026-07-04
**Version**: 1.0
