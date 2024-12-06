## Azure Configuration

.. _azure_config:

Follow these steps to analyze Microsoft Azure assets with Cartography:

1. Set up an Azure identity for Cartography to use, and ensure that this identity has the built-in Azure [Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader) attached:
    * Authenticate: `$ az login`
    * Create a Service Principal: `$ az ad sp create-for-rbac --name cartography --role Reader`
    * Note the values of the `tenant`, `appId`, and `password` fields
1. Populate environment variables with the values generated in the previous step (e.g., `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
1. Call the `cartography` CLI with:
    ```bash
    --azure-sp-auth --azure-sync-all-subscriptions      \
    --azure-tenant-id ${AZURE_TENANT_ID}                \
    --azure-client-id ${AZURE_CLIENT_ID}                \
    --azure-client-secret-env-var AZURE_CLIENT_SECRET
    ```
