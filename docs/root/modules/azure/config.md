# Azure Configuration

## Authentication

Create a service principal for Cartography:

```bash
az login
az ad sp create-for-rbac --name cartography --role Reader
```

Store the returned `tenant`, `appId`, and `password` values in environment
variables such as `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and
`AZURE_CLIENT_SECRET`.

## Required Permissions

Grant the service principal the built-in Azure
[Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader)
on every subscription that Cartography should sync.

To ingest the management group hierarchy and subscription placement, also
grant a management-group-scoped read role such as `Management Group Reader`.
Assign it at the tenant root management group or another scope broad enough to
cover the management groups that Cartography should sync.

## Configure Cartography

Enable service principal authentication with `--azure-sp-auth`. Use
`--azure-sync-all-subscriptions` to sync all subscriptions visible to the
identity.

## Run Cartography

```bash
cartography \
  --selected-modules azure \
  --azure-sp-auth \
  --azure-sync-all-subscriptions \
  --azure-tenant-id "$AZURE_TENANT_ID" \
  --azure-client-id "$AZURE_CLIENT_ID" \
  --azure-client-secret-env-var AZURE_CLIENT_SECRET
```
