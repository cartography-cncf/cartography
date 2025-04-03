## Azure Configuration

### Create Azure Identity
Follow these steps to analyze Microsoft Azure assets with Cartography:

1. Set up an Azure identity for Cartography to use, and ensure that this identity has the built-in Azure [Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader) attached:
    * Authenticate: `$ az login`
    * Create a Service Principal: `$ az ad sp create-for-rbac --name cartography --role Reader`
    * Note the values of the `tenant`, `appId`, and `password` fields

### Cartography Configuration 

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_AZURE__SYNC_ALL_SUBSCRIPTIONS | `bool` _(default: False)_ | Enable Azure sync for all discovered subscriptions. When this parameter is supplied cartography will discover all configured Azure subscriptions. |
| CARTOGRAPHY_AZURE__SP_AUTH | `bool` _(default: False)_ | Use Service Principal authentication for Azure sync. |
| CARTOGRAPHY_AZURE__TENANT_ID | `str` | Azure Tenant Id for Service Principal Authentication. |
| CARTOGRAPHY_AZURE__CLIENT_ID | `str` | Azure Client Id for Service Principal Authentication. |
| CARTOGRAPHY_AZURE__CLIENT_SECRET | `str` | Azure Client Secret for Service Principal Authentication. |