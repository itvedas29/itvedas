<#
.SYNOPSIS
    Create new DHCP scope with automated configuration.

.DESCRIPTION
    Creates DHCP scopes with standard settings including exclusion ranges, options,
    lease duration, and scope descriptions.

.PARAMETER ScopeName
    Descriptive name for the DHCP scope.

.PARAMETER StartRange
    Starting IP address for scope (e.g., "192.168.1.100").

.PARAMETER EndRange
    Ending IP address for scope (e.g., "192.168.1.200").

.PARAMETER SubnetMask
    Subnet mask for the scope.

.PARAMETER DefaultGateway
    Default gateway IP address.

.PARAMETER DNSServers
    Array of DNS server IP addresses.

.PARAMETER LeaseDuration
    Lease duration in days. Default: 8 days

.PARAMETER ExclusionRanges
    Array of IP ranges to exclude from scope.

.PARAMETER DHCPServer
    DHCP server name. Default: localhost

.EXAMPLE
    New-DHCPScopeWithSettings -ScopeName "Office-WiFi" -StartRange "192.168.1.100" `
        -EndRange "192.168.1.200" -SubnetMask "255.255.255.0" -DefaultGateway "192.168.1.1" `
        -DNSServers @("8.8.8.8", "8.8.4.4")

.PREREQUISITES
    - DHCP Server role installed
    - Administrator permissions
    - Server 2012 R2 or later
#>

function New-DHCPScopeWithSettings {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$ScopeName,

        [Parameter(Mandatory = $true)]
        [ValidatePattern('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')]
        [string]$StartRange,

        [Parameter(Mandatory = $true)]
        [ValidatePattern('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')]
        [string]$EndRange,

        [Parameter(Mandatory = $true)]
        [ValidatePattern('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')]
        [string]$SubnetMask,

        [Parameter(Mandatory = $true)]
        [ValidatePattern('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')]
        [string]$DefaultGateway,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string[]]$DNSServers,

        [Parameter(Mandatory = $false)]
        [ValidateRange(1, 365)]
        [int]$LeaseDuration = 8,

        [Parameter(Mandatory = $false)]
        [string[]]$ExclusionRanges,

        [Parameter(Mandatory = $false)]
        [string]$DHCPServer = "localhost"
    )

    begin {
        Write-Verbose "Starting DHCP scope creation for: $ScopeName"

        # Calculate network address
        $startIPArray = $StartRange.Split('.')
        $subnetMaskArray = $SubnetMask.Split('.')
        $networkAddress = @()

        for ($i = 0; $i -lt 4; $i++) {
            $networkAddress += [int]$startIPArray[$i] -band [int]$subnetMaskArray[$i]
        }

        $networkAddress = $networkAddress -join '.'
    }

    process {
        try {
            Write-Verbose "Creating DHCP scope with network: $networkAddress / $SubnetMask"

            # Create the scope
            Add-DhcpServerv4Scope -Name $ScopeName -StartRange $StartRange -EndRange $EndRange `
                -SubnetMask $SubnetMask -ComputerName $DHCPServer -State Active -ErrorAction Stop

            Write-Verbose "DHCP scope created: $ScopeName"

            # Set lease duration
            Set-DhcpServerv4Scope -ScopeId $networkAddress -LeaseDuration (New-TimeSpan -Days $LeaseDuration) `
                -ComputerName $DHCPServer -ErrorAction Stop

            Write-Verbose "Lease duration set to $LeaseDuration days"

            # Add exclusion ranges
            if ($ExclusionRanges) {
                foreach ($exclusionRange in $ExclusionRanges) {
                    try {
                        $rangeParts = $exclusionRange.Split('-')
                        if ($rangeParts.Count -eq 2) {
                            Add-DhcpServerv4ExclusionRange -ScopeId $networkAddress -StartRange $rangeParts[0] `
                                -EndRange $rangeParts[1] -ComputerName $DHCPServer -ErrorAction Stop

                            Write-Verbose "Added exclusion range: $exclusionRange"
                        }
                    }
                    catch {
                        Write-Warning "Failed to add exclusion range $exclusionRange : $_"
                    }
                }
            }

            # Set DHCP options
            # Option 3: Default Gateway
            Set-DhcpServerv4OptionValue -ScopeId $networkAddress -OptionId 3 -Value $DefaultGateway `
                -ComputerName $DHCPServer -ErrorAction Stop

            Write-Verbose "Set default gateway: $DefaultGateway"

            # Option 6: DNS Servers
            Set-DhcpServerv4OptionValue -ScopeId $networkAddress -OptionId 6 -Value $DNSServers `
                -ComputerName $DHCPServer -ErrorAction Stop

            Write-Verbose "Set DNS servers: $($DNSServers -join ', ')"

            # Option 15: DNS Domain Name
            $dnsDomain = (Get-ADDomain -ErrorAction SilentlyContinue).DNSRoot
            if ($dnsDomain) {
                Set-DhcpServerv4OptionValue -ScopeId $networkAddress -OptionId 15 -Value $dnsDomain `
                    -ComputerName $DHCPServer -ErrorAction Stop

                Write-Verbose "Set DNS domain: $dnsDomain"
            }

            # Get scope statistics
            $scope = Get-DhcpServerv4Scope -ScopeId $networkAddress -ComputerName $DHCPServer

            return [PSCustomObject]@{
                ScopeName         = $ScopeName
                NetworkAddress    = $networkAddress
                SubnetMask        = $SubnetMask
                StartRange        = $StartRange
                EndRange          = $EndRange
                DefaultGateway    = $DefaultGateway
                DNSServers        = $DNSServers -join '; '
                LeaseDuration     = "$LeaseDuration days"
                State             = $scope.State
                Status            = "Successfully Created"
                Timestamp         = Get-Date
            }
        }
        catch {
            Write-Error "Failed to create DHCP scope: $_"
            return [PSCustomObject]@{
                ScopeName = $ScopeName
                Status    = "Failed"
                Error     = $_.Exception.Message
            }
        }
    }

    end {
        Write-Verbose "DHCP scope creation process completed"
    }
}

Export-ModuleMember -Function New-DHCPScopeWithSettings
