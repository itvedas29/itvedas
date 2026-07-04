<#
.SYNOPSIS
    Automate NTFS permission assignment and auditing.

.DESCRIPTION
    Sets, modifies, and audits NTFS permissions on files and folders with comprehensive
    error handling and logging.

.PARAMETER Path
    File or folder path for permission modification.

.PARAMETER Identity
    User or group identity (e.g., "CONTOSO\Finance-Team").

.PARAMETER AccessType
    Access type: 'Allow' or 'Deny'. Default: Allow

.PARAMETER FileSystemRights
    Rights to assign: 'FullControl', 'Modify', 'Read', 'Write', 'ReadAndExecute', 'ListDirectory'.

.PARAMETER Scope
    Inheritance scope: 'This Folder Only', 'SubFolders Only', 'Files Only', 'This Folder, Subfolders and Files'.

.PARAMETER IsInherited
    Enable inheritance. Default: $true

.PARAMETER Recursive
    Apply permissions recursively to subfolders.

.EXAMPLE
    Set-NTFSPermissions -Path "D:\Shares\Finance" -Identity "CONTOSO\Finance-Team" `
        -FileSystemRights "Modify" -Recursive

.EXAMPLE
    Set-NTFSPermissions -Path "D:\Shares\Reports" -Identity "CONTOSO\Everyone" `
        -FileSystemRights "Read" -Scope "This Folder, Subfolders and Files"

.PREREQUISITES
    - Administrator permissions
    - NTFSSecurity or similar module installed (optional, uses native cmdlets)
#>

function Set-NTFSPermissions {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Identity,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Allow', 'Deny')]
        [string]$AccessType = 'Allow',

        [Parameter(Mandatory = $true)]
        [ValidateSet('FullControl', 'Modify', 'Read', 'Write', 'ReadAndExecute', 'ListDirectory')]
        [string]$FileSystemRights,

        [Parameter(Mandatory = $false)]
        [ValidateSet('This Folder Only', 'SubFolders Only', 'Files Only', 'This Folder, Subfolders and Files')]
        [string]$Scope = 'This Folder, Subfolders and Files',

        [Parameter(Mandatory = $false)]
        [bool]$IsInherited = $true,

        [Parameter(Mandatory = $false)]
        [switch]$Recursive
    )

    begin {
        Write-Verbose "Starting NTFS permission configuration for: $Path"

        # Verify path exists
        if (-not (Test-Path $Path)) {
            throw "Path does not exist: $Path"
        }

        # Validate identity exists
        try {
            $ntAccount = New-Object System.Security.Principal.NTAccount($Identity)
            $sid = $ntAccount.Translate([System.Security.Principal.SecurityIdentifier])
            Write-Verbose "Identity verified: $Identity"
        }
        catch {
            throw "Invalid identity: $Identity. Error: $_"
        }
    }

    process {
        try {
            # Get current ACL
            $acl = Get-Acl -Path $Path -ErrorAction Stop
            Write-Verbose "Current ACL retrieved for: $Path"

            # Map scope to inheritance flags
            $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::None
            $propagationFlags = [System.Security.AccessControl.PropagationFlags]::None

            switch ($Scope) {
                'This Folder Only' {
                    $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::None
                    $propagationFlags = [System.Security.AccessControl.PropagationFlags]::None
                }
                'SubFolders Only' {
                    $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit
                    $propagationFlags = [System.Security.AccessControl.PropagationFlags]::InheritOnly
                }
                'Files Only' {
                    $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
                    $propagationFlags = [System.Security.AccessControl.PropagationFlags]::InheritOnly
                }
                'This Folder, Subfolders and Files' {
                    $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
                    $propagationFlags = [System.Security.AccessControl.PropagationFlags]::None
                }
            }

            # Map file system rights
            $rights = [System.Security.AccessControl.FileSystemRights]::$FileSystemRights

            # Create access rule
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $ntAccount,
                $rights,
                $inheritanceFlags,
                $propagationFlags,
                $AccessType
            )

            # Add rule to ACL
            $acl.AddAccessRule($accessRule)
            Write-Verbose "Access rule created: $Identity - $FileSystemRights - $AccessType"

            # Set ACL
            Set-Acl -Path $Path -AclObject $acl -ErrorAction Stop
            Write-Verbose "ACL applied to: $Path"

            # Apply recursively if requested
            if ($Recursive -and (Get-Item $Path).PSIsContainer) {
                Write-Verbose "Applying permissions recursively to subfolders"
                Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                    try {
                        $childAcl = Get-Acl -Path $_.FullName
                        $childAcl.AddAccessRule($accessRule)
                        Set-Acl -Path $_.FullName -AclObject $childAcl
                    }
                    catch {
                        Write-Warning "Failed to apply permissions to $($_.FullName): $_"
                    }
                }
            }

            return [PSCustomObject]@{
                Path            = $Path
                Identity        = $Identity
                AccessType      = $AccessType
                Rights          = $FileSystemRights
                Scope           = $Scope
                Recursive       = $Recursive.IsPresent
                Status          = "Successfully Applied"
                Timestamp       = Get-Date
            }
        }
        catch {
            Write-Error "Failed to set NTFS permissions: $_"
            return [PSCustomObject]@{
                Path   = $Path
                Status = "Failed"
                Error  = $_.Exception.Message
            }
        }
    }

    end {
        Write-Verbose "NTFS permission configuration completed"
    }
}

Export-ModuleMember -Function Set-NTFSPermissions
