<#
.SYNOPSIS
    Monitor DHCP lease usage and generate utilization reports.

.DESCRIPTION
    Monitors DHCP scope leases, tracks utilization percentages, identifies unused leases,
    and generates detailed reports.

.PARAMETER DHCPServer
    DHCP server name to monitor. Default: localhost

.PARAMETER ScopeFilter
    Filter specific scopes (optional).

.PARAMETER ThresholdWarning
    Warning threshold percentage. Default: 75

.PARAMETER ThresholdCritical
    Critical threshold percentage. Default: 90

.PARAMETER OutputFormat
    Output format: 'Table', 'CSV', 'HTML'. Default: Table

.EXAMPLE
    Monitor-DHCPLeases -DHCPServer "dhcp1.contoso.com"

.EXAMPLE
    Monitor-DHCPLeases -DHCPServer "dhcp1.contoso.com" -ThresholdWarning 80 -ThresholdCritical 95

.PREREQUISITES
    - DHCP Server role installed
    - Administrator permissions
#>

function Monitor-DHCPLeases {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [string]$DHCPServer = "localhost",

        [Parameter(Mandatory = $false)]
        [string]$ScopeFilter,

        [Parameter(Mandatory = $false)]
        [ValidateRange(0, 100)]
        [int]$ThresholdWarning = 75,

        [Parameter(Mandatory = $false)]
        [ValidateRange(0, 100)]
        [int]$ThresholdCritical = 90,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table', 'CSV', 'HTML')]
        [string]$OutputFormat = 'Table'
    )

    begin {
        $scopeReports = @()
        Write-Verbose "Starting DHCP lease monitoring on $DHCPServer"
    }

    process {
        try {
            # Get all scopes
            $scopes = Get-DhcpServerv4Scope -ComputerName $DHCPServer -ErrorAction Stop

            if ($ScopeFilter) {
                $scopes = $scopes | Where-Object { $_.Name -like "*$ScopeFilter*" }
            }

            Write-Verbose "Found $($scopes.Count) scope(s) to monitor"

            foreach ($scope in $scopes) {
                try {
                    $scopeId = $scope.ScopeId

                    # Get lease statistics
                    $stats = Get-DhcpServerv4ScopeStatistics -ScopeId $scopeId -ComputerName $DHCPServer `
                        -ErrorAction Stop

                    # Calculate utilization
                    $totalAddresses = $stats.AddressesInUse + $stats.AddressesFree
                    $utilizationPercent = if ($totalAddresses -gt 0) {
                        [math]::Round(($stats.AddressesInUse / $totalAddresses) * 100, 2)
                    }
                    else {
                        0
                    }

                    # Determine health status
                    $status = 'OK'
                    if ($utilizationPercent -ge $ThresholdCritical) {
                        $status = 'CRITICAL'
                    }
                    elseif ($utilizationPercent -ge $ThresholdWarning) {
                        $status = 'WARNING'
                    }

                    $report = [PSCustomObject]@{
                        ScopeName       = $scope.Name
                        ScopeId         = $scopeId
                        AddressesInUse  = $stats.AddressesInUse
                        AddressesFree   = $stats.AddressesFree
                        TotalAddresses  = $totalAddresses
                        Utilization     = "$utilizationPercent%"
                        Status          = $status
                        ReservedLeases  = $stats.ReservedAddresses
                        ExcludedLeases  = $stats.ExcludedAddresses
                        PendingLeases   = $stats.PendingOffers
                        Timestamp       = Get-Date
                    }

                    $scopeReports += $report

                    Write-Verbose "Scope: $($scope.Name) - Utilization: $utilizationPercent%"

                    # Display warning if threshold exceeded
                    if ($status -eq 'CRITICAL') {
                        Write-Warning "CRITICAL: Scope $($scope.Name) utilization is $utilizationPercent%"
                    }
                    elseif ($status -eq 'WARNING') {
                        Write-Warning "WARNING: Scope $($scope.Name) utilization is $utilizationPercent%"
                    }
                }
                catch {
                    Write-Error "Failed to get statistics for scope $scopeId : $_"
                }
            }
        }
        catch {
            Write-Error "Error during DHCP monitoring: $_"
            return
        }
    }

    end {
        Write-Verbose "DHCP lease monitoring completed"

        # Format output
        switch ($OutputFormat) {
            'HTML' {
                $html = $scopeReports | ConvertTo-Html -Fragment
                $htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>DHCP Lease Utilization Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .WARNING { background-color: #fff3cd; }
        .CRITICAL { background-color: #f8d7da; }
        .OK { background-color: #d4edda; }
    </style>
</head>
<body>
    <h1>DHCP Lease Utilization Report</h1>
    <p>Server: $DHCPServer | Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
    $html
</body>
</html>
"@
                return $htmlContent
            }
            'CSV' {
                return $scopeReports | ConvertTo-Csv -NoTypeInformation
            }
            default {
                return $scopeReports | Format-Table -AutoSize
            }
        }
    }
}

Export-ModuleMember -Function Monitor-DHCPLeases
