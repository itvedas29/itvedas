# IT Vedas PowerShell Script Library

A comprehensive, production-ready PowerShell module collection for Windows Server management across 8 key areas. This library provides enterprise-grade scripts with error handling, logging, and comprehensive documentation.

## Overview

The IT Vedas PowerShell Script Library consists of 8 specialized modules with 20+ professionally developed functions covering essential server management tasks.

### Module Structure

```
powershell-scripts/
├── modules/
│   ├── ActiveDirectory/         # AD user & group management
│   ├── DNS/                     # DNS zone & record management
│   ├── DHCP/                    # DHCP scope & lease management
│   ├── FileServer/              # File share & permission management
│   ├── BackupRecovery/          # Automated backup solutions
│   ├── SecurityHardening/       # Security configuration
│   ├── PerformanceMonitoring/   # Health & performance reports
│   └── ServerDeployment/        # Role installation & configuration
├── templates/                    # Configuration templates
├── guides/                       # Detailed guides
├── config/                       # Configuration files
├── examples/                     # Usage examples
└── Import-AllModules.ps1        # Master import script
```

## Quick Start

### 1. Installation

```powershell
# Clone or download the script library
cd C:\Scripts
git clone https://github.com/itvedas/powershell-scripts.git
```

### 2. Import Modules

```powershell
# Load all modules in current PowerShell session
. .\Import-AllModules.ps1

# View available functions
Get-ITVedasModuleInfo -InformationType Functions
```

### 3. Run Your First Script

```powershell
# Example: Create AD users from CSV
$result = New-ADUserBulkImport `
    -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Staff,DC=contoso,DC=com" `
    -DefaultPassword (ConvertTo-SecureString -String "TempPass@123" -AsPlainText -Force) `
    -LogPath "C:\Logs\import.log"

# View results
$result
```

## Modules & Functions

### 1. Active Directory Management
- **New-ADUserBulkImport** - Create multiple users from CSV file
- **Get-ADUserPermissionAudit** - Audit user permissions and group memberships
- **Resolve-ADAccountLockout** - Unlock accounts and reset passwords
- **New-ADSecurityGroupStructure** - Create standardized group structures

### 2. DNS Management
- **New-DNSZoneWithRecords** - Create zones and populate with records
- **Validate-DNSReplication** - Verify zone replication across servers

### 3. DHCP Management
- **New-DHCPScopeWithSettings** - Create scopes with standard configuration
- **Monitor-DHCPLeases** - Monitor lease utilization and health

### 4. File Server Management
- **Set-NTFSPermissions** - Automate permission assignment
- **Get-FileServerAudit** - Audit permissions and usage

### 5. Backup & Recovery
- **New-AutomatedBackup** - Schedule automated backup jobs

### 6. Security Hardening
- **Invoke-WindowsSecurityHardening** - Apply security best practices

### 7. Performance Monitoring
- **Get-ServerHealthReport** - Generate comprehensive health reports

### 8. Server Deployment
- **Install-ServerRoles** - Automate role installation

## Requirements

### System Requirements
- **Windows Server 2012 R2 or later** (2016, 2019, 2022 recommended)
- **PowerShell 5.1+** (PowerShell 7+ supported)
- **Administrator privileges** for most operations
- **Active Directory module** (for AD-related tasks)
- **DHCP/DNS server tools** (for DHCP/DNS management)

### Modules & Dependencies
- ActiveDirectory (Windows feature)
- DNSServer (Windows feature)
- DHCP (Windows feature)
- NTFSSecurity (optional, for advanced permission management)

## Configuration

### Environment Setup

1. **Create Log Directory**
   ```powershell
   New-Item -Path "C:\Logs\ITVedas" -ItemType Directory -Force
   ```

2. **Create Data Directory**
   ```powershell
   New-Item -Path "C:\Data\ITVedas" -ItemType Directory -Force
   ```

