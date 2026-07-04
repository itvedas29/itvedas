# Installation Guide - IT Vedas PowerShell Script Library

Complete step-by-step installation guide for the IT Vedas PowerShell Script Library.

## Prerequisites

### System Requirements

- **Operating System**: Windows Server 2012 R2 or later (2016, 2019, 2022 recommended)
- **PowerShell**: Version 5.1 or later (Windows PowerShell or PowerShell 7+)
- **Administrator Rights**: Required for most server management tasks
- **Disk Space**: Minimum 500 MB for all modules
- **Network**: Internet connection for initial setup (optional)

### Verify Prerequisites

```powershell
# Check Windows version
[System.Environment]::OSVersion.VersionString

# Check PowerShell version
$PSVersionTable.PSVersion

# Verify administrator status
([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
```

## Installation Steps

### Step 1: Download Script Library

**Option A: Direct Download**
1. Download the script library package
2. Extract to desired location (e.g., `C:\Scripts\ITVedas\`)

**Option B: Clone from Repository**
```powershell
# Install Git (if not installed)
# Download from https://git-scm.com/download/win

# Clone repository
cd C:\Scripts
git clone https://github.com/itvedas/powershell-scripts.git

# Navigate to directory
cd powershell-scripts
```

### Step 2: Create Directory Structure

```powershell
# Create necessary directories
New-Item -Path "C:\Scripts\ITVedas" -ItemType Directory -Force
New-Item -Path "C:\Logs\ITVedas" -ItemType Directory -Force
New-Item -Path "C:\Data\ITVedas" -ItemType Directory -Force
New-Item -Path "C:\Reports\ITVedas" -ItemType Directory -Force
New-Item -Path "C:\Backup\ITVedas" -ItemType Directory -Force

# Verify creation
Get-ChildItem -Path "C:\Scripts\ITVedas"
```

### Step 3: Configure PowerShell Execution Policy

```powershell
# Check current execution policy
Get-ExecutionPolicy

# Set execution policy (for current user)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Or for LocalMachine (requires admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

# Verify setting
Get-ExecutionPolicy
```

### Step 4: Copy Script Files

```powershell
# Copy entire library to scripts directory
Copy-Item -Path ".\powershell-scripts\*" -Destination "C:\Scripts\ITVedas\" -Recurse -Force

# Verify copy
Get-ChildItem -Path "C:\Scripts\ITVedas" -Recurse | Where-Object { $_.Extension -eq ".ps1" } | Measure-Object
```

### Step 5: Install Required Windows Features

#### For Active Directory Management
```powershell
# Install Active Directory module
Add-WindowsFeature RSAT-AD-PowerShell
```

#### For DNS Management
```powershell
# Install DNS tools
Add-WindowsFeature RSAT-DNS-Server
```

#### For DHCP Management
```powershell
# Install DHCP tools
Add-WindowsFeature RSAT-DHCP
```

#### For File Server Management
```powershell
# Install File Services tools
Add-WindowsFeature RSAT-File-Services
```

#### Install All at Once
```powershell
# Install all recommended features
Add-WindowsFeature `
    RSAT-AD-PowerShell, `
    RSAT-DNS-Server, `
    RSAT-DHCP, `
    RSAT-File-Services, `
    RSAT-Hyper-V-Tools

# Verify installation
Get-WindowsFeature -Name RSAT-* | Where-Object { $_.Installed -eq $true } | Format-Table
```

### Step 6: Initialize Script Library

```powershell
# Navigate to script directory
cd C:\Scripts\ITVedas

# Load the master import script
. .\Import-AllModules.ps1

# Verify all modules loaded
Get-ITVedasModuleInfo -InformationType Summary
```

### Step 7: Validate Installation

```powershell
# Run validation
. .\Import-AllModules.ps1 -ValidateOnly

# List all available functions
Get-ITVedasModuleInfo -InformationType Functions

# Check specific module
Get-Command -Name "New-ADUserBulkImport" | Format-Table
```

## Configuration

### Environment Variables

Create a configuration file for your environment:

**File**: `C:\Scripts\ITVedas\config\environment.json`

```json
{
  "LogPath": "C:\Logs\ITVedas",
  "DataPath": "C:\Data\ITVedas",
  "ReportPath": "C:\Reports\ITVedas",
  "BackupPath": "C:\Backup\ITVedas",
  "Domain": "contoso.com",
  "DomainDN": "DC=contoso,DC=com",
  "DefaultOU": "OU=Users,DC=contoso,DC=com",
  "DHCPServer": "dhcp1.contoso.com",
  "DNSServer": "dns1.contoso.com"
}
```

### PowerShell Profile Configuration

Add to your PowerShell profile (`$PROFILE`) for automatic loading:

```powershell
# Open PowerShell profile in editor
notepad $PROFILE

# Add these lines to your profile
# IT Vedas PowerShell Modules
$ITVedasPath = "C:\Scripts\ITVedas"
if (Test-Path $ITVedasPath) {
    . (Join-Path $ITVedasPath "Import-AllModules.ps1")
}
```

Create profile if it doesn't exist:
```powershell
# Create profile if needed
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
}
```

### Proxy Configuration (if required)

If behind a corporate proxy:

```powershell
# Set proxy settings
[System.Net.ServicePointManager]::DefaultConnectionLimit = 10
[System.Net.ServicePointManager]::ReusePort = $true

# Configure proxy credentials
$proxy = New-Object System.Net.WebProxy("http://proxy.contoso.com:8080", $true)
$proxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
[System.Net.ServicePointManager]::DefaultWebProxy = $proxy
```

## Verification Checklist

After installation, verify all components:

```powershell
# Checklist Script
Write-Host "Installation Verification Checklist"
Write-Host "===================================="

# 1. Check directories
Write-Host "`n1. Directory Structure:"
$dirs = @("C:\Scripts\ITVedas", "C:\Logs\ITVedas", "C:\Data\ITVedas", "C:\Reports\ITVedas")
foreach ($dir in $dirs) {
    $exists = Test-Path $dir
    Write-Host "  $dir : $(if ($exists) {'✓ OK'} else {'✗ MISSING'})"
}

# 2. Check PowerShell version
Write-Host "`n2. PowerShell Version: $($PSVersionTable.PSVersion)"

# 3. Check execution policy
Write-Host "`n3. Execution Policy: $(Get-ExecutionPolicy)"

# 4. Check required modules
Write-Host "`n4. Required Modules:"
$modules = @('ActiveDirectory', 'DNSServer', 'DHCP')
foreach ($module in $modules) {
    $available = Get-Module -Name $module -ListAvailable
    Write-Host "  $module : $(if ($available) {'✓ Available'} else {'✗ Not Available'})"
}

# 5. Check script files
Write-Host "`n5. Script Files:"
$scripts = @(Get-ChildItem -Path "C:\Scripts\ITVedas\modules" -Filter "*.ps1" -Recurse)
Write-Host "  Total scripts found: $($scripts.Count)"

# 6. Load modules
Write-Host "`n6. Module Loading:"
try {
    . "C:\Scripts\ITVedas\Import-AllModules.ps1" -ErrorAction Stop
    $moduleInfo = Get-ITVedasModuleInfo
    Write-Host "  Modules loaded: $($moduleInfo.ModulesLoaded)"
    Write-Host "  Functions available: $($moduleInfo.AvailableFunctions)"
}
catch {
    Write-Error "Failed to load modules: $_"
}

Write-Host "`n===================================="
Write-Host "Verification Complete"
```

## Troubleshooting Installation

### Issue: "Cannot find path"

**Cause**: Script library not in expected location

**Solution**:
```powershell
# Verify location
Get-ChildItem -Path "C:\Scripts\ITVedas" | Select-Object -First 5

# Update path if needed
$ITVedasPath = "C:\YourPath\to\scripts"
. "$ITVedasPath\Import-AllModules.ps1"
```

### Issue: "Active Directory module not found"

**Cause**: RSAT tools not installed

**Solution**:
```powershell
# Install required feature
Add-WindowsFeature RSAT-AD-PowerShell

# Verify installation
Get-Module -Name ActiveDirectory -ListAvailable
```

### Issue: "Script execution disabled"

**Cause**: Execution policy set to Restricted

**Solution**:
```powershell
# Change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Verify
Get-ExecutionPolicy
```

### Issue: "Access denied" on directories

**Cause**: Insufficient permissions

**Solution**:
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell and select "Run as Administrator"

# Or run elevated command
Start-Process powershell -Verb RunAs
```

### Issue: "Module import fails"

**Cause**: Syntax errors or dependencies missing

**Solution**:
```powershell
# Validate modules
. "C:\Scripts\ITVedas\Import-AllModules.ps1" -ValidateOnly

# Check for errors
Get-ITVedasModuleInfo -InformationType Failed
```

## Post-Installation

### Run Initial Tests

```powershell
# Test Active Directory functions
Get-Command -Module ActiveDirectory | Measure-Object

# Test DNS functions
Get-Command -Name "*DNS*" | Measure-Object

# Test DHCP functions
Get-Command -Name "*DHCP*" | Measure-Object
```

### Create Sample Configuration Files

Use templates provided in `config/` directory:

```powershell
# Copy templates to data directory
Copy-Item "C:\Scripts\ITVedas\config\*-template.*" `
    -Destination "C:\Data\ITVedas\" -Force
```

### Schedule Initial Backup

```powershell
# Create initial backup of configuration
New-AutomatedBackup `
    -BackupName "InitialConfig" `
    -SourcePath "C:\Scripts\ITVedas" `
    -DestinationPath "C:\Backup\ITVedas" `
    -ScheduleType Daily `
    -RetentionDays 30
```

### Set Up Logging

```powershell
# Create log directory structure
$logDirs = @(
    "C:\Logs\ITVedas\AD",
    "C:\Logs\ITVedas\DNS",
    "C:\Logs\ITVedas\DHCP",
    "C:\Logs\ITVedas\FileServer",
    "C:\Logs\ITVedas\Backup",
    "C:\Logs\ITVedas\Security",
    "C:\Logs\ITVedas\Performance"
)

foreach ($dir in $logDirs) {
    New-Item -Path $dir -ItemType Directory -Force
}
```

## Upgrading

To upgrade to a newer version:

```powershell
# Backup current installation
Copy-Item -Path "C:\Scripts\ITVedas" -Destination "C:\Scripts\ITVedas_Backup_$(Get-Date -Format yyyyMMdd)" -Recurse

# Download and extract new version
# Copy files to installation directory

# Reload modules
Remove-Module -Name * -ErrorAction SilentlyContinue
. "C:\Scripts\ITVedas\Import-AllModules.ps1"

# Verify upgrade
Get-ITVedasModuleInfo
```

## Uninstallation

To remove the script library:

```powershell
# Remove script files
Remove-Item -Path "C:\Scripts\ITVedas" -Recurse -Force

# Remove log files (optional)
Remove-Item -Path "C:\Logs\ITVedas" -Recurse -Force

# Remove PowerShell profile entries (manual edit required)
# Edit your profile with: notepad $PROFILE
# Remove IT Vedas entries
```

## Next Steps

After successful installation:

1. **Read Quick Start Guide**: `QUICKSTART.md`
2. **Review Examples**: `examples/` directory
3. **Check Troubleshooting**: `TROUBLESHOOTING.md`
4. **Explore Functions**: `Get-Help <function-name> -Full`

## Support

For installation issues:
- Check `TROUBLESHOOTING.md`
- Review error messages carefully
- Verify prerequisites are met
- Contact IT Vedas support

---

**Last Updated**: 2026-07-04
**Version**: 1.0
