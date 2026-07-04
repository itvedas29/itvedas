# IT Vedas PowerShell Script Library - Complete Index

Master index and guide to all resources in the IT Vedas PowerShell Script Library.

## Quick Navigation

- **Getting Started**: [README.md](README.md) - Complete overview
- **Installation**: [INSTALLATION.md](INSTALLATION.md) - Step-by-step setup guide
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) - Common tasks in 5 minutes
- **Quick Reference**: [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - Command cheat sheet
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- **Deployment**: [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md) - Production deployment guide

## Directory Structure

```
powershell-scripts/
├── modules/                          # PowerShell modules (8 total)
│   ├── ActiveDirectory/             # AD user, group, and account management
│   │   ├── New-ADUserBulkImport.ps1
│   │   ├── Get-ADUserPermissionAudit.ps1
│   │   ├── Resolve-ADAccountLockout.ps1
│   │   └── New-ADSecurityGroupStructure.ps1
│   ├── DNS/                         # DNS zone and record management
│   │   ├── New-DNSZoneWithRecords.ps1
│   │   └── Validate-DNSReplication.ps1
│   ├── DHCP/                        # DHCP scope and lease management
│   │   ├── New-DHCPScopeWithSettings.ps1
│   │   └── Monitor-DHCPLeases.ps1
│   ├── FileServer/                  # File server and permission management
│   │   ├── Set-NTFSPermissions.ps1
│   │   └── Get-FileServerAudit.ps1
│   ├── BackupRecovery/              # Automated backup solutions
│   │   └── New-AutomatedBackup.ps1
│   ├── SecurityHardening/           # Security configuration
│   │   └── Invoke-WindowsSecurityHardening.ps1
│   ├── PerformanceMonitoring/       # Health and performance reports
│   │   └── Get-ServerHealthReport.ps1
│   └── ServerDeployment/            # Role installation and configuration
│       └── Install-ServerRoles.ps1
├── templates/                        # (Placeholder for future templates)
├── guides/                          # (Placeholder for future guides)
├── config/                          # Configuration templates
│   ├── ad-users-template.csv        # CSV template for bulk user import
│   └── dns-records-template.csv     # CSV template for DNS records
├── examples/                        # Complete workflow examples
│   └── Complete-Employee-Onboarding.ps1  # End-to-end employee setup
├── Import-AllModules.ps1            # Master import script
├── README.md                        # Complete documentation
├── INSTALLATION.md                  # Installation guide
├── QUICKSTART.md                    # Quick start guide
├── QUICK-REFERENCE.md               # Command reference
├── TROUBLESHOOTING.md               # Troubleshooting guide
├── DEPLOYMENT-CHECKLIST.md          # Deployment checklist
└── INDEX.md                         # This file
```

## Module Reference

### 1. Active Directory Management Module

**File Location**: `modules/ActiveDirectory/`

**Functions**:
1. **New-ADUserBulkImport** - Bulk import users from CSV file
   - Parameters: CSVPath, TargetOU, DefaultPassword, SendWelcomeEmail, LogPath
   - Output: Success count, failure count, user list, log path
   - Use Case: Create multiple users at once from CSV data

2. **Get-ADUserPermissionAudit** - Audit user permissions and group membership
   - Parameters: Username, DepartmentFilter, OutputFormat, IncludeNested
   - Output: User details, group membership, permissions
   - Use Case: Audit user access and group membership

3. **Resolve-ADAccountLockout** - Unlock locked accounts
   - Parameters: Username, UnlockOnly, ResetPassword, TemporaryPassword
   - Output: Unlock status, previous lockout time, password reset status
   - Use Case: Quickly unlock user accounts and optionally reset passwords

4. **New-ADSecurityGroupStructure** - Create standardized group structures
   - Parameters: OrganizationName, ParentOU, TemplateType, GroupsList, Scope
   - Output: Created groups, failed groups, summary
   - Use Case: Create organized group hierarchies for departments

**Example Usage**:
```powershell
# Import 10 users from CSV
New-ADUserBulkImport -CSVPath "C:\Data\users.csv" `
    -TargetOU "OU=Finance,DC=contoso,DC=com" `
    -DefaultPassword (ConvertTo-SecureString "Pass@123" -AsPlainText -Force)

# Unlock locked account
Resolve-ADAccountLockout -Username "jsmith" -ResetPassword
```

---

### 2. DNS Management Module

**File Location**: `modules/DNS/`

**Functions**:
1. **New-DNSZoneWithRecords** - Create DNS zone with records
   - Parameters: ZoneName, DNSServer, ZoneType, RecordsCSV, AllowTransfer, CreateStandardRecords
   - Output: Zone creation status, records created, records failed
   - Use Case: Automate DNS zone and record creation

2. **Validate-DNSReplication** - Validate zone replication
   - Parameters: ZoneName, DNSServers, SerialNumberCheck, RecordCountCheck, OutputFormat
   - Output: Server details, SOA serial, record count, inconsistencies
   - Use Case: Verify DNS zones are properly replicated

**Example Usage**:
```powershell
# Create zone with standard records
New-DNSZoneWithRecords -ZoneName "contoso.com" -CreateStandardRecords

# Validate replication across servers
Validate-DNSReplication -ZoneName "contoso.com" `
    -DNSServers @("dns1.contoso.com", "dns2.contoso.com")
```

---

### 3. DHCP Management Module

**File Location**: `modules/DHCP/`

**Functions**:
1. **New-DHCPScopeWithSettings** - Create DHCP scope with configuration
   - Parameters: ScopeName, StartRange, EndRange, SubnetMask, DefaultGateway, DNSServers, LeaseDuration, ExclusionRanges, DHCPServer
   - Output: Scope details, configuration status
   - Use Case: Create and configure DHCP scopes

2. **Monitor-DHCPLeases** - Monitor DHCP lease utilization
   - Parameters: DHCPServer, ScopeFilter, ThresholdWarning, ThresholdCritical, OutputFormat
   - Output: Scope statistics, utilization percentage, status
   - Use Case: Monitor DHCP scope health and utilization

**Example Usage**:
```powershell
# Create DHCP scope
New-DHCPScopeWithSettings -ScopeName "Building-A" `
    -StartRange "192.168.10.100" -EndRange "192.168.10.200" `
    -SubnetMask "255.255.255.0" -DefaultGateway "192.168.10.1" `
    -DNSServers @("8.8.8.8", "8.8.4.4")

# Monitor scopes
Monitor-DHCPLeases -OutputFormat HTML | Out-File "report.html"
```

---

### 4. File Server Management Module

**File Location**: `modules/FileServer/`

**Functions**:
1. **Set-NTFSPermissions** - Set NTFS permissions on files/folders
   - Parameters: Path, Identity, AccessType, FileSystemRights, Scope, IsInherited, Recursive
   - Output: Permission assignment status
   - Use Case: Configure file share permissions

2. **Get-FileServerAudit** - Audit file server permissions and usage
   - Parameters: ServerPath, IncludeAccessTimes, ReportLargeFiles, OutputFormat
   - Output: File/folder details, permissions, usage statistics
   - Use Case: Generate comprehensive file server audit reports

**Example Usage**:
```powershell
# Set permissions
Set-NTFSPermissions -Path "D:\Shares\Finance" `
    -Identity "CONTOSO\Finance-Team" `
    -FileSystemRights "Modify" -Recursive

# Audit file server
Get-FileServerAudit -ServerPath "\\fileserver" `
    -OutputFormat CSV | Out-File "audit.csv"
```

---

### 5. Backup & Recovery Module

**File Location**: `modules/BackupRecovery/`

**Functions**:
1. **New-AutomatedBackup** - Schedule automated backups
   - Parameters: BackupName, SourcePath, DestinationPath, ScheduleType, RetentionDays, CompressionEnabled, NotificationEmail
   - Output: Backup configuration, scheduled task details
   - Use Case: Automate backup scheduling with retention policies

**Example Usage**:
```powershell
# Create daily backup with 30-day retention
New-AutomatedBackup -BackupName "FileServer-Daily" `
    -SourcePath "D:\Shares" `
    -DestinationPath "E:\Backups" `
    -ScheduleType Daily -RetentionDays 30 -CompressionEnabled
```

---

### 6. Security Hardening Module

**File Location**: `modules/SecurityHardening/`

**Functions**:
1. **Invoke-WindowsSecurityHardening** - Apply security hardening
   - Parameters: ApplyUpdates, ConfigureFirewall, EnableAudit, DisableUnnecessaryServices, PasswordPolicy, Level
   - Output: Hardening status for each component
   - Use Case: Apply security best practices to systems

**Example Usage**:
```powershell
# Apply standard hardening
Invoke-WindowsSecurityHardening -Level Standard `
    -ApplyUpdates -ConfigureFirewall -EnableAudit
```

---

### 7. Performance Monitoring Module

**File Location**: `modules/PerformanceMonitoring/`

**Functions**:
1. **Get-ServerHealthReport** - Generate server health report
   - Parameters: ComputerName, IncludeEventLogs, IncludeServices, ThresholdCPU, ThresholdMemory, ThresholdDisk, OutputFormat
   - Output: System info, performance metrics, disk status, event log summary
   - Use Case: Generate comprehensive server health reports

**Example Usage**:
```powershell
# Generate health report
Get-ServerHealthReport -ComputerName "Server1" `
    -IncludeEventLogs -IncludeServices -OutputFormat HTML
```

---

### 8. Server Deployment Module

**File Location**: `modules/ServerDeployment/`

**Functions**:
1. **Install-ServerRoles** - Install Windows Server roles
   - Parameters: Roles, Features, IncludeManagementTools, ValidateInstallation, ComputerName, RestartIfRequired
   - Output: Installation status, success count, failure count
   - Use Case: Automate server role installation

**Example Usage**:
```powershell
# Install AD, DNS, DHCP
Install-ServerRoles `
    -Roles @('AD-Domain-Services', 'DNS', 'DHCP') `
    -IncludeManagementTools -ValidateInstallation
```

---

## Configuration Files

### Templates

- **ad-users-template.csv** - Sample CSV format for bulk user import
  - Columns: FirstName, LastName, Username, Email, Department, Title
  - Location: `config/`

- **dns-records-template.csv** - Sample CSV format for DNS records
  - Columns: Name, Type, Value, Preference, TTL
  - Location: `config/`

### Configuration

Edit configuration files in `config/` directory to match your environment:
- Domain name
- LDAP distinguished names (DN)
- Server names
- IP addresses
- Log paths

---

## Documentation Files

### Main Documentation

| File | Purpose | Audience |
|------|---------|----------|
| README.md | Complete library overview | Everyone |
| INSTALLATION.md | Step-by-step installation | System Administrators |
| QUICKSTART.md | Quick start tasks | New Users |
| QUICK-REFERENCE.md | Command reference | Experienced Users |
| TROUBLESHOOTING.md | Problem solutions | Support Staff |
| DEPLOYMENT-CHECKLIST.md | Production deployment | Project Managers |
| INDEX.md | Complete index | Everyone |

### Example Scripts

- **Complete-Employee-Onboarding.ps1** - Full employee setup workflow
  - Creates AD user, sets permissions, configures access
  - Location: `examples/`

---

## Getting Started

### 1. First Time Users
1. Read [README.md](README.md)
2. Follow [INSTALLATION.md](INSTALLATION.md)
3. Try [QUICKSTART.md](QUICKSTART.md)
4. Use [QUICK-REFERENCE.md](QUICK-REFERENCE.md) as needed

### 2. Experienced PowerShell Users
1. Review [README.md](README.md) for module overview
2. Check [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for syntax
3. Review examples in module comments
4. Use Get-Help for detailed documentation

### 3. Production Deployment
1. Read [INSTALLATION.md](INSTALLATION.md)
2. Review [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md)
3. Test in lab environment first
4. Use checklist for production deployment

### 4. Troubleshooting
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for your issue
2. Review module help: `Get-Help FunctionName -Full`
3. Enable verbose logging
4. Check system event logs

---

## Common Workflows

### Workflow 1: Bulk User Creation
1. Prepare CSV file using `config/ad-users-template.csv`
2. Load modules: `. .\Import-AllModules.ps1`
3. Run: `New-ADUserBulkImport -CSVPath "path\to\file.csv" -TargetOU "OU=..."`
4. Review logs for any issues

### Workflow 2: User Access Audit
1. Load modules: `. .\Import-AllModules.ps1`
2. Run: `Get-ADUserPermissionAudit -Username "username" -IncludeNested`
3. Export: `| Export-Csv "report.csv" -NoTypeInformation`

### Workflow 3: File Server Audit
1. Load modules: `. .\Import-AllModules.ps1`
2. Run: `Get-FileServerAudit -ServerPath "\\server\share"`
3. Generate HTML: `| Out-File "report.html"`

### Workflow 4: Scheduled Backups
1. Load modules: `. .\Import-AllModules.ps1`
2. Run: `New-AutomatedBackup -BackupName "Name" -SourcePath "..." -DestinationPath "..."`
3. Verify: `Get-ScheduledTask -TaskName "Backup_*"`

### Workflow 5: Server Health Monitoring
1. Load modules: `. .\Import-AllModules.ps1`
2. Run: `Get-ServerHealthReport -ComputerName "ServerName"`
3. Schedule: `Get-ScheduledTask -TaskName "*Health*"`

---

## Performance Considerations

- Bulk operations: Use -Verbose for tracking
- Large file servers: Run audits during off-hours
- DNS operations: Verify replication before proceeding
- DHCP monitoring: Check thresholds match your environment
- Backups: Schedule during low-usage periods

---

## Security Best Practices

1. **Credentials**: Use SecureString, never hardcode passwords
2. **Logging**: Enable comprehensive logging for audit trails
3. **Access**: Restrict script execution to authorized users
4. **Validation**: Always validate user input
5. **Testing**: Test in lab before production deployment

---

## Support & Resources

- **Help on Functions**: `Get-Help FunctionName -Full`
- **Examples**: `Get-Help FunctionName -Examples`
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Quick Reference**: See [QUICK-REFERENCE.md](QUICK-REFERENCE.md)

---

## Frequently Asked Questions

**Q: Can I run these scripts on PowerShell 7?**
A: Yes, PowerShell 7+ is fully supported and recommended for new installations.

**Q: Do I need all the Windows features installed?**
A: No, only install features for the modules you'll use (e.g., RSAT-AD-PowerShell for AD functions).

**Q: Can I modify the scripts?**
A: Yes, all scripts include comments and are fully editable. Maintain proper error handling and documentation.

**Q: How do I schedule automated tasks?**
A: Use Windows Task Scheduler or PowerShell's New-ScheduledTask cmdlets.

**Q: Are these scripts production-ready?**
A: Yes, all scripts include error handling, logging, and have been tested. Always test in lab first.

---

## Version Information

- **Version**: 1.0
- **Last Updated**: 2026-07-04
- **Compatibility**: PowerShell 5.1+, Windows Server 2012 R2+
- **Status**: Production Ready

---

## Quick Links

- 📖 [Full Documentation](README.md)
- 🚀 [Installation Guide](INSTALLATION.md)
- ⚡ [Quick Start (5 minutes)](QUICKSTART.md)
- 📋 [Command Reference](QUICK-REFERENCE.md)
- 🔧 [Troubleshooting](TROUBLESHOOTING.md)
- ✅ [Deployment Checklist](DEPLOYMENT-CHECKLIST.md)

---

**Need help?** Check the relevant documentation file or use `Get-Help` on any function.

**Found an issue?** Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or check function help documentation.

---

**Last Updated**: 2026-07-04 | **Version**: 1.0 | **Status**: Production Ready
