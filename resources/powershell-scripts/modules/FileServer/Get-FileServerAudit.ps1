<#
.SYNOPSIS
    Comprehensive file server permissions and usage audit.

.DESCRIPTION
    Audits file servers for permission configurations, large files, access patterns,
    and generates detailed reports.

.PARAMETER ServerPath
    File server path to audit (e.g., "\\fileserver\share").

.PARAMETER IncludeAccessTimes
    Include file access time information.

.PARAMETER ReportLargeFiles
    Report files larger than specified size (in MB).

.PARAMETER OutputFormat
    Output format: 'Table', 'CSV', 'JSON', 'HTML'

.EXAMPLE
    Get-FileServerAudit -ServerPath "\\fileserver\Finance" -IncludeAccessTimes -ReportLargeFiles 500

.EXAMPLE
    Get-FileServerAudit -ServerPath "\\fileserver\Archive" -OutputFormat CSV

.PREREQUISITES
    - Access to file server
    - Read permissions on target path
#>

function Get-FileServerAudit {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$ServerPath,

        [Parameter(Mandatory = $false)]
        [switch]$IncludeAccessTimes,

        [Parameter(Mandatory = $false)]
        [int]$ReportLargeFiles = 0,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table', 'CSV', 'JSON', 'HTML')]
        [string]$OutputFormat = 'Table'
    )

    begin {
        $auditResults = @()
        $statistics = @{
            TotalFiles      = 0
            TotalFolders    = 0
            TotalSizeBytes  = 0
            LargeFiles      = @()
            AccessSummary   = @{}
        }

        Write-Verbose "Starting file server audit for: $ServerPath"
    }

    process {
        try {
            # Get all items in directory
            $items = Get-ChildItem -Path $ServerPath -Recurse -Force -ErrorAction Continue

            foreach ($item in $items) {
                try {
                    # Get ACL information
                    $acl = Get-Acl -Path $item.FullName -ErrorAction Continue

                    if ($item.PSIsContainer) {
                        $statistics['TotalFolders']++
                        $size = 0
                    }
                    else {
                        $statistics['TotalFiles']++
                        $size = $item.Length
                        $statistics['TotalSizeBytes'] += $size

                        # Check if file is large
                        if ($ReportLargeFiles -gt 0 -and ($size / 1MB) -gt $ReportLargeFiles) {
                            $statistics['LargeFiles'] += [PSCustomObject]@{
                                Path = $item.FullName
                                Size = [math]::Round($size / 1MB, 2)
                            }
                        }
                    }

                    # Build audit entry
                    $auditEntry = [PSCustomObject]@{
                        Path        = $item.FullName
                        Name        = $item.Name
                        Type        = if ($item.PSIsContainer) { 'Folder' } else { 'File' }
                        Size        = [math]::Round($size / 1MB, 2)
                        Owner       = $acl.Owner
                        AccessRules = $acl.Access.Count
                        Created     = $item.CreationTime
                        Modified    = $item.LastWriteTime
                        Accessed    = if ($IncludeAccessTimes) { $item.LastAccessTime } else { 'N/A' }
                    }

                    $auditResults += $auditEntry

                    # Track access patterns
                    if ($IncludeAccessTimes) {
                        $accessedBy = $acl.Owner -split '\\' | Select-Object -Last 1
                        if ($statistics['AccessSummary'].ContainsKey($accessedBy)) {
                            $statistics['AccessSummary'][$accessedBy]++
                        }
                        else {
                            $statistics['AccessSummary'][$accessedBy] = 1
                        }
                    }
                }
                catch {
                    Write-Warning "Failed to audit item $($item.FullName): $_"
                }
            }

            Write-Verbose "Audit collected $($auditResults.Count) items"
        }
        catch {
            Write-Error "Error during audit: $_"
            return
        }
    }

    end {
        Write-Verbose "File server audit completed"

        $summaryReport = [PSCustomObject]@{
            ServerPath      = $ServerPath
            TotalFiles      = $statistics['TotalFolders']
            TotalFolders    = $statistics['TotalFolders']
            TotalSizeGB     = [math]::Round($statistics['TotalSizeBytes'] / 1GB, 2)
            LargeFilesCount = $statistics['LargeFiles'].Count
            AuditDate       = Get-Date
        }

        # Format output
        switch ($OutputFormat) {
            'JSON' {
                return @{
                    Summary    = $summaryReport
                    Details    = $auditResults
                    LargeFiles = $statistics['LargeFiles']
                } | ConvertTo-Json -Depth 10
            }
            'CSV' {
                return $auditResults | ConvertTo-Csv -NoTypeInformation
            }
            'HTML' {
                $html = $auditResults | ConvertTo-Html -Fragment
                return @"
<!DOCTYPE html>
<html>
<head>
    <title>File Server Audit Report</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
    </style>
</head>
<body>
    <h1>File Server Audit Report</h1>
    <div class="summary">
        <h3>Summary</h3>
        <p>Server Path: $($summaryReport.ServerPath)</p>
        <p>Total Files: $($summaryReport.TotalFiles) | Total Folders: $($summaryReport.TotalFolders)</p>
        <p>Total Size: $($summaryReport.TotalSizeGB) GB</p>
    </div>
    $html
</body>
</html>
"@
            }
            default {
                Write-Output "=== Audit Summary ==="
                Write-Output $summaryReport
                Write-Output ""
                Write-Output "=== Details ==="
                return $auditResults | Format-Table -AutoSize
            }
        }
    }
}

Export-ModuleMember -Function Get-FileServerAudit
