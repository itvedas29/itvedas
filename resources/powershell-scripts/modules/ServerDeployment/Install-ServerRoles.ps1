<#
.SYNOPSIS
    Automate Windows Server role installation and configuration.

.DESCRIPTION
    Installs specified server roles with dependencies, configures features,
    and validates post-installation.

.PARAMETER Roles
    Array of roles to install (e.g., @('AD-Domain-Services', 'DHCP', 'DNS'))

.PARAMETER Features
    Additional Windows features to install.

.PARAMETER IncludeManagementTools
    Install management tools for roles.

.PARAMETER ValidateInstallation
    Run validation checks after installation.

.PARAMETER ComputerName
    Target computer. Default: localhost

.PARAMETER RestartIfRequired
    Restart server if required by installation.

.EXAMPLE
    Install-ServerRoles -Roles @('AD-Domain-Services', 'DNS') -IncludeManagementTools -ValidateInstallation

.EXAMPLE
    Install-ServerRoles -Roles @('DHCP') -ComputerName "Server1" -ValidateInstallation -RestartIfRequired

.PREREQUISITES
    - Administrator permissions
    - Windows Server 2012 R2 or later
#>

function Install-ServerRoles {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string[]]$Roles,

        [Parameter(Mandatory = $false)]
        [string[]]$Features,

        [Parameter(Mandatory = $false)]
        [switch]$IncludeManagementTools,

        [Parameter(Mandatory = $false)]
        [switch]$ValidateInstallation,

        [Parameter(Mandatory = $false)]
        [string]$ComputerName = "localhost",

        [Parameter(Mandatory = $false)]
        [switch]$RestartIfRequired
    )

    begin {
        $installResults = @()
        Write-Verbose "Starting server role installation"

        # Map roles to management tools
        $managementTools = @{
            'AD-Domain-Services'         = @('RSAT-AD-Tools')
            'DHCP'                       = @('RSAT-DHCP')
            'DNS'                        = @('RSAT-DNS-Server')
            'File-Services'              = @('RSAT-File-Services')
            'Print-Services'             = @('RSAT-Print-Server')
            'Web-Server'                 = @('Web-Mgmt-Console', 'Web-Mgmt-Compat')
            'Hyper-V'                    = @('RSAT-Hyper-V-Tools')
        }
    }

    process {
        try {
            # Install roles
            Write-Verbose "Installing roles: $($Roles -join ', ')"

            $roleInstallParams = @{
                Name                   = $Roles
                ComputerName          = $ComputerName
                IncludeAllSubFeature  = $true
                ErrorAction           = 'Stop'
            }

            if (-not $RestartIfRequired) {
                $roleInstallParams['NoRestart'] = $true
            }

            Install-WindowsFeature @roleInstallParams | ForEach-Object {
                $installResults += [PSCustomObject]@{
                    Name     = $_.Name
                    Type     = "Role"
                    Status   = if ($_.Success) { "Installed" } else { "Failed" }
                    Details  = $_.FeatureResult
                }
            }

            Write-Verbose "Role installation completed"

            # Install features
            if ($Features) {
                Write-Verbose "Installing features: $($Features -join ', ')"

                $featureInstallParams = @{
                    Name          = $Features
                    ComputerName  = $ComputerName
                    ErrorAction   = 'Stop'
                }

                if (-not $RestartIfRequired) {
                    $featureInstallParams['NoRestart'] = $true
                }

                Install-WindowsFeature @featureInstallParams | ForEach-Object {
                    $installResults += [PSCustomObject]@{
                        Name    = $_.Name
                        Type    = "Feature"
                        Status  = if ($_.Success) { "Installed" } else { "Failed" }
                        Details = $_.FeatureResult
                    }
                }

                Write-Verbose "Feature installation completed"
            }

            # Install management tools if requested
            if ($IncludeManagementTools) {
                Write-Verbose "Installing management tools"

                $toolsToInstall = @()
                foreach ($role in $Roles) {
                    if ($managementTools.ContainsKey($role)) {
                        $toolsToInstall += $managementTools[$role]
                    }
                }

                if ($toolsToInstall.Count -gt 0) {
                    Write-Verbose "Installing: $($toolsToInstall -join ', ')"

                    $toolsInstallParams = @{
                        Name          = $toolsToInstall
                        ComputerName  = $ComputerName
                        ErrorAction   = 'Continue'
                    }

                    if (-not $RestartIfRequired) {
                        $toolsInstallParams['NoRestart'] = $true
                    }

                    Install-WindowsFeature @toolsInstallParams | ForEach-Object {
                        $installResults += [PSCustomObject]@{
                            Name    = $_.Name
                            Type    = "Management Tool"
                            Status  = if ($_.Success) { "Installed" } else { "Failed" }
                            Details = $_.FeatureResult
                        }
                    }
                }
            }

            # Validate installation if requested
            if ($ValidateInstallation) {
                Write-Verbose "Validating installation"

                foreach ($role in $Roles) {
                    try {
                        $installedRole = Get-WindowsFeature -ComputerName $ComputerName `
                            -Name $role -ErrorAction Stop

                        if ($installedRole.Installed) {
                            Write-Verbose "Role validated: $role"
                        }
                        else {
                            Write-Warning "Role not installed: $role"
                        }
                    }
                    catch {
                        Write-Warning "Could not validate role $role : $_"
                    }
                }
            }
        }
        catch {
            Write-Error "Error during role installation: $_"
            return
        }
    }

    end {
        Write-Verbose "Server role installation process completed"

        $summary = [PSCustomObject]@{
            ComputerName         = $ComputerName
            RolesRequested       = $Roles.Count
            FeaturesRequested    = if ($Features) { $Features.Count } else { 0 }
            InstallationsAttempted = $installResults.Count
            SuccessfulInstalls   = ($installResults | Where-Object { $_.Status -eq "Installed" }).Count
            FailedInstalls       = ($installResults | Where-Object { $_.Status -eq "Failed" }).Count
            Details              = $installResults
        }

        return $summary
    }
}

Export-ModuleMember -Function Install-ServerRoles
