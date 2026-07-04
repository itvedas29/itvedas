<#
.SYNOPSIS
    Create a new DNS zone with automated record creation.

.DESCRIPTION
    Automates DNS zone creation and populates it with standard DNS records
    (A, CNAME, MX, TXT, SRV records).

.PARAMETER ZoneName
    Name of the DNS zone to create (e.g., "contoso.com").

.PARAMETER DNSServer
    DNS server where zone will be created. Default: localhost

.PARAMETER ZoneType
    Zone type: 'Primary', 'Secondary', 'Stub'. Default: Primary

.PARAMETER RecordsCSV
    Path to CSV file containing records to create.

.PARAMETER AllowTransfer
    Specify secondary DNS servers for zone transfers.

.PARAMETER CreateStandardRecords
    Create standard records (A, MX, TXT, SOA).

.EXAMPLE
    New-DNSZoneWithRecords -ZoneName "contoso.com" -CreateStandardRecords

.EXAMPLE
    New-DNSZoneWithRecords -ZoneName "contoso.com" -RecordsCSV "C:\DNS\records.csv" `
        -AllowTransfer @("192.168.1.20", "192.168.1.21")

.PREREQUISITES
    - DNS Server role installed
    - Administrator permissions
#>

function New-DNSZoneWithRecords {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$ZoneName,

        [Parameter(Mandatory = $false)]
        [string]$DNSServer = "localhost",

        [Parameter(Mandatory = $false)]
        [ValidateSet('Primary', 'Secondary', 'Stub')]
        [string]$ZoneType = 'Primary',

        [Parameter(Mandatory = $false)]
        [ValidateScript({ if ($_ -and -not (Test-Path $_)) { throw "File not found: $_" } else { $true } })]
        [string]$RecordsCSV,

        [Parameter(Mandatory = $false)]
        [string[]]$AllowTransfer,

        [Parameter(Mandatory = $false)]
        [switch]$CreateStandardRecords
    )

    begin {
        $createdZone = $null
        $createdRecords = @()
        $failedRecords = @()

        Write-Verbose "Starting DNS zone creation process for zone: $ZoneName"
    }

    process {
        try {
            # Create the zone
            Write-Verbose "Creating $ZoneType DNS zone: $ZoneName"

            $zoneParams = @{
                Name       = $ZoneName
                ComputerName = $DNSServer
                ZoneType   = $ZoneType
                ErrorAction = 'Stop'
            }

            if ($AllowTransfer) {
                $zoneParams['SecondaryServers'] = $AllowTransfer
            }

            $createdZone = Add-DnsServerPrimaryZone @zoneParams

            Write-Verbose "Zone created successfully: $ZoneName"

            # Create standard records if requested
            if ($CreateStandardRecords) {
                try {
                    # Create A record for zone apex
                    Add-DnsServerResourceRecordA -ZoneName $ZoneName -Name "@" -IPv4Address "192.168.1.10" `
                        -ComputerName $DNSServer -ErrorAction Stop

                    Write-Verbose "Created A record for zone apex"

                    # Create MX record
                    Add-DnsServerResourceRecordMX -ZoneName $ZoneName -MailExchange "mail.$ZoneName" `
                        -Preference 10 -ComputerName $DNSServer -ErrorAction Stop

                    Write-Verbose "Created MX record"

                    # Create TXT record for SPF
                    Add-DnsServerResourceRecordTxt -ZoneName $ZoneName -Name "@" -DescriptiveText "v=spf1 mx -all" `
                        -ComputerName $DNSServer -ErrorAction Stop

                    Write-Verbose "Created TXT/SPF record"

                    $createdRecords += @(
                        [PSCustomObject]@{ Type = 'A'; Name = '@'; Value = '192.168.1.10'; Status = 'Created' },
                        [PSCustomObject]@{ Type = 'MX'; Name = '@'; Value = "mail.$ZoneName"; Status = 'Created' },
                        [PSCustomObject]@{ Type = 'TXT'; Name = '@'; Value = 'v=spf1 mx -all'; Status = 'Created' }
                    )
                }
                catch {
                    Write-Error "Error creating standard records: $_"
                }
            }

            # Import records from CSV if provided
            if ($RecordsCSV -and (Test-Path $RecordsCSV)) {
                try {
                    $records = Import-Csv -Path $RecordsCSV -ErrorAction Stop

                    foreach ($record in $records) {
                        try {
                            $recordParams = @{
                                ZoneName = $ZoneName
                                Name     = $record.Name
                                ComputerName = $DNSServer
                                ErrorAction = 'Stop'
                            }

                            switch ($record.Type) {
                                'A' {
                                    $recordParams['IPv4Address'] = $record.Value
                                    Add-DnsServerResourceRecordA @recordParams
                                }
                                'AAAA' {
                                    $recordParams['IPv6Address'] = $record.Value
                                    Add-DnsServerResourceRecordAAAA @recordParams
                                }
                                'CNAME' {
                                    $recordParams['CanonicalName'] = $record.Value
                                    Add-DnsServerResourceRecordCName @recordParams
                                }
                                'MX' {
                                    $recordParams['MailExchange'] = $record.Value
                                    $recordParams['Preference'] = [int]$record.Preference
                                    Add-DnsServerResourceRecordMX @recordParams
                                }
                                'TXT' {
                                    $recordParams['DescriptiveText'] = $record.Value
                                    Add-DnsServerResourceRecordTxt @recordParams
                                }
                            }

                            Write-Verbose "Created $($record.Type) record: $($record.Name)"
                            $createdRecords += [PSCustomObject]@{
                                Type   = $record.Type
                                Name   = $record.Name
                                Value  = $record.Value
                                Status = 'Created'
                            }
                        }
                        catch {
                            Write-Error "Failed to create record $($record.Name): $_"
                            $failedRecords += [PSCustomObject]@{
                                Type   = $record.Type
                                Name   = $record.Name
                                Value  = $record.Value
                                Status = "Failed: $_"
                            }
                        }
                    }
                }
                catch {
                    Write-Error "Error importing records from CSV: $_"
                }
            }
        }
        catch {
            Write-Error "Error during DNS zone creation: $_"
            throw
        }
    }

    end {
        Write-Verbose "DNS zone creation process completed"

        return [PSCustomObject]@{
            ZoneName       = $ZoneName
            ZoneCreated    = $null -ne $createdZone
            RecordsCreated = $createdRecords.Count
            RecordsFailed  = $failedRecords.Count
            Records        = $createdRecords
            FailedRecords  = $failedRecords
        }
    }
}

Export-ModuleMember -Function New-DNSZoneWithRecords
