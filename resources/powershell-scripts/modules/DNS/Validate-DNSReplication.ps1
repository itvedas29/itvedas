<#
.SYNOPSIS
    Validate DNS zone replication across multiple DNS servers.

.DESCRIPTION
    Checks DNS zone replication status, detects inconsistencies, and generates
    detailed replication reports with diagnostic information.

.PARAMETER ZoneName
    DNS zone name to validate.

.PARAMETER DNSServers
    Array of DNS servers to check replication against.

.PARAMETER SerialNumberCheck
    Verify SOA serial numbers are consistent.

.PARAMETER RecordCountCheck
    Verify record counts match across servers.

.PARAMETER OutputFormat
    Output format: 'Table', 'CSV', 'JSON'. Default: Table

.EXAMPLE
    Validate-DNSReplication -ZoneName "contoso.com" -DNSServers @("192.168.1.10", "192.168.1.20")

.EXAMPLE
    Validate-DNSReplication -ZoneName "contoso.com" -DNSServers @("dns1.contoso.com", "dns2.contoso.com") `
        -SerialNumberCheck -RecordCountCheck -OutputFormat CSV

.PREREQUISITES
    - DNS Server cmdlets
    - Network connectivity to all DNS servers
#>

function Validate-DNSReplication {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$ZoneName,

        [Parameter(Mandatory = $true)]
        [string[]]$DNSServers,

        [Parameter(Mandatory = $false)]
        [switch]$SerialNumberCheck,

        [Parameter(Mandatory = $false)]
        [switch]$RecordCountCheck,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table', 'CSV', 'JSON')]
        [string]$OutputFormat = 'Table'
    )

    begin {
        $replicationResults = @()
        $inconsistencies = @()

        Write-Verbose "Starting DNS replication validation for zone: $ZoneName"
    }

    process {
        try {
            foreach ($server in $DNSServers) {
                try {
                    Write-Verbose "Checking server: $server"

                    # Get zone information
                    $zone = Get-DnsServerZone -Name $ZoneName -ComputerName $server -ErrorAction Stop

                    # Get SOA record
                    $soaRecord = Get-DnsServerResourceRecord -ZoneName $ZoneName -Name "@" `
                        -RRType SOA -ComputerName $server -ErrorAction Stop

                    # Get all records in zone
                    $allRecords = Get-DnsServerResourceRecord -ZoneName $ZoneName `
                        -ComputerName $server -ErrorAction Stop

                    # Get zone statistics
                    $statistics = Get-DnsServerZoneStatistics -Name $ZoneName `
                        -ComputerName $server -ErrorAction Stop

                    $result = [PSCustomObject]@{
                        Server           = $server
                        ZoneName         = $ZoneName
                        ZoneType         = $zone.ZoneType
                        IsDsIntegrated   = $zone.IsDsIntegrated
                        SOASerialNumber  = $soaRecord.RecordData.SerialNumber
                        RecordCount      = $allRecords.Count
                        MasterServers    = ($zone.MasterServers -join '; ')
                        LastReplication  = $statistics.LastReplicationTime
                        Status           = 'OK'
                        Timestamp        = Get-Date
                    }

                    $replicationResults += $result
                    Write-Verbose "Successfully retrieved zone data from $server"
                }
                catch {
                    Write-Error "Failed to connect to server $server : $_"
                    $replicationResults += [PSCustomObject]@{
                        Server      = $server
                        ZoneName    = $ZoneName
                        Status      = "Error: $_"
                        Timestamp   = Get-Date
                    }
                }
            }

            # Validate consistency if multiple servers
            if ($replicationResults.Count -gt 1) {
                Write-Verbose "Validating replication consistency"

                if ($SerialNumberCheck) {
                    $firstSerial = ($replicationResults | Where-Object { $_.SOASerialNumber } | Select-Object -First 1).SOASerialNumber
                    foreach ($result in $replicationResults) {
                        if ($result.SOASerialNumber -and $result.SOASerialNumber -ne $firstSerial) {
                            $inconsistencies += [PSCustomObject]@{
                                Server   = $result.Server
                                Issue    = "SOA Serial Mismatch"
                                Expected = $firstSerial
                                Actual   = $result.SOASerialNumber
                                Severity = "High"
                            }
                        }
                    }
                }

                if ($RecordCountCheck) {
                    $firstCount = ($replicationResults | Where-Object { $_.RecordCount } | Select-Object -First 1).RecordCount
                    foreach ($result in $replicationResults) {
                        if ($result.RecordCount -and $result.RecordCount -ne $firstCount) {
                            $inconsistencies += [PSCustomObject]@{
                                Server   = $result.Server
                                Issue    = "Record Count Mismatch"
                                Expected = $firstCount
                                Actual   = $result.RecordCount
                                Severity = "Medium"
                            }
                        }
                    }
                }
            }
        }
        catch {
            Write-Error "Error during replication validation: $_"
        }
    }

    end {
        Write-Verbose "DNS replication validation completed"

        # Format output
        switch ($OutputFormat) {
            'JSON' {
                return @{
                    ReplicationResults = $replicationResults
                    Inconsistencies    = $inconsistencies
                } | ConvertTo-Json -Depth 10
            }
            'CSV' {
                return $replicationResults | ConvertTo-Csv -NoTypeInformation
            }
            default {
                if ($inconsistencies.Count -gt 0) {
                    Write-Warning "Replication inconsistencies detected:"
                    Write-Output $inconsistencies | Format-Table -AutoSize
                }
                return $replicationResults
            }
        }
    }
}

Export-ModuleMember -Function Validate-DNSReplication
