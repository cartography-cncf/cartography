## Entra Configuration

To enable Entra data ingestion, you need to configure the following CLI settings:

- `--entra-tenant-id`: Your Entra tenant ID
- `--entra-client-id`: The client ID of your Entra application
- `--entra-client-secret-env-var`: The name of an environment variable that contains the client secret of your Entra application.


To set up the Entra client,

1. Go to [App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) in the Azure portal
1. Create a new app registration.
1. Grant it `User.Read.All` and `User.Read` permissions to the Microsoft graph to audit users.
