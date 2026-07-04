<#
.SYNOPSIS
    Create Active Directory security group structure for organizations.

.DESCRIPTION
    Automates the creation of standardized AD security group structures including distribution,
    security, and application groups with proper naming conventions.

.PARAMETER OrganizationName
    Name of the organization for group naming.

.PARAMETER ParentOU
    Parent OU where groups will be created.

.PARAMETER TemplateType
    Predefined templates: 'Standard', 'Enterprise', 'Custom'

.PARAMETER GroupsList
    Custom list of groups to create (PSCustomObject array).

.PARAMETER Scope
    Group scope: 'Global', 'Universal', 'DomainLocal'. Default: Global

.EXAMPLE
    New-ADSecurityGroupStructure -OrganizationName "HR" -ParentOU "OU=Groups,DC=contoso,DC=com"

.EXAMPLE
    New-ADSecurityGroupStructure -OrganizationName "Finance" -TemplateType "Enterprise" `
        -ParentOU "OU=Groups,DC=contoso,DC=com"

.PREREQUISITES
    - Active Directory PowerShell module
    - Domain Admin permissions
#>

function New-ADSecurityGroupStructure {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$OrganizationName,

        [Parameter(Mandatory = $true)]
        [string]$ParentOU,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Standard', 'Enterprise', 'Custom')]
        [string]$TemplateType = 'Standard',

        [Parameter(Mandatory = $false)]
        [PSObject[]]$GroupsList,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Global', 'Universal', 'DomainLocal')]
        [string]$Scope = 'Global'
    )

    begin {
        try {
            Import-Module ActiveDirectory -ErrorAction Stop
        }
        catch {
            throw "Failed to import Active Directory module: $_"
        }

        $createdGroups = @()
        $failedGroups = @()

        # Define group templates
        $groupTemplates = @{
            'Standard' = @(
                @{ Name = "GRP_$OrganizationName-Managers"; Description = "Managers in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-Staff"; Description = "Staff in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-External"; Description = "External users in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-ResourceAccess"; Description = "Resource access group for $OrganizationName" }
            );
            'Enterprise' = @(
                @{ Name = "GRP_$OrganizationName-Managers"; Description = "Managers in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-Staff"; Description = "Staff in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-External"; Description = "External users in $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-ResourceAccess"; Description = "Resource access group for $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-ApplicationAccess"; Description = "Application access group for $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-EmailDist"; Description = "Email distribution group for $OrganizationName" },
                @{ Name = "GRP_$OrganizationName-VPNAccess"; Description = "VPN access group for $OrganizationName" }
            )
        }
    }

    process {
        try {
            # Verify parent OU exists
            $ou = Get-ADOrganizationalUnit -Identity $ParentOU -ErrorAction Stop
            Write-Verbose "Parent OU verified: $($ou.DistinguishedName)"

            # Determine which groups to create
            $groupsToCreate = if ($TemplateType -eq 'Custom' -and $GroupsList) {
                $GroupsList
            }
            else {
                $groupTemplates[$TemplateType]
            }

            Write-Verbose "Creating $($groupsToCreate.Count) groups from $TemplateType template"

            foreach ($group in $groupsToCreate) {
                try {
                    # Check if group already exists
                    $existingGroup = Get-ADGroup -Filter { Name -eq $group.Name } -ErrorAction SilentlyContinue

                    if ($existingGroup) {
                        Write-Warning "Group already exists: $($group.Name)"
                        $failedGroups += [PSCustomObject]@{
                            GroupName = $group.Name
                            Status    = "Already Exists"
                            Error     = "Group already exists in domain"
                        }
                        continue
                    }

                    # Create the group
                    $newGroupParams = @{
                        Name              = $group.Name
                        SamAccountName    = $group.Name
                        GroupCategory    = 'Security'
                        GroupScope       = $Scope
                        DisplayName      = $group.Name
                        Description      = $group.Description
                        Path             = $ParentOU
                        ErrorAction      = 'Stop'
                    }

                    New-ADGroup @newGroupParams

                    Write-Verbose "Group created: $($group.Name)"
                    $createdGroups += [PSCustomObject]@{
                        GroupName   = $group.Name
                        Description = $group.Description
                        DistinguishedName = "CN=$($group.Name),$ParentOU"
                        Status      = "Created"
                    }
                }
                catch {
                    Write-Error "Failed to create group $($group.Name): $_"
                    $failedGroups += [PSCustomObject]@{
                        GroupName = $group.Name
                        Status    = "Failed"
                        Error     = $_.Exception.Message
                    }
                }
            }
        }
        catch {
            Write-Error "Error during group structure creation: $_"
            throw
        }
    }

    end {
        Write-Verbose "Group structure creation completed"
        Write-Verbose "Successfully created: $($createdGroups.Count) groups"
        Write-Verbose "Failed: $($failedGroups.Count) groups"

        return [PSCustomObject]@{
            CreatedGroups = $createdGroups
            FailedGroups  = $failedGroups
            Summary       = "Created: $($createdGroups.Count), Failed: $($failedGroups.Count)"
        }
    }
}

Export-ModuleMember -Function New-ADSecurityGroupStructure
