<#
.SYNOPSIS
    Create and schedule automated backup jobs.

.DESCRIPTION
    Automates creation of scheduled backup tasks with configurable retention,
    notification, and recovery options.

.PARAMETER BackupName
    Descriptive name for the backup job.

.PARAMETER SourcePath
    Source path or volume to backup.

.PARAMETER DestinationPath
    Destination path for backups.

.PARAMETER ScheduleType
    Schedule: 'Daily', 'Weekly', 'Monthly'. Default: Daily

.PARAMETER RetentionDays
    Number of days to retain backups. Default: 30

.PARAMETER CompressionEnabled
    Enable backup compression.

.PARAMETER NotificationEmail
    Email address for notifications.

.EXAMPLE
    New-AutomatedBackup -BackupName "FileServer-Daily" -SourcePath "D:\Shares" `
        -DestinationPath "E:\Backups" -ScheduleType Daily -RetentionDays 30

.PREREQUISITES
    - Windows Server with backup capabilities
    - Administrator permissions
    - Sufficient disk space at destination
#>

function New-AutomatedBackup {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$BackupName,

        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$SourcePath,

        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$DestinationPath,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Daily', 'Weekly', 'Monthly')]
        [string]$ScheduleType = 'Daily',

        [Parameter(Mandatory = $false)]
        [ValidateRange(1, 365)]
        [int]$RetentionDays = 30,

        [Parameter(Mandatory = $false)]
        [switch]$CompressionEnabled,

        [Parameter(Mandatory = $false)]
        [ValidatePattern('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')]
        [string]$NotificationEmail
    )

    begin {
        Write-Verbose "Starting automated backup configuration for: $BackupName"

        # Create backup directory structure
        $backupDir = Join-Path -Path $DestinationPath -ChildPath $BackupName
        if (-not (Test-Path $backupDir)) {
            $null = New-Item -Path $backupDir -ItemType Directory -Force
            Write-Verbose "Created backup directory: $backupDir"
        }

        # Determine schedule times
        $scheduleTime = @{
            'Daily'   = 2, 0  # 2:00 AM daily
            'Weekly'  = 2, 0  # 2:00 AM on Monday
            'Monthly' = 2, 0  # 2:00 AM on 1st of month
        }
    }

    process {
        try {
            # Create backup script
            $backupScript = @"
# Automated Backup Script for $BackupName
# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

`$SourcePath = '$SourcePath'
`$DestinationPath = '$backupDir'
`$BackupName = '$BackupName'
`$CompressionEnabled = `$$($CompressionEnabled.IsPresent)
`$RetentionDays = $RetentionDays

# Create timestamped backup
`$BackupDate = Get-Date -Format 'yyyyMMdd_HHmmss'
`$BackupPath = Join-Path -Path `$DestinationPath -ChildPath "Backup_`$BackupDate"

Write-Host "Starting backup: `$BackupName at `$(Get-Date)"

# Create backup directory
`$null = New-Item -Path `$BackupPath -ItemType Directory -Force

# Copy files
try {
    Copy-Item -Path `$SourcePath -Destination `$BackupPath -Recurse -Force -ErrorAction Stop
    Write-Host "Backup completed: `$BackupPath"
}
catch {
    Write-Error "Backup failed: `$_"
    exit 1
}

# Apply compression if enabled
if (`$CompressionEnabled) {
    try {
        `$zipPath = "`$BackupPath.zip"
        Compress-Archive -Path `$BackupPath -DestinationPath `$zipPath -Force
        Remove-Item -Path `$BackupPath -Recurse -Force
        Write-Host "Backup compressed: `$zipPath"
    }
    catch {
        Write-Warning "Compression failed: `$_"
    }
}

# Clean up old backups
`$oldBackups = Get-ChildItem -Path `$DestinationPath -Directory | `
    Where-Object { `$_.CreationTime -lt (Get-Date).AddDays(-`$RetentionDays) }

foreach (`$backup in `$oldBackups) {
    try {
        Remove-Item -Path `$backup.FullName -Recurse -Force
        Write-Host "Deleted old backup: `$(`$backup.Name)"
    }
    catch {
        Write-Warning "Failed to delete old backup `$(`$backup.Name): `$_"
    }
}

Write-Host "Backup process completed at `$(Get-Date)"
"@

            # Save script to file
            $scriptPath = Join-Path -Path $backupDir -ChildPath "backup_script.ps1"
            Set-Content -Path $scriptPath -Value $backupScript -Force
            Write-Verbose "Backup script saved to: $scriptPath"

            # Create scheduled task
            $taskName = "Backup_$BackupName"
            $action = New-ScheduledTaskAction -Execute "powershell.exe" `
                -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""

            # Set trigger based on schedule type
            $trigger = switch ($ScheduleType) {
                'Daily' {
                    New-ScheduledTaskTrigger -Daily -At "02:00"
                }
                'Weekly' {
                    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "02:00"
                }
                'Monthly' {
                    New-ScheduledTaskTrigger -Monthly -Day 1 -At "02:00"
                }
            }

            # Create task settings
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                -DontStopIfGoingOnBatteries -RunWithHighestPrivileges

            # Register the task
            Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
                -Settings $settings -Force -ErrorAction Stop

            Write-Verbose "Scheduled task created: $taskName"

            return [PSCustomObject]@{
                BackupName        = $BackupName
                SourcePath        = $SourcePath
                DestinationPath   = $backupDir
                ScheduleType      = $ScheduleType
                RetentionDays     = $RetentionDays
                CompressionEnabled = $CompressionEnabled.IsPresent
                TaskName          = $taskName
                ScriptPath        = $scriptPath
                Status            = "Successfully Configured"
                Timestamp         = Get-Date
            }
        }
        catch {
            Write-Error "Failed to create automated backup: $_"
            return [PSCustomObject]@{
                BackupName = $BackupName
                Status     = "Failed"
                Error      = $_.Exception.Message
            }
        }
    }

    end {
        Write-Verbose "Automated backup configuration completed"
    }
}

Export-ModuleMember -Function New-AutomatedBackup
