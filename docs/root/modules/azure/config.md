## Azure Configuration

Recommended approach: use a Service Principal (SP) with Reader access. CLI authentication is still supported for local workflows, but SP auth is more reliable in CI/CD and does not depend on the Azure CLI being present or logged in.

1) Create a Service Principal with Reader role
- Authenticate locally: `az login`
- Create SP: `az ad sp create-for-rbac --name cartography --role Reader`
- Record `tenant`, `appId`, and `password`

2) Set environment variables
- `AZURE_TENANT_ID` = `tenant`
- `AZURE_CLIENT_ID` = `appId`
- `AZURE_CLIENT_SECRET` = `password`

3) Run Cartography with SP auth
```bash
cartography \
  --selected-modules azure \
  --azure-sp-auth --azure-sync-all-subscriptions \
  --azure-tenant-id ${AZURE_TENANT_ID} \
  --azure-client-id ${AZURE_CLIENT_ID} \
  --azure-client-secret-env-var AZURE_CLIENT_SECRET
```

Optional: Azure CLI auth (local development)
- Ensure `az login` has been run.
- No Python dependency on `azure-cli-core` is required; Cartography uses `AzureCliCredential` from `azure-identity` and the Azure SDK to discover tenant/subscription. You do not need to install or pin `azure-cli-core` in your Python environment.

Dependency note
- Cartography no longer depends on `azure-cli-core`. If upgrading from older versions, refresh your lockfile or environment so that `azure-cli-core` is removed.