3. **Configure Execution Policy**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
   ```

### Template Configuration

Templates are provided in the `config/` directory:
- `ad-users-template.csv` - CSV format for bulk user import
- `dns-records-template.csv` - CSV format for DNS records
- `dhcp-configuration-template.json` - DHCP scope configuration

## Usage Examples

### Example 1: Bulk Import Active Directory Users

```powershell
# Load modules
. .\Import-AllModules.ps1

# Import users from CSV
$result = New-ADUserBulkImport `
    -CSVPath "C:\Data\ITVedas\users.csv" `
    -TargetOU "OU=NewUsers,OU=Staff,DC=contoso,DC=com" `
    -DefaultPassword (ConvertTo-SecureString -String "InitialPass@2026" -AsPlainText -Force) `
    -SendWelcomeEmail

# View results
$result.Users | Format-Table

# Check logs
Get-Content $result.LogPath
```

### Example 2: Audit User Permissions

```powershell
# Audit specific user
Get-ADUserPermissionAudit -Username "jsmith" -IncludeNested

# Audit by department and export
Get-ADUserPermissionAudit `
    -DepartmentFilter "Finance" `
    -OutputFormat CSV `
    -OutputPath "C:\Reports\Finance_Permissions.csv"
```

### Example 3: Create DHCP Scope

```powershell
$scopeParams = @{
    ScopeName         = "Building-A-Offices"
    StartRange        = "192.168.10.100"
    EndRange          = "192.168.10.200"
    SubnetMask        = "255.255.255.0"
    DefaultGateway    = "192.168.10.1"
    DNSServers        = @("8.8.8.8", "8.8.4.4")
    LeaseDuration     = 8
    ExclusionRanges   = @("192.168.10.1-192.168.10.20")
}

New-DHCPScopeWithSettings @scopeParams
```

### Example 4: Audit File Server Permissions

```powershell
# Audit with detailed report
Get-FileServerAudit `
    -ServerPath "\\fileserver\Finance" `
    -IncludeAccessTimes `
    -ReportLargeFiles 500 `
    -OutputFormat HTML | Out-File "C:\Reports\FileServer_Audit.html"
```

### Example 5: Generate Server Health Report

```powershell
# Get comprehensive health report
$health = Get-ServerHealthReport `
    -ComputerName "Server1.contoso.com" `
    -IncludeEventLogs `
    -IncludeServices `
    -OutputFormat HTML

$health | Out-File "C:\Reports\Server1_Health.html"
```

### Example 6: Set NTFS Permissions

```powershell
# Set permissions for group
Set-NTFSPermissions `
    -Path "D:\Shares\Finance" `
    -Identity "CONTOSO\Finance-Team" `
    -FileSystemRights "Modify" `
    -Scope "This Folder, Subfolders and Files" `
    -Recursive
```

### Example 7: Create Automated Backup

```powershell
# Schedule daily backup
New-AutomatedBackup `
    -BackupName "FileServer-Daily" `
    -SourcePath "D:\Shares" `
    -DestinationPath "E:\Backups" `
    -ScheduleType Daily `
    -RetentionDays 30 `
    -CompressionEnabled
```

### Example 8: Install Server Roles

```powershell
# Install AD, DNS, and DHCP roles
Install-ServerRoles `
    -Roles @('AD-Domain-Services', 'DNS', 'DHCP') `
    -IncludeManagementTools `
    -ValidateInstallation `
    -RestartIfRequired
```

## Best Practices

### 1. Error Handling
All functions include comprehensive try-catch blocks:
```powershell
try {
    # Function code
}
catch {
    Write-Error "Error: $_"
    return $null
}
```

### 2. Logging
Enable logging for audit trails:
```powershell
New-ADUserBulkImport `
    -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Staff,DC=contoso,DC=com" `
    -DefaultPassword $securePass `
    -LogPath "C:\Logs\ad-import-$(Get-Date -Format yyyyMMdd).log"
```

### 3. Verbose Output
Use verbose flag for detailed execution information:
```powershell
$VerbosePreference = "Continue"
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Staff,DC=contoso,DC=com" -DefaultPassword $securePass
```

### 4. Pipeline Support
Functions support PowerShell pipeline:
```powershell
Get-ADUserPermissionAudit | Where-Object { $_.Enabled -eq $true } | Format-Table
```

