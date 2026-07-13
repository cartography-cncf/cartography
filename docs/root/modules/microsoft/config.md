## Microsoft Configuration

To enable Microsoft data ingestion, configure the following CLI settings:

- `--microsoft-tenant-id`: Your Microsoft tenant ID
- `--microsoft-client-id`: The client ID of your Microsoft application
- `--microsoft-client-secret-env-var`: The name of an environment variable that contains the client secret of your Microsoft application

These credentials are used for Microsoft Graph ingestion across the `microsoft` module, including Entra ID identity data and Intune data.

The legacy `--entra-tenant-id`, `--entra-client-id`, and `--entra-client-secret-env-var` flags are still accepted as deprecated aliases until Cartography v1.0.0. Do not mix `--microsoft-*` and `--entra-*` credential flags in the same invocation.

To set up the Microsoft client:

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal.
1. Create a new app registration.
1. Grant it the following permissions:
    - `AdministrativeUnit.Read.All`
        - Read all administrative units
        - Type: Application
    - `Application.Read.All`
        - Read all applications
        - Type: Application
    - `Directory.Read.All`
        - Read directory data
        - Type: Application
    - `Group.Read.All`
        - Read all groups
        - Type: Application
    - `GroupMember.Read.All`
        - Read all group memberships
        - Type: Application
    - `User.Read.All`
        - Read all users' full profiles
        - Type: Application
    - `DeviceManagementManagedDevices.Read.All`
        - Read Microsoft Intune managed devices and detected apps
        - Type: Application
        - Required for: Intune managed devices and detected apps
    - `DeviceManagementConfiguration.Read.All`
        - Read Microsoft Intune device configuration and compliance policies
        - Type: Application
        - Required for: Intune compliance policies
    - `RoleManagement.Read.Directory`
        - Read directory role definitions and assignments
        - Type: Application
        - Required for: Entra directory role definitions and assignments
