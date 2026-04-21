## Microsoft Configuration

The `microsoft` module ingests both Entra ID and Intune data through Microsoft Graph using a single Service Principal. Configure it with the following CLI settings:

- `--entra-tenant-id`: Your Entra tenant ID
- `--entra-client-id`: The client ID of your Entra application
- `--entra-client-secret-env-var`: The name of an environment variable that contains the client secret of your Entra application.
- `--entra-cloud`: (optional) Microsoft sovereign cloud to target. One of:
    - `commercial` (default) — `graph.microsoft.com` / `login.microsoftonline.com`
    - `usgov` — GCC High / L4 (`graph.microsoft.us` / `login.microsoftonline.us`)
    - `usgov-dod` — DoD / L5 (`dod-graph.microsoft.us` / `login.microsoftonline.us`)
    - `china` — 21Vianet (`microsoftgraph.chinacloudapi.cn` / `login.chinacloudapi.cn`)

Endpoints are those published in the Microsoft Graph [deployments reference](https://learn.microsoft.com/en-us/graph/deployments). The CLI flags are named `--entra-*` for backwards compatibility — they apply to both the Entra and Intune submodules.

To set up the Service Principal:

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal (or the equivalent portal for your sovereign cloud).
1. Create a new app registration.
1. Grant it the following Microsoft Graph application permissions:
    - `AdministrativeUnit.Read.All` — Read all administrative units
    - `AppRoleAssignment.ReadWrite.All` — Manage app permission grants and app role assignments
    - `Application.Read.All` — Read all applications
    - `Directory.Read.All` — Read directory data
    - `Group.Read.All` — Read all groups
    - `GroupMember.Read.All` — Read all group memberships
    - `User.Read.All` — Read all users' full profiles
    - `DeviceManagementManagedDevices.Read.All` — Required for Intune managed devices and detected apps
    - `DeviceManagementConfiguration.Read.All` — Required for Intune compliance policies
