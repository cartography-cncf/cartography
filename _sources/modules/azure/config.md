## Azure Configuration

Follow these steps to analyze Microsoft Azure assets with Cartography:

1. Set up an Azure identity for Cartography to use, and ensure that this identity has the Azure permissions needed for both subscription resources and management-group hierarchy reads:
    * Subscription/resource inventory: the built-in Azure [Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader) on the subscriptions you want to sync
    * Management-group hierarchy: a management-group-scoped read role such as `Management Group Reader` on the tenant root management group (or another scope broad enough to read the management groups you want to sync)
    * Authenticate: `$ az login`
    * Create a Service Principal: `$ az ad sp create-for-rbac --name cartography --role Reader`
    * Note the values of the `tenant`, `appId`, and `password` fields
1. If you are using a Service Principal, also assign it read access to the management-group hierarchy. For example, grant `Management Group Reader` at the `Tenant Root Group` so Cartography can read management groups and subscription placement within that hierarchy.
1. Populate environment variables with the values generated in the previous step (e.g., `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
1. Call the `cartography` CLI with:
    ```bash
    --azure-sp-auth --azure-sync-all-subscriptions      \
    --azure-tenant-id ${AZURE_TENANT_ID}                \
    --azure-client-id ${AZURE_CLIENT_ID}                \
    --azure-client-secret-env-var AZURE_CLIENT_SECRET
    ```
