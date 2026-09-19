# Microsoft Configuration

## Prerequisites

Create an app registration in [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal.

## Authentication

Create a client secret for the app registration. Store the secret in an environment variable and note the Microsoft tenant ID and application client ID.

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

Defender for Endpoint is enabled separately with `--microsoft-defender`. Grant
admin consent for both of these **application** permissions on the same app:

| API | Permission | Data |
| --- | --- | --- |
| WindowsDefenderATP | `Machine.Read.All` | Defender for Endpoint machine inventory |
| Microsoft Graph | `SecurityAlert.Read.All` | Unresolved Defender for Endpoint alerts |

The tenant must have Defender for Endpoint provisioned. The connector uses the
commercial cloud endpoints and does not support sovereign cloud endpoints.
Machine tokens use `https://api.securitycenter.microsoft.com/.default`, as required
by Microsoft even though requests go to `https://api.security.microsoft.com`.
Alert tokens use `https://graph.microsoft.com/.default`. Both are obtained through
the existing Microsoft service principal credential. No write API permissions are
required.

## Configure Cartography

Provide these options:

- `--microsoft-tenant-id`: Microsoft tenant ID.
- `--microsoft-client-id`: App registration client ID.
- `--microsoft-client-secret-env-var`: Name of the environment variable containing the client secret.
- `--microsoft-defender`: Opt in to Defender for Endpoint machine and unresolved-alert ingestion; disabled by default.

These credentials apply to all ingestion in the `microsoft` module, including
Entra ID, Intune, and optional Defender for Endpoint ingestion.

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

Add `--microsoft-defender` to the command above to include Defender. Machine
inventory requests use pages of up to 10,000 records; Microsoft documents limits
of 100 machine requests per minute and 1,500 per hour. Alerts use Graph
`/v1.0/security/alerts_v2` with
`serviceSource eq 'microsoftDefenderForEndpoint' and status ne 'resolved'`, pages
of 100, and `@odata.nextLink` pagination. Requests retry HTTP 429 and transient 5xx
responses up to five times and honor `Retry-After`.

## Troubleshooting

When Defender is enabled, an authorization error, exhausted retry, malformed page,
or incomplete pagination aborts its sync before graph writes or cleanup. Previous
Defender data is preserved. Verify both application permissions and their admin
consent for 403 errors. Microsoft documents 404 for machine queries with no recent
machines; this connector conservatively treats that response as an error, preserving
the previous inventory. A successful empty collection is eligible for cleanup.

## References

- [Defender for Endpoint machine list](https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines)
- [Defender for Endpoint machine properties](https://learn.microsoft.com/en-us/defender-endpoint/api/machine)
- [Defender app-only authentication and token audience](https://learn.microsoft.com/en-us/defender-endpoint/api/exposed-apis-create-app-webapp)
- [Microsoft Graph security alerts v2 list, permissions, filters, and pagination](https://learn.microsoft.com/en-us/graph/api/security-list-alerts_v2?view=graph-rest-1.0)
- [Microsoft Graph device evidence and Defender device IDs](https://learn.microsoft.com/en-us/graph/api/resources/security-deviceevidence?view=graph-rest-1.0)

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
