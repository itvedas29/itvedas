<#
.SYNOPSIS
    Master script to import all IT Vedas PowerShell modules.

.DESCRIPTION
    Centralized import script that loads all available modules and initializes
    the PowerShell environment for IT management tasks.

.PARAMETER ModulePath
    Path to modules directory. Default: Script directory\modules

.PARAMETER ListFunctions
    Display all available functions.

.PARAMETER ValidateOnly
    Validate module integrity without loading.

.EXAMPLE
    . .\Import-AllModules.ps1
    Get-ADUserBulkImport -Help

.EXAMPLE
    . .\Import-AllModules.ps1 -ListFunctions | Format-Table

.NOTES
    Author: IT Vedas
    Version: 1.0
    Last Modified: 2026-07-04
#>

param (
    [Parameter(Mandatory = $false)]
    [string]$ModulePath = (Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) -ChildPath "modules"),

    [Parameter(Mandatory = $false)]
    [switch]$ListFunctions,

    [Parameter(Mandatory = $false)]
    [switch]$ValidateOnly
)

# Validate module path exists
if (-not (Test-Path $ModulePath)) {
    Write-Error "Module path not found: $ModulePath"
    exit 1
}

Write-Verbose "IT Vedas PowerShell Module Loader"
Write-Verbose "Module Path: $ModulePath"

# Define module structure
$modules = @{
    'ActiveDirectory'       = @(
        'New-ADUserBulkImport.ps1',
        'Get-ADUserPermissionAudit.ps1',
        'Resolve-ADAccountLockout.ps1',
        'New-ADSecurityGroupStructure.ps1'
    );
    'DNS'                   = @(
        'New-DNSZoneWithRecords.ps1',
        'Validate-DNSReplication.ps1'
    );
    'DHCP'                  = @(
        'New-DHCPScopeWithSettings.ps1',
        'Monitor-DHCPLeases.ps1'
    );
    'FileServer'            = @(
        'Set-NTFSPermissions.ps1',
        'Get-FileServerAudit.ps1'
    );
    'BackupRecovery'        = @(
        'New-AutomatedBackup.ps1'
    );
    'SecurityHardening'     = @(
        'Invoke-WindowsSecurityHardening.ps1'
    );
    'PerformanceMonitoring' = @(
        'Get-ServerHealthReport.ps1'
    );
    'ServerDeployment'      = @(
        'Install-ServerRoles.ps1'
    );
}

# Initialize collections
$loadedModules = @()
$failedModules = @()
$allFunctions = @()

# Load modules
Write-Host "Loading IT Vedas PowerShell Modules..." -ForegroundColor Green

foreach ($moduleName in $modules.Keys) {
    $moduleFolderPath = Join-Path -Path $ModulePath -ChildPath $moduleName

    if (-not (Test-Path $moduleFolderPath)) {
        Write-Warning "Module folder not found: $moduleFolderPath"
        $failedModules += $moduleName
        continue
    }

    Write-Verbose "Loading module: $moduleName"

    foreach ($scriptFile in $modules[$moduleName]) {
        $scriptPath = Join-Path -Path $moduleFolderPath -ChildPath $scriptFile

        if (-not (Test-Path $scriptPath)) {
            Write-Warning "Script not found: $scriptPath"
            $failedModules += "$moduleName\$scriptFile"
            continue
        }

        if ($ValidateOnly) {
            # Validate PowerShell syntax
            try {
                $tokens = @()
                $errors = @()
                $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $scriptPath), [ref]$errors)

                if ($errors.Count -gt 0) {
                    Write-Error "Syntax error in $scriptFile : $($errors[0].Message)"
                    $failedModules += "$moduleName\$scriptFile"
                }
                else {
                    Write-Verbose "✓ $scriptFile"
                }
            }
            catch {
                Write-Error "Failed to validate $scriptFile : $_"
                $failedModules += "$moduleName\$scriptFile"
            }
        }
        else {
            # Load the script
            try {
                . $scriptPath
                $loadedModules += "$moduleName\$scriptFile"
                Write-Verbose "✓ Loaded: $scriptFile"

                # Extract function names from script
                $content = Get-Content $scriptPath -Raw
                $functionMatches = [regex]::Matches($content, 'function\s+(\w+)')
                foreach ($match in $functionMatches) {
                    $allFunctions += [PSCustomObject]@{
                        Module   = $moduleName
                        Function = $match.Groups[1].Value
                    }
                }
            }
            catch {
                Write-Error "Failed to load module $scriptFile : $_"
                $failedModules += "$moduleName\$scriptFile"
            }
        }
    }
}

# Display summary
if (-not $ValidateOnly) {
    Write-Host "`n=== Module Load Summary ===" -ForegroundColor Green
    Write-Host "Successfully loaded: $($loadedModules.Count) modules" -ForegroundColor Green

    if ($failedModules.Count -gt 0) {
        Write-Warning "Failed to load: $($failedModules.Count) modules"
        foreach ($failed in $failedModules) {
            Write-Warning "  - $failed"
        }
    }

    Write-Host "`nAvailable functions: $($allFunctions.Count)" -ForegroundColor Green

    # Display available functions if requested
    if ($ListFunctions) {
        Write-Host "`n=== Available Functions ===" -ForegroundColor Green
        $allFunctions | Format-Table -Property Module, Function -AutoSize

        Write-Host "`nUsage Examples:" -ForegroundColor Cyan
        Write-Host "  Get-Help <FunctionName> -Full       # Get detailed help"
        Write-Host "  <FunctionName> -?                   # Quick help"
        Write-Host "  Get-Command -Module *              # List all commands"
    }
}
else {
    Write-Host "Module validation complete" -ForegroundColor Green
    if ($failedModules.Count -eq 0) {
        Write-Host "All modules validated successfully" -ForegroundColor Green
    }
}

# Create global variables for module tracking
$global:ITVedasModulesLoaded = $loadedModules
$global:ITVedasModulesFailed = $failedModules
$global:ITVedasAvailableFunctions = $allFunctions

# Export summary function
function Get-ITVedasModuleInfo {
    <#
    .SYNOPSIS
        Display IT Vedas module information
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [ValidateSet('Summary', 'Functions', 'Loaded', 'Failed')]
        [string]$InformationType = 'Summary'
    )

    switch ($InformationType) {
        'Summary' {
            [PSCustomObject]@{
                ModulesLoaded          = $global:ITVedasModulesLoaded.Count
                ModulesFailed          = $global:ITVedasModulesFailed.Count
                AvailableFunctions    = $global:ITVedasAvailableFunctions.Count
                ModulePath             = $ModulePath
                LoadedTimestamp        = Get-Date
            }
        }
        'Functions' {
            $global:ITVedasAvailableFunctions | Format-Table -AutoSize
        }
        'Loaded' {
            $global:ITVedasModulesLoaded
        }
        'Failed' {
            $global:ITVedasModulesFailed
        }
    }
}

# Export the function
Export-ModuleMember -Function Get-ITVedasModuleInfo -Variable ITVedasModulesLoaded, ITVedasModulesFailed, ITVedasAvailableFunctions -ErrorAction SilentlyContinue

Write-Host "`nRun 'Get-ITVedasModuleInfo -InformationType Functions' to see all available functions" -ForegroundColor Cyan
