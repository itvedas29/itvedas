<#
.SYNOPSIS
    Audit Active Directory user permissions and group membership.

.DESCRIPTION
    Generates comprehensive permission audit reports for AD users including group memberships,
    nested groups, and security group analysis.

.PARAMETER Username
    Single username to audit. If not provided, audits all domain users.

.PARAMETER DepartmentFilter
    Filter users by specific department.

.PARAMETER OutputFormat
    Output format: 'Table', 'CSV', or 'HTML'. Default: Table

.PARAMETER OutputPath
    Path to save report. If not specified, returns to pipeline.

.PARAMETER IncludeNested
    Include nested group membership analysis.

.EXAMPLE
    Get-ADUserPermissionAudit -Username "jsmith"

.EXAMPLE
    Get-ADUserPermissionAudit -DepartmentFilter "Finance" -OutputFormat "CSV" -OutputPath "C:\Reports\Finance_Audit.csv"

.EXAMPLE
    Get-ADUserPermissionAudit -Username "jsmith" -IncludeNested | Format-Table -AutoSize

.PREREQUISITES
    - Active Directory PowerShell module installed
    - Domain Admin or delegated read permissions
#>

function Get-ADUserPermissionAudit {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [string]$Username,

        [Parameter(Mandatory = $false)]
        [string]$DepartmentFilter,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table', 'CSV', 'HTML')]
        [string]$OutputFormat = 'Table',

        [Parameter(Mandatory = $false)]
        [string]$OutputPath,

        [Parameter(Mandatory = $false)]
        [switch]$IncludeNested
    )

    begin {
        try {
            Import-Module ActiveDirectory -ErrorAction Stop
        }
        catch {
            throw "Failed to import Active Directory module: $_"
        }

        $auditResults = @()
    }

    process {
        try {
            # Get users to audit
            $filter = "Enabled -eq `$true"
            if ($Username) {
                $filter += " -and SamAccountName -like '$Username'"
            }
            if ($DepartmentFilter) {
                $filter += " -and Department -like '$DepartmentFilter'"
            }

            $users = Get-ADUser -Filter $filter -Properties Department, Mail, Title, MemberOf -ErrorAction Stop

            foreach ($user in $users) {
                $groups = Get-ADGroup -Filter { member -RecursiveMatch $user.DistinguishedName } `
                    -Properties Description -ErrorAction SilentlyContinue

                $directGroups = $user.MemberOf | ForEach-Object {
                    Get-ADGroup -Identity $_ -ErrorAction SilentlyContinue
                }

                $auditEntry = [PSCustomObject]@{
                    Username       = $user.SamAccountName
                    DisplayName    = $user.Name
                    Email          = $user.Mail
                    Department     = $user.Department
                    Title          = $user.Title
                    Enabled        = $user.Enabled
                    DirectGroups   = $directGroups.Count
                    AllGroups      = $groups.Count
                    Groups         = ($groups.Name -join '; ')
                    CreatedDate    = $user.Created
                    LastLogon      = $user.LastLogonDate
                    PasswordExpires = ([datetime]::FromFileTime((Get-ADUser -Identity $user -Properties pwdLastSet).pwdLastSet)).AddDays(90)
                }

                $auditResults += $auditEntry
            }

            Write-Verbose "Audited $($auditResults.Count) user(s)"
        }
        catch {
            Write-Error "Error during audit: $_"
            return
        }
    }

    end {
        # Output results based on format
        switch ($OutputFormat) {
            'CSV' {
                if ($OutputPath) {
                    $auditResults | Export-Csv -Path $OutputPath -NoTypeInformation -Force
                    Write-Verbose "Report saved to: $OutputPath"
                    return "Report saved to: $OutputPath"
                }
                else {
                    return $auditResults | ConvertTo-Csv -NoTypeInformation
                }
            }
            'HTML' {
                if ($OutputPath) {
                    $html = $auditResults | ConvertTo-Html -Fragment
                    @"
<!DOCTYPE html>
<html>
<head>
    <title>AD User Permission Audit Report</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Active Directory User Permission Audit Report</h1>
    <p>Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
    $html
</body>
</html>
"@ | Set-Content -Path $OutputPath -Force
                    Write-Verbose "HTML report saved to: $OutputPath"
                    return "Report saved to: $OutputPath"
                }
            }
            default {
                return $auditResults
            }
        }
    }
}

Export-ModuleMember -Function Get-ADUserPermissionAudit
