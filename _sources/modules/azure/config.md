# Azure Configuration

## Authentication

Cartography supports Azure CLI authentication and service principal
authentication.

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
- Set `--azure-subscription-id` to sync one specific subscription.
- Set `--azure-sync-all-subscriptions` to discover and sync every subscription
  visible to the authenticated identity.

When neither subscription option is set, Azure CLI authentication selects the
first subscription returned by the Azure subscription API, which may not be
the CLI's current subscription. Service principal authentication has no
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
