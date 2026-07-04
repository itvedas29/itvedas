<#
.SYNOPSIS
    Resolve Active Directory account lockouts.

.DESCRIPTION
    Unlocks locked-out AD accounts and optionally resets passwords. Includes diagnostic information
    about lockout causes and can generate lockout reports.

.PARAMETER Username
    Username of the locked-out account.

.PARAMETER UnlockOnly
    Unlock the account without resetting password.

.PARAMETER ResetPassword
    Generate new temporary password.

.PARAMETER TemporaryPassword
    Custom temporary password (if not provided, generates one).

.EXAMPLE
    Resolve-ADAccountLockout -Username "jsmith"

.EXAMPLE
    Resolve-ADAccountLockout -Username "jsmith" -UnlockOnly

.EXAMPLE
    Resolve-ADAccountLockout -Username "jsmith" -ResetPassword -TemporaryPassword "NewPass@123"

.PREREQUISITES
    - Active Directory PowerShell module
    - Account Operator or higher permissions
#>

function Resolve-ADAccountLockout {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Username,

        [Parameter(Mandatory = $false)]
        [switch]$UnlockOnly,

        [Parameter(Mandatory = $false)]
        [switch]$ResetPassword,

        [Parameter(Mandatory = $false)]
        [SecureString]$TemporaryPassword
    )

    begin {
        try {
            Import-Module ActiveDirectory -ErrorAction Stop
        }
        catch {
            throw "Failed to import Active Directory module: $_"
        }
    }

    process {
        foreach ($user in $Username) {
            try {
                # Get the user object
                $adUser = Get-ADUser -Identity $user -Properties LockedOut, LastBadPasswordAttempt, `
                    AccountLockoutTime, BadPwdCount -ErrorAction Stop

                Write-Verbose "Processing user: $($adUser.SamAccountName)"

                # Collect current state
                $currentState = [PSCustomObject]@{
                    Username              = $adUser.SamAccountName
                    IsLockedOut           = $adUser.LockedOut
                    LastBadPasswordAttempt = $adUser.LastBadPasswordAttempt
                    AccountLockoutTime    = $adUser.AccountLockoutTime
                    BadPasswordCount      = $adUser.BadPwdCount
                    DistinguishedName     = $adUser.DistinguishedName
                }

                if (-not $adUser.LockedOut) {
                    Write-Warning "User $user is not currently locked out"
                    return $currentState
                }

                # Unlock the account
                Unlock-ADAccount -Identity $adUser -ErrorAction Stop
                Write-Verbose "Account unlocked: $user"

                # Reset password if requested
                if ($ResetPassword) {
                    if (-not $TemporaryPassword) {
                        # Generate random password
                        $randomPassword = -join ((33..126) | Get-Random -Count 16 | ForEach-Object { [char]$_ })
                        $TemporaryPassword = ConvertTo-SecureString -String $randomPassword -AsPlainText -Force
                    }

                    Set-ADAccountPassword -Identity $adUser -NewPassword $TemporaryPassword `
                        -Reset -ErrorAction Stop

                    # Force password change on next logon
                    Set-ADUser -Identity $adUser -ChangePasswordAtLogon $true -ErrorAction Stop

                    Write-Verbose "Password reset for user: $user"
                }

                # Verify unlock
                $updatedUser = Get-ADUser -Identity $adUser -Properties LockedOut, BadPwdCount

                $result = [PSCustomObject]@{
                    Username           = $adUser.SamAccountName
                    UnlockSuccessful   = -not $updatedUser.LockedOut
                    PreviousLockoutTime = $currentState.AccountLockoutTime
                    BadPasswordCount   = $updatedUser.BadPwdCount
                    PasswordReset      = $ResetPassword.IsPresent
                    Timestamp          = Get-Date
                }

                Write-Verbose "Account successfully unlocked: $user"
                return $result
            }
            catch {
                Write-Error "Failed to resolve lockout for user $user : $_"
                return $null
            }
        }
    }

    end {
        Write-Verbose "Lockout resolution process completed"
    }
}

Export-ModuleMember -Function Resolve-ADAccountLockout