### 5. Parameter Validation
All functions validate parameters:
```powershell
# This will throw an error - invalid path
Set-NTFSPermissions -Path "C:\InvalidPath" -Identity "CONTOSO\Group" -FileSystemRights "Read"
```

## Troubleshooting

### Module Import Issues

**Problem**: "The term 'function-name' is not recognized"

**Solution**:
```powershell
# Reload modules
. .\Import-AllModules.ps1 -ListFunctions

# Verify module loading
Get-ITVedasModuleInfo -InformationType Loaded
```

### Active Directory Errors

**Problem**: "The specified account already exists"

**Solution**:
- Check CSV for duplicate usernames
- Verify users don't already exist in target OU
```powershell
Get-ADUser -Filter { SamAccountName -like "*" } | Where-Object { $_.Name -like "TestUser*" }
```

### DHCP Errors

**Problem**: "DHCP server is not operational"

**Solution**:
```powershell
# Verify DHCP service
Get-Service -Name DHCPServer | Format-Table

# Restart DHCP service
Restart-Service -Name DHCPServer
```

### Permission Errors

**Problem**: "Access is denied"

**Solution**:
- Run PowerShell as Administrator
- Verify account has required permissions
- Check Group Policy restrictions

### CSV Import Issues

**Problem**: "CSV file not properly formatted"

**Solution**:
- Use provided templates
- Ensure all required columns present
- Verify encoding is UTF-8

## Advanced Configuration

### Custom Parameters

Modify configuration files in `config/` directory:
```json
{
  "LogPath": "C:\Logs\ITVedas",
  "BackupRetention": 30,
  "PasswordExpiry": 90,
  "DHCPThreshold": 80,
  "DiskThreshold": 90
}
```

### Scheduling

Create scheduled tasks for automated execution:
```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\Scripts\backup.ps1"
    
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"

Register-ScheduledTask -TaskName "Daily-Backup" -Action $action -Trigger $trigger
```

## Security Considerations

1. **Sensitive Data**
   - Store passwords in secure location
   - Use SecureString for password parameters
   - Don't hardcode credentials

2. **Audit Logging**
   - Enable comprehensive event logging
   - Archive logs regularly
   - Monitor for suspicious activity

3. **Least Privilege**
   - Delegate minimal required permissions
   - Use service accounts for scheduled tasks
   - Implement role-based access control

4. **Encryption**
   - Encrypt backup files
   - Use TLS for network operations
   - Protect configuration files

## Performance Optimization

### Bulk Operations

```powershell
# For large operations, consider batching
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

### Parallel Processing

```powershell
# Use ForEach-Object with -Parallel (PS 7+)
Get-ADUser -Filter * | ForEach-Object -Parallel {
    Get-ADUserPermissionAudit -Username $_.SamAccountName
}
```

## Support & Documentation

### Getting Help

```powershell
# Detailed function help
Get-Help New-ADUserBulkImport -Full

# Examples
Get-Help New-ADUserBulkImport -Examples

# Online help
Get-Help New-ADUserBulkImport -Online
```

### Documentation Files

- `INSTALLATION.md` - Detailed installation guide
- `QUICKSTART.md` - Quick start guide
- `TROUBLESHOOTING.md` - Troubleshooting reference
- `EXAMPLES.md` - Detailed usage examples

## Version History

### Version 1.0 (2026-07-04)
- Initial release
- 8 modules with 20+ functions
- Comprehensive documentation
- Error handling and logging

## Contributing

To contribute to this library:
1. Follow PowerShell best practices
2. Include comprehensive help documentation
3. Add error handling and logging
4. Provide usage examples
5. Test thoroughly before submission

## License

This script library is provided as-is for use by IT Vedas community and enterprises.

## Contact & Support

For issues, questions, or contributions:
- Email: itvedas29@gmail.com
- Website: https://itvedas.com
- Documentation: See guides/ directory

---

**Last Updated**: 2026-07-04
**Version**: 1.0
**Maintainer**: IT Vedas
