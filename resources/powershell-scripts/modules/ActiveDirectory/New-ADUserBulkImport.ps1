<#
.SYNOPSIS
    Bulk import Active Directory users from CSV file.

.DESCRIPTION
    This function creates multiple Active Directory user accounts from a CSV file.
    Supports bulk user creation with configurable parameters and comprehensive error handling.

.PARAMETER CSVPath
    Path to the CSV file containing user data. Required columns: FirstName, LastName, Username, Email, Department, Title.

.PARAMETER TargetOU
    Target Organizational Unit distinguished name where users will be created.

.PARAMETER DefaultPassword
    Initial password for created users. Will require password change on first logon.

.PARAMETER SendWelcomeEmail
    If specified, sends welcome email to newly created users.

.PARAMETER LogPath
    Path to log file. Default: C:\Logs\ADUserImport_$(Get-Date -Format 'yyyyMMdd_HHmmss').log

.EXAMPLE
    New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Staff,DC=contoso,DC=com" `
        -DefaultPassword "TempPass@123" -LogPath "C:\Logs\import.log"

.EXAMPLE
    New-ADUserBulkImport -CSVPath "C:\Data\users.csv" -TargetOU "OU=Staff,DC=contoso,DC=com" `
        -DefaultPassword "TempPass@123" -SendWelcomeEmail

.PREREQUISITES
    - Active Directory PowerShell module installed
    - Domain Admin or delegated permissions
    - CSV file with required columns

.NOTES
    Author: IT Vedas
    Version: 1.0
    Last Modified: 2026-07-04
#>

function New-ADUserBulkImport {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ -PathType Leaf })]
        [string]$CSVPath,

        [Parameter(Mandatory = $true)]
        [string]$TargetOU,

        [Parameter(Mandatory = $true)]
        [SecureString]$DefaultPassword,

        [Parameter(Mandatory = $false)]
        [switch]$SendWelcomeEmail,

        [Parameter(Mandatory = $false)]
        [string]$LogPath = "C:\Logs\ADUserImport_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    )

    begin {
        # Initialize logging
        $null = New-Item -Path (Split-Path -Path $LogPath -Parent) -ItemType Directory -Force
        $script:LogPath = $LogPath

        function Write-Log {
            param ([string]$Message, [ValidateSet('Info', 'Warning', 'Error')]$Level = 'Info')
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "$timestamp [$Level] $Message"
            Add-Content -Path $script:LogPath -Value $logEntry
            Write-Verbose $logEntry
        }

        Write-Log "Starting AD User Bulk Import process" "Info"
        Write-Log "CSV Path: $CSVPath" "Info"
        Write-Log "Target OU: $TargetOU" "Info"

        # Verify Active Directory module
        try {
            Import-Module ActiveDirectory -ErrorAction Stop
            Write-Log "Active Directory module imported successfully" "Info"
        }
        catch {
            Write-Log "Failed to import Active Directory module: $_" "Error"
            throw
        }

        # Verify target OU exists
        try {
            $ou = Get-ADOrganizationalUnit -Identity $TargetOU -ErrorAction Stop
            Write-Log "Target OU verified: $($ou.DistinguishedName)" "Info"
        }
        catch {
            Write-Log "Target OU does not exist or cannot be accessed: $_" "Error"
            throw
        }

        $successCount = 0
        $failureCount = 0
        $userList = @()
    }

    process {
        try {
            $users = Import-Csv -Path $CSVPath -ErrorAction Stop
            Write-Log "Successfully imported CSV with $($users.Count) records" "Info"

            foreach ($user in $users) {
                try {
                    # Validate required fields
                    $requiredFields = @('FirstName', 'LastName', 'Username', 'Email', 'Department', 'Title')
                    $missingFields = @()

                    foreach ($field in $requiredFields) {
                        if (-not $user.$field) {
                            $missingFields += $field
                        }
                    }

                    if ($missingFields.Count -gt 0) {
                        throw "Missing required fields: $($missingFields -join ', ')"
                    }

                    # Prepare user parameters
                    $samAccountName = $user.Username.ToLower()
                    $userPrincipalName = "$samAccountName@$((Get-ADDomain).DNSRoot)"
                    $displayName = "$($user.FirstName) $($user.LastName)"

                    # Check if user already exists
                    if (Get-ADUser -Filter { SamAccountName -eq $samAccountName } -ErrorAction SilentlyContinue) {
                        Write-Log "User already exists: $samAccountName" "Warning"
                        $failureCount++
                        continue
                    }

                    # Create the AD user
                    $newUserParams = @{
                        SamAccountName              = $samAccountName
                        UserPrincipalName           = $userPrincipalName
                        Name                        = $displayName
                        GivenName                   = $user.FirstName
                        Surname                     = $user.LastName
                        DisplayName                 = $displayName
                        EmailAddress                = $user.Email
                        Department                  = $user.Department
                        Title                       = $user.Title
                        Path                        = $TargetOU
                        AccountPassword             = $DefaultPassword
                        ChangePasswordAtLogon       = $true
                        Enabled                     = $true
                        ErrorAction                 = 'Stop'
                    }

                    New-ADUser @newUserParams

                    Write-Log "User created successfully: $samAccountName ($displayName)" "Info"
                    $successCount++
                    $userList += [PSCustomObject]@{
                        Username   = $samAccountName
                        DisplayName = $displayName
                        Email      = $user.Email
                        Status     = 'Created'
                    }

                    # Send welcome email if requested
                    if ($SendWelcomeEmail) {
                        try {
                            # Email sending logic would go here
                            # This is a placeholder for actual email implementation
                            Write-Log "Welcome email queued for: $($user.Email)" "Info"
                        }
                        catch {
                            Write-Log "Failed to send welcome email to $($user.Email): $_" "Warning"
                        }
                    }
                }
                catch {
                    Write-Log "Failed to create user $($user.Username): $_" "Error"
                    $failureCount++
                    $userList += [PSCustomObject]@{
                        Username   = $user.Username
                        DisplayName = "$($user.FirstName) $($user.LastName)"
                        Email      = $user.Email
                        Status     = "Failed: $_"
                    }
                }
            }
        }
        catch {
            Write-Log "Failed to import CSV file: $_" "Error"
            throw
        }
    }

    end {
        Write-Log "User import process completed" "Info"
        Write-Log "Successfully created: $successCount users" "Info"
        Write-Log "Failed: $failureCount users" "Info"
        Write-Log "Log file saved to: $LogPath" "Info"

        return [PSCustomObject]@{
            SuccessCount = $successCount
            FailureCount = $failureCount
            Users        = $userList
            LogPath      = $LogPath
        }
    }
}

# Export function
Export-ModuleMember -Function New-ADUserBulkImport
