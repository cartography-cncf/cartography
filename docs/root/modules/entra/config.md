## Entra Configuration

To enable Entra data ingestion, you need to configure the following settings:

- `entra_tenant_id`: Your Entra tenant ID
- `entra_client_id`: The client ID of your Entra application
- `entra_client_secret`: The client secret of your Entra application


To set up the application,

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal
1. Create a new app registration.
1. Grant it `User.Read.All` and `User.Read` permissions to the Microsoft graph.
