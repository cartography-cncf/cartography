# Azure Configuration

## Authentication

Cartography supports Azure CLI authentication, service principal
authentication, and access token authentication.

### Azure CLI

Azure CLI authentication is the default. Sign in before running Cartography:

```bash
az login
```

Cartography uses the active Azure CLI identity. Always set either
`--azure-subscription-id` or `--azure-sync-all-subscriptions` to select the
subscriptions to sync explicitly.

### Service principal

Create a service principal for Cartography:

```bash
az login
az ad sp create-for-rbac --name cartography --role Reader
```

Store the returned `tenant`, `appId`, and `password` values in environment
variables such as `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and
`AZURE_CLIENT_SECRET`.

### Access token

Access token authentication runs the sync with a pre-issued Azure Resource
Manager (ARM) access token, typically a signed-in user's delegated token. It
needs no service principal and no Azure CLI session in the environment that
runs Cartography, which suits directories where only delegated (user) sign-in
is allowed.

The token must be issued for ARM (`https://management.azure.com`). A Microsoft
Graph token is rejected: ARM and Graph are separate audiences, and a token for
one is never accepted by the other.

To mint one from a signed-in Azure CLI session:

```bash
az login
export AZURE_ACCESS_TOKEN="$(az account get-access-token \
  --resource https://management.azure.com \
  --query accessToken --output tsv)"
```

To mint one from your own app registration instead (for example, a
delegated sign-in flow in another tool):

1. In **App registrations > your app > API permissions**, add the delegated
   permission **Azure Service Management > `user_impersonation`**. It is the
   only delegated permission ARM exposes.
2. Grant consent for it: either the signed-in user consents on first sign-in,
   or an administrator selects **Grant admin consent** where user consent is
   restricted.
3. Request the token for the scope
   `https://management.azure.com/user_impersonation` (or
   `https://management.azure.com/.default`). Request it separately from any
   Microsoft Graph token.

Limitations:

- The token cannot be refreshed, and the sync fails once it expires. ARM access
  tokens typically last 60 to 90 minutes; Cartography logs the remaining
  lifetime when the sync starts. Mint the token immediately before the run, and
  use a service principal for subscriptions that take longer to sync.
- The token only reaches ARM. Key Vault secrets, keys, and certificates, and
  Synapse pipelines and linked services, are served by separate data-plane
  audiences, so they are not synced and a warning is logged. Existing Key Vault
  contents in the graph are left in place; Synapse pipelines and linked
  services are treated as empty, as with any identity that cannot read them.
  Key vaults and Synapse workspaces themselves still sync.
- Coverage is limited to what the token's identity can read through its Azure
  RBAC role assignments, exactly as with any other identity.

## Required Permissions

Grant the authenticated identity the built-in Azure
[Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader)
on every subscription that Cartography should sync.

To ingest the management group hierarchy and subscription placement, also
grant a management-group-scoped read role such as `Management Group Reader`.
Assign it at the tenant root management group or another scope broad enough to
cover the management groups that Cartography should sync.

## Configure Cartography

- Omit `--azure-sp-auth` to use the active Azure CLI session.
- Set `--azure-sp-auth` to use the tenant ID, client ID, and client secret
  options.
- Set `--azure-access-token-env-var` to the name of an environment variable
  holding an ARM access token. It cannot be combined with `--azure-sp-auth`.
- Set `--azure-subscription-id` to sync one specific subscription.
- Set `--azure-sync-all-subscriptions` to discover and sync every subscription
  visible to the authenticated identity.

When neither subscription option is set, Azure CLI and access token
authentication select the first subscription returned by the Azure
subscription API, which may not be the CLI's current subscription. Service principal authentication has no
default subscription ID and cannot sync a single subscription without
`--azure-subscription-id`.

## Run Cartography

With the active Azure CLI session and one explicit subscription:

```bash
az login

cartography \
  --selected-modules azure \
  --azure-subscription-id "<subscription-id>"
```

With a service principal and all visible subscriptions:

```bash
cartography \
  --selected-modules azure \
  --azure-sp-auth \
  --azure-sync-all-subscriptions \
  --azure-tenant-id "$AZURE_TENANT_ID" \
  --azure-client-id "$AZURE_CLIENT_ID" \
  --azure-client-secret-env-var AZURE_CLIENT_SECRET
```

With an ARM access token and all visible subscriptions:

```bash
cartography \
  --selected-modules azure \
  --azure-sync-all-subscriptions \
  --azure-access-token-env-var AZURE_ACCESS_TOKEN
```
