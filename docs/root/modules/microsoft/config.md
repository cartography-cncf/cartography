# Microsoft configuration

## Prerequisites

Create an app registration in [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal.

## Authentication

Create a client secret for the app registration. Store the secret in an environment variable and note the Microsoft tenant ID and application client ID.

Application authentication is the recommended mode because it provides explicit,
repeatable permissions and complete cleanup semantics.

## Required permissions

Grant the app registration these Microsoft Graph application permissions:

- `AdministrativeUnit.Read.All`: Read all administrative units.
- `Application.Read.All`: Read all applications.
- `Directory.Read.All`: Read directory data.
- `Group.Read.All`: Read all groups.
- `GroupMember.Read.All`: Read all group memberships.
- `User.Read.All`: Read all users' full profiles.

## Optional permissions

Grant these application permissions when ingesting the indicated data:

- `DeviceManagementManagedDevices.Read.All`: Intune managed devices and detected apps.
- `DeviceManagementConfiguration.Read.All`: Intune device configuration and compliance policies.
- `RoleManagement.Read.Directory`: Entra directory role definitions and assignments.
- `AuditLog.Read.All`: Entra user sign-in activity; also requires an Entra ID P1 or P2 license.

### User sign-in activity

Cartography requests `signInActivity` with the existing user inventory query,
using pages of up to 500 users and no per-user requests. If the first request
returns `403 Forbidden`, it logs a warning and retries the inventory without
activity. Failure of that retry or any later page still propagates and prevents
cleanup. A successful fallback preserves previously collected activity timestamps
and sets `sign_in_activity_available` to false. It still refreshes basic user
inventory and allows its normal cleanup. Missing activity on an individual user
also preserves old timestamps; new users without activity have null timestamps.

The three activity properties on `EntraUser` are native UTC datetimes:

- `last_successful_sign_in_date_time`: last successful interactive **or non-interactive** sign-in. Use this for inactivity queries.
- `last_sign_in_date_time`: last interactive attempt, including failures.
- `last_non_interactive_sign_in_date_time`: last non-interactive attempt, including failures.

For example, find enabled accounts with a known successful sign-in older than
90 days:

```cypher
MATCH (u:EntraUser)
WHERE u.account_enabled = true
  AND u.sign_in_activity_available = true
  AND u.last_successful_sign_in_date_time < datetime() - duration('P90D')
RETURN u.user_principal_name, u.last_successful_sign_in_date_time
ORDER BY u.last_successful_sign_in_date_time
```

Null means unknown, not proof that an account has never signed in. Microsoft
does not backfill `lastSuccessfulSignInDateTime` before December 1, 2023.
These timestamps measure sign-in recency, not usage frequency or active human
use; background clients can produce successful non-interactive sign-ins.

See Microsoft's [signInActivity reference](https://learn.microsoft.com/en-us/graph/api/resources/signinactivity?view=graph-rest-1.0)
and [inactive-account guidance](https://learn.microsoft.com/en-us/entra/identity/monitoring-health/howto-manage-inactive-user-accounts).

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

Use delegated authentication only when you can't use an app registration and
you need a best-effort snapshot of the Entra data visible to a signed-in user.
Delegated authentication doesn't grant the user additional Microsoft Graph
permissions. It isn't a replacement for application authentication.

### Limitations

- Only Entra datasets are attempted. Intune and O365 ingestion are skipped.
- Microsoft Graph may return partial results without an authorization error.
- If Microsoft Graph returns `403 Forbidden`, Cartography stops the affected
  dataset, reports it, and continues with the next dataset. After attempting all
  datasets, Cartography exits with a nonzero status so automation can't mistake
  the partial inventory for a complete sync. Records from earlier pages of the
  affected dataset can remain in the graph.
- Because the command exits with a nonzero status after a denied dataset, run
  delegated Microsoft ingestion separately from other selected modules.
- If Microsoft Graph returns `401 Unauthorized`, or an error other than `403`,
  Cartography stops the run.
- Cartography disables cleanup and derived federation analysis. A delegated run
  doesn't delete existing Entra data, so records that the user can't see can
  remain in the graph.
- Cartography reads the local Azure CLI token cache. Use this mode only for an
  attended, one-time run on a trusted workstation. Don't use it for hosted or
  unattended inventory collection.

A run that reports no denied datasets can still be incomplete. Microsoft Graph
can filter results based on the signed-in user's effective visibility without
returning `403 Forbidden`.

### Sign in and run Cartography

Use a dedicated, non-privileged test user and a fresh disposable Neo4j database
when you evaluate this mode.

1. Sign in to the target tenant. You don't need an Azure subscription.

   ```bash
   az login --tenant '<TENANT_ID>' --allow-no-subscriptions
   ```

   If a browser can't open in your environment, add `--use-device-code`. Your
   tenant's Conditional Access policy might not allow device-code authentication.

2. Run Cartography.

   ```bash
   cartography \
     --selected-modules microsoft \
     --microsoft-tenant-id '<TENANT_ID>' \
     --microsoft-delegated-auth
   ```

Do not pass `--microsoft-client-id` or
`--microsoft-client-secret-env-var` with delegated authentication.

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
