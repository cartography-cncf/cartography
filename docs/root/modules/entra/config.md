## Entra Configuration

To enable Entra data ingestion, you need to configure the following CLI settings:

- `--entra-tenant-id`: Your Entra tenant ID
- `--entra-client-id`: The client ID of your Entra application
- `--entra-client-secret-env-var`: The name of an environment variable that contains the client secret of your Entra application.


To set up the Entra client,

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal
1. Create a new app registration.
1. Grant it the following permissions:
    - `Group.Read.All`
        - Read all groups
        - Type: Application
    - `AdministrativeUnit.Read.All`
        - Read all administrative units
        - Type: Application
    - `Directory.Read.All`
        - Read directory data
        - Type: Application
    - `User.Read.All`
        - Read all users' full profiles
        - Type: Application
    - `GroupMember.Read.All`
        - Read all group memberships
        - Type: Application
    - `AppRoleAssignment.ReadWrite.All`
        - Manage app permission grants and app role assignments
        - Type: Application
    - `Application.Read.All`
        - Read all applications
        - Type: Application
    - `Directory.Read.All`
        - Read directory data
        - Type: Delegated
    - `Group.Read.All`
        - Read all groups
        - Type: Delegated
    - `GroupMember.Read.All`
        - Read group memberships
        - Type: Delegated
    - `User.Read`
        - Sign in and read user profile
        - Type: Delegated