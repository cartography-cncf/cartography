## Entra Configuration

To set up the Entra client,

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal
1. Create a new app registration.
1. Grant it `User.Read.All` and `User.Read` permissions to the Microsoft graph to audit users.

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_ENTRA__TENANT_ID** | `str` | Your Entra tenant ID. |
| **CARTOGRAPHY_ENTRA__CLIENT_ID** | `str` | The client ID of your Entra application. |
| **CARTOGRAPHY_ENTRA__CLIENT_SECRET** | `str` | The client secret of your Entra application. |
