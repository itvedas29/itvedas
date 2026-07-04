<#
.SYNOPSIS
    Generate comprehensive server health and performance report.

.DESCRIPTION
    Collects system performance metrics including CPU, memory, disk, network,
    and event log information for comprehensive health analysis.

.PARAMETER ComputerName
    Computer to analyze. Default: localhost

.PARAMETER IncludeEventLogs
    Include event log analysis in report.

.PARAMETER IncludeServices
    Include service status analysis.

.PARAMETER ThresholdCPU
    CPU usage warning threshold (%). Default: 80

.PARAMETER ThresholdMemory
    Memory usage warning threshold (%). Default: 85

.PARAMETER ThresholdDisk
    Disk usage warning threshold (%). Default: 90

.PARAMETER OutputFormat
    Output format: 'Table', 'CSV', 'HTML', 'JSON'

.EXAMPLE
    Get-ServerHealthReport -ComputerName "Server1" -IncludeEventLogs -IncludeServices

.EXAMPLE
    Get-ServerHealthReport -ComputerName "Server1" -OutputFormat HTML | Out-File "C:\Reports\health.html"

.PREREQUISITES
    - WinRM enabled for remote access
    - Administrator permissions
#>

function Get-ServerHealthReport {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [string]$ComputerName = $env:COMPUTERNAME,

        [Parameter(Mandatory = $false)]
        [switch]$IncludeEventLogs,

        [Parameter(Mandatory = $false)]
        [switch]$IncludeServices,

        [Parameter(Mandatory = $false)]
        [ValidateRange(0, 100)]
        [int]$ThresholdCPU = 80,

        [Parameter(Mandatory = $false)]
        [ValidateRange(0, 100)]
        [int]$ThresholdMemory = 85,

        [Parameter(Mandatory = $false)]
        [ValidateRange(0, 100)]
        [int]$ThresholdDisk = 90,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table', 'CSV', 'HTML', 'JSON')]
        [string]$OutputFormat = 'Table'
    )

    begin {
        $report = @{}
        Write-Verbose "Starting server health analysis for: $ComputerName"
    }

    process {
        try {
            # Get system information
            $compInfo = Get-ComputerInfo -ComputerName $ComputerName -ErrorAction Stop

            # Get CPU information
            $cpuMetrics = Get-WmiObject -ComputerName $ComputerName -Class Win32_PerfFormattedData_PerfOS_Processor `
                -Filter "Name='_Total'" -ErrorAction Stop | Select-Object -First 1

            $cpuUsage = if ($cpuMetrics) { $cpuMetrics.PercentProcessorTime } else { 0 }

            # Get memory information
            $memInfo = Get-WmiObject -ComputerName $ComputerName -Class Win32_OperatingSystem -ErrorAction Stop
            $memUsagePercent = [math]::Round((($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / $memInfo.TotalVisibleMemorySize) * 100, 2)

            # Get disk information
            $diskInfo = Get-WmiObject -ComputerName $ComputerName -Class Win32_LogicalDisk -Filter "DriveType=3" -ErrorAction Stop
            $diskMetrics = @()
            foreach ($disk in $diskInfo) {
                $diskUsagePercent = [math]::Round(($disk.Size - $disk.FreeSpace) / $disk.Size * 100, 2)
                $diskMetrics += [PSCustomObject]@{
                    Drive       = $disk.Name
                    TotalGB     = [math]::Round($disk.Size / 1GB, 2)
                    FreeGB      = [math]::Round($disk.FreeSpace / 1GB, 2)
                    UsedGB      = [math]::Round(($disk.Size - $disk.FreeSpace) / 1GB, 2)
                    UsagePercent = $diskUsagePercent
                    Status      = if ($diskUsagePercent -ge $ThresholdDisk) { "WARNING" } else { "OK" }
                }
            }

            $report['SystemInfo'] = [PSCustomObject]@{
                ComputerName = $ComputerName
                OSVersion    = $compInfo.OSVersion
                SystemUptime = (Get-Date) - (Get-WmiObject -ComputerName $ComputerName -Class Win32_OperatingSystem).LastBootUpTime
                Timestamp    = Get-Date
            }

            $report['Performance'] = [PSCustomObject]@{
                CPUUsagePercent    = $cpuUsage
                CPUStatus         = if ($cpuUsage -ge $ThresholdCPU) { "WARNING" } else { "OK" }
                MemoryUsagePercent = $memUsagePercent
                MemoryStatus      = if ($memUsagePercent -ge $ThresholdMemory) { "WARNING" } else { "OK" }
                TotalMemoryMB     = [math]::Round($memInfo.TotalVisibleMemorySize / 1024, 2)
                AvailableMemoryMB = [math]::Round($memInfo.FreePhysicalMemory / 1024, 2)
            }

            $report['Disk'] = $diskMetrics

            # Get event log summary if requested
            if ($IncludeEventLogs) {
                $errorCount = (Get-EventLog -ComputerName $ComputerName -LogName System -EntryType Error -After (Get-Date).AddHours(-24) -ErrorAction SilentlyContinue | Measure-Object).Count
                $warningCount = (Get-EventLog -ComputerName $ComputerName -LogName System -EntryType Warning -After (Get-Date).AddHours(-24) -ErrorAction SilentlyContinue | Measure-Object).Count

                $report['EventLogs'] = [PSCustomObject]@{
                    ErrorsLast24Hours   = $errorCount
                    WarningsLast24Hours = $warningCount
                }
            }

            # Get service status if requested
            if ($IncludeServices) {
                $stoppedServices = Get-Service -ComputerName $ComputerName -ErrorAction Continue | Where-Object { $_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic' }

                $report['Services'] = [PSCustomObject]@{
                    TotalServices       = (Get-Service -ComputerName $ComputerName -ErrorAction SilentlyContinue | Measure-Object).Count
                    StoppedAutoServices = $stoppedServices.Count
                    StoppedServices     = $stoppedServices
                }
            }
        }
        catch {
            Write-Error "Error during health analysis: $_"
            return
        }
    }

    end {
        Write-Verbose "Server health analysis completed"

        # Format output
        switch ($OutputFormat) {
            'JSON' {
                return $report | ConvertTo-Json -Depth 10
            }
            'HTML' {
                $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Server Health Report - $ComputerName</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #666; margin-top: 20px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-left: 4px solid #4CAF50; }
        .metric.warning { border-left-color: #ff9800; }
        .metric.critical { border-left-color: #f44336; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Server Health Report: $ComputerName</h1>
        <p>Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>

        <h2>Performance Metrics</h2>
        <div class="metric">
            <strong>CPU Usage:</strong> $($report['Performance'].CPUUsagePercent)%
        </div>
        <div class="metric $(if ($report['Performance'].MemoryStatus -eq 'WARNING') {'warning'})">
            <strong>Memory Usage:</strong> $($report['Performance'].MemoryUsagePercent)%
        </div>
    </div>
</body>
</html>
"@
                return $html
            }
            'CSV' {
                return $report['Disk'] | ConvertTo-Csv -NoTypeInformation
            }
            default {
                return $report
            }
        }
    }
}

Export-ModuleMember -Function Get-ServerHealthReport
