## Microsoft Configuration

Follow these steps to analyze Microsoft tenant data with Cartography.

The `microsoft` module uses Microsoft Graph and currently ingests:

- **Entra ID** — users, groups, administrative units, applications, service
  principals, app role assignments, and AWS Identity Center federation edges
- **Intune** — managed devices, detected apps, and compliance policies

Configure the module with these CLI settings:

- `--entra-tenant-id`: Your Entra tenant ID
- `--entra-client-id`: The client ID of your Entra application
- `--entra-client-secret-env-var`: The name of an environment variable that
  contains the client secret of your Entra application

To set up the Microsoft Graph client:

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
   in the Azure portal.
1. Create a new app registration.
1. Grant it the following **application** permissions:
    - `AdministrativeUnit.Read.All`
        - Read all administrative units
        - Required for: Entra administrative units
    - `AppRoleAssignment.ReadWrite.All`
        - Manage app permission grants and app role assignments
        - Required for: Entra app role assignments
    - `Application.Read.All`
        - Read all applications
        - Required for: Entra applications
    - `Directory.Read.All`
        - Read directory data
        - Required for: tenant-level Entra resources
    - `Group.Read.All`
        - Read all groups
        - Required for: Entra groups
    - `GroupMember.Read.All`
        - Read all group memberships
        - Required for: Entra group memberships
    - `User.Read.All`
        - Read all users' full profiles
        - Required for: Entra users
    - `DeviceManagementManagedDevices.Read.All`
        - Read Microsoft Intune managed devices and detected apps
        - Required for: Intune managed devices and detected apps
    - `DeviceManagementConfiguration.Read.All`
        - Read Microsoft Intune device configuration and compliance policies
        - Required for: Intune compliance policies

The legacy `entra` module name continues to use the same credentials, but new
documentation and module selection should use `microsoft`.
