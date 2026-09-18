# Microsoft Configuration

## Prerequisites

Create an app registration in [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal.

## Authentication

Create a client secret for the app registration. Store the secret in an environment variable and note the Microsoft tenant ID and application client ID.

Application authentication is the recommended mode because it provides explicit,
repeatable permissions and complete cleanup semantics.

## Required Permissions

Grant the app registration these Microsoft Graph application permissions:

- `AdministrativeUnit.Read.All`: Read all administrative units.
- `Application.Read.All`: Read all applications.
- `Directory.Read.All`: Read directory data.
- `Group.Read.All`: Read all groups.
- `GroupMember.Read.All`: Read all group memberships.
- `User.Read.All`: Read all users' full profiles.

## Optional Permissions

Grant these application permissions when ingesting the indicated data:

- `DeviceManagementManagedDevices.Read.All`: Intune managed devices and detected apps.
- `DeviceManagementConfiguration.Read.All`: Intune device configuration and compliance policies.
- `RoleManagement.Read.Directory`: Entra directory role definitions and assignments.

## Configure Cartography

Provide these options:

- `--microsoft-tenant-id`: Microsoft tenant ID.
- `--microsoft-client-id`: App registration client ID.
- `--microsoft-client-secret-env-var`: Name of the environment variable containing the client secret.

These credentials apply to all Microsoft Graph ingestion in the `microsoft` module, including Entra ID and Intune.

The deprecated `--entra-tenant-id`, `--entra-client-id`, and `--entra-client-secret-env-var` aliases remain accepted until Cartography v1.0.0. Do not mix `--microsoft-*` and `--entra-*` credential flags in one invocation.

## Run Cartography

```bash
export MICROSOFT_CLIENT_SECRET='<client-secret>'
cartography \
  --selected-modules microsoft \
  --microsoft-tenant-id '<tenant-id>' \
  --microsoft-client-id '<client-id>' \
  --microsoft-client-secret-env-var MICROSOFT_CLIENT_SECRET
```

## Experimental delegated user authentication

Use delegated authentication only when an app registration is not available and
you need a best-effort snapshot of the Entra data visible to a human user. It is
not a replacement for application authentication:

- Only Entra datasets are attempted. Intune and O365 ingestion are skipped.
- Microsoft Graph may return partial results without an authorization error.
- A denied Entra dataset is logged and skipped while later datasets continue.
- Cleanup and derived federation analysis are disabled so partial visibility
  cannot delete existing graph data.
- The mode uses the local Azure CLI token cache and is intended for an attended,
  one-off run on a trusted workstation. Do not use it for hosted or unattended
  inventory collection.

Use a dedicated, non-privileged test user and a fresh disposable Neo4j database
when evaluating the mode. Sign in to the target tenant without requiring an Azure
subscription, then run Cartography:

```bash
az login --tenant '<tenant-id>' --allow-no-subscriptions

cartography \
  --selected-modules microsoft \
  --microsoft-tenant-id '<tenant-id>' \
  --microsoft-delegated-auth
```

Do not pass `--microsoft-client-id` or
`--microsoft-client-secret-env-var` with delegated authentication. A run that
reports no denied datasets can still be incomplete because results are limited
to the signed-in user's effective visibility.

## References

- [Microsoft Graph user](https://learn.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http)
- [Microsoft Graph administrative unit](https://learn.microsoft.com/en-us/graph/api/administrativeunit-get?view=graph-rest-1.0&tabs=http)
- [Microsoft Graph group](https://learn.microsoft.com/en-us/graph/api/group-get?view=graph-rest-1.0&tabs=http)
- [Microsoft Graph application](https://learn.microsoft.com/en-us/graph/api/application-get?view=graph-rest-1.0&tabs=http)
- [Microsoft Graph app role assignment](https://learn.microsoft.com/en-us/graph/api/resources/approleassignment)
- [Microsoft Graph service principal](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get?view=graph-rest-1.0&tabs=http)
- [Microsoft Graph directory role definition](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroledefinition)
- [Microsoft Graph directory role assignment](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroleassignment)
- [Intune managed device](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-manageddevice?view=graph-rest-1.0)
- [Intune detected app](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-detectedapp?view=graph-rest-1.0)
- [Intune device compliance policy](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-devicecompliancepolicy?view=graph-rest-1.0)
- [Microsoft Entra federation with AWS Identity Center](https://learn.microsoft.com/en-us/entra/identity/saas-apps/aws-single-sign-on-tutorial)
- [AWS Identity Center external identity provider setup](https://docs.aws.amazon.com/singlesignon/latest/userguide/idp-microsoft-entra.html)
