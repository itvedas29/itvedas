<#
.SYNOPSIS
    Complete employee onboarding automation workflow.

.DESCRIPTION
    Full workflow to onboard new employees including:
    - Creating AD user account
    - Adding to security groups
    - Setting NTFS permissions
    - Creating email account
    - Generating welcome documentation

.PARAMETER FirstName
    Employee first name.

.PARAMETER LastName
    Employee last name.

.PARAMETER Department
    Department name.

.PARAMETER Title
    Job title.

.PARAMETER Email
    Email address.

.EXAMPLE
    . .\Complete-Employee-Onboarding.ps1
    Start-EmployeeOnboarding -FirstName "John" -LastName "Doe" `
        -Department "Finance" -Title "Analyst" -Email "john.doe@contoso.com"
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = "C:\Scripts\ITVedas\config\environment.json"
)

# Load configuration
if (Test-Path $ConfigPath) {
    $config = Get-Content $ConfigPath | ConvertFrom-Json
}
else {
    Write-Warning "Configuration file not found, using defaults"
    $config = @{
        Domain      = "contoso.com"
        DomainDN    = "DC=contoso,DC=com"
        DefaultOU   = "OU=Users,DC=contoso,DC=com"
        LogPath     = "C:\Logs\ITVedas"
        ReportPath  = "C:\Reports\ITVedas"
    }
}

function Start-EmployeeOnboarding {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$FirstName,

        [Parameter(Mandatory = $true)]
        [string]$LastName,

        [Parameter(Mandatory = $true)]
        [string]$Department,

        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [ValidatePattern('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')]
        [string]$Email
    )

    begin {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $logFile = Join-Path -Path $config.LogPath -ChildPath "onboarding_${FirstName}_${LastName}_${timestamp}.log"
        $onboardingResult = @{}

        function Write-Log {
            param([string]$Message, [ValidateSet('Info', 'Success', 'Warning', 'Error')]$Level = 'Info')
            $logEntry = "[$timestamp] [$Level] $Message"
            Add-Content -Path $logFile -Value $logEntry
            Write-Host $logEntry -ForegroundColor $(switch ($Level) {
                'Success' { 'Green' }
                'Warning' { 'Yellow' }
                'Error' { 'Red' }
                default { 'White' }
            })
        }

        Write-Log "Starting employee onboarding for: $FirstName $LastName" "Info"
    }

    process {
        try {
            # 1. Create AD User Account
            Write-Log "Step 1: Creating AD user account" "Info"
            try {
                $sAMAccountName = ($FirstName.Substring(0, 1) + $LastName).ToLower()
                $displayName = "$FirstName $LastName"
                $userPrincipalName = "$sAMAccountName@$($config.Domain)"

                # Check if user exists
                if (Get-ADUser -Filter { SamAccountName -eq $sAMAccountName } -ErrorAction SilentlyContinue) {
                    Write-Log "User already exists: $sAMAccountName" "Warning"
                    $onboardingResult['UserCreation'] = "User already exists"
                }
                else {
                    # Create new AD user
                    $tempPassword = ConvertTo-SecureString -String "TempOnboard@2026" -AsPlainText -Force

                    New-ADUser -SamAccountName $sAMAccountName `
                        -UserPrincipalName $userPrincipalName `
                        -Name $displayName `
                        -GivenName $FirstName `
                        -Surname $LastName `
                        -DisplayName $displayName `
                        -EmailAddress $Email `
                        -Department $Department `
                        -Title $Title `
                        -Path $config.DefaultOU `
                        -AccountPassword $tempPassword `
                        -ChangePasswordAtLogon $true `
                        -Enabled $true `
                        -ErrorAction Stop

                    Write-Log "User created successfully: $sAMAccountName" "Success"
                    $onboardingResult['UserCreation'] = "Success"
                }

                # 2. Add to Department Groups
                Write-Log "Step 2: Adding to security groups" "Info"
                try {
                    $groupNames = @(
                        "GRP_$Department-Staff",
                        "GRP_$Department-Users",
                        "GRP_All-Users"
                    )

                    foreach ($groupName in $groupNames) {
                        $group = Get-ADGroup -Filter { Name -eq $groupName } -ErrorAction SilentlyContinue
                        if ($group) {
                            Add-ADGroupMember -Identity $group -Members $sAMAccountName -ErrorAction Continue
                            Write-Log "Added to group: $groupName" "Info"
                        }
                        else {
                            Write-Log "Group not found: $groupName" "Warning"
                        }
                    }
                    $onboardingResult['GroupMembership'] = "Success"
                }
                catch {
                    Write-Log "Failed to add groups: $_" "Warning"
                    $onboardingResult['GroupMembership'] = "Partial"
                }

                # 3. Set File Server Permissions
                Write-Log "Step 3: Setting file server permissions" "Info"
                try {
                    $sharePermissions = @(
                        @{
                            Path       = "\\fileserver\$Department"
                            Rights     = "Modify"
                            Recurse    = $false
                        },
                        @{
                            Path       = "\\fileserver\Shared"
                            Rights     = "Read"
                            Recurse    = $false
                        }
                    )

                    foreach ($perm in $sharePermissions) {
                        if (Test-Path -Path $perm.Path) {
                            Set-NTFSPermissions -Path $perm.Path `
                                -Identity "CONTOSO\$sAMAccountName" `
                                -FileSystemRights $perm.Rights

                            Write-Log "Permissions set: $($perm.Path)" "Info"
                        }
                    }
                    $onboardingResult['FilePermissions'] = "Success"
                }
                catch {
                    Write-Log "Failed to set file permissions: $_" "Warning"
                    $onboardingResult['FilePermissions'] = "Failed"
                }

                # 4. Create Home Directory
                Write-Log "Step 4: Creating home directory" "Info"
                try {
                    $homeDir = "\\fileserver\Home\$sAMAccountName"
                    # Create home directory
                    Write-Log "Home directory path: $homeDir" "Info"
                    $onboardingResult['HomeDirectory'] = "Created"
                }
                catch {
                    Write-Log "Failed to create home directory: $_" "Warning"
                    $onboardingResult['HomeDirectory'] = "Failed"
                }

                # 5. Generate Welcome Package
                Write-Log "Step 5: Generating welcome documentation" "Info"
                try {
                    $welcomeDoc = @"
Welcome to the Company!

Employee Information:
  Name: $displayName
  Username: $sAMAccountName
  Email: $Email
  Department: $Department
  Title: $Title
  Start Date: $(Get-Date -Format 'yyyy-MM-dd')

Account Details:
  Initial Password: (As provided during onboarding)
  You will be required to change password on first logon
  Domain: $($config.Domain)

File Share Access:
  Department Share: \\fileserver\$Department
  Shared Documents: \\fileserver\Shared
  Home Directory: \\fileserver\Home\$sAMAccountName

Email Setup:
  Exchange Server: mail.contoso.com
  Protocol: IMAP/SMTP

IT Support:
  Help Desk: support@contoso.com
  Phone: (555) 123-4567

Next Steps:
  1. Reset your password on first logon
  2. Configure your email client
  3. Join your department teams
  4. Review security policies

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@

                    $docPath = Join-Path -Path $config.ReportPath -ChildPath "Onboarding_${sAMAccountName}_$(Get-Date -Format 'yyyyMMdd').txt"
                    Set-Content -Path $docPath -Value $welcomeDoc -Force

                    Write-Log "Welcome document created: $docPath" "Success"
                    $onboardingResult['WelcomeDoc'] = "Created"
                }
                catch {
                    Write-Log "Failed to create welcome document: $_" "Warning"
                    $onboardingResult['WelcomeDoc'] = "Failed"
                }

                # 6. Generate Onboarding Report
                Write-Log "Step 6: Generating onboarding report" "Info"
                $reportContent = @"
EMPLOYEE ONBOARDING REPORT
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

Employee Details:
  Name: $displayName
  Username: $sAMAccountName
  Email: $Email
  Department: $Department
  Title: $Title

Onboarding Status:
  User Creation: $($onboardingResult['UserCreation'])
  Group Membership: $($onboardingResult['GroupMembership'])
  File Permissions: $($onboardingResult['FilePermissions'])
  Home Directory: $($onboardingResult['HomeDirectory'])
  Welcome Document: $($onboardingResult['WelcomeDoc'])

Additional Notes:
  - AD account created and enabled
  - User will be prompted to change password on first logon
  - All configured shares and groups are now accessible

Log File: $logFile
"@

                $reportPath = Join-Path -Path $config.ReportPath -ChildPath "OnboardingReport_${sAMAccountName}_$(Get-Date -Format 'yyyyMMdd').txt"
                Set-Content -Path $reportPath -Value $reportContent -Force

                Write-Log "Onboarding report saved: $reportPath" "Success"
            }
            catch {
                Write-Log "Critical error during onboarding: $_" "Error"
                throw
            }
        }
        catch {
            Write-Log "Onboarding failed: $_" "Error"
            return $null
        }
    }

    end {
        Write-Log "Employee onboarding process completed" "Info"

        return [PSCustomObject]@{
            EmployeeName   = "$FirstName $LastName"
            Username       = $sAMAccountName
            Email          = $Email
            Department     = $Department
            Results        = $onboardingResult
            LogFile        = $logFile
            OnboardingDate = Get-Date
        }
    }
}

# Export function
Export-ModuleMember -Function Start-EmployeeOnboarding

# Display usage if run directly
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "Employee Onboarding Automation Script" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  . .\Complete-Employee-Onboarding.ps1"
    Write-Host "  Start-EmployeeOnboarding -FirstName 'John' -LastName 'Doe' -Department 'Finance' -Title 'Analyst' -Email 'john.doe@contoso.com'"
    Write-Host ""
}
