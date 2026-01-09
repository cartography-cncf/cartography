# Microsoft Defender for Endpoint (MDE) Configuration

This module requires a registered Azure AD Application with specific permissions to access the Microsoft Defender for Endpoint API.

## 1. API Permissions
Ensure your Azure AD application is granted the following **WindowsDefenderATP API** (Application) permissions (found under 'APIs my organization uses' in Azure portal):
* `Machine.Read.All`: Required to ingest device metadata and health status.
* `Software.Read.All`: (Recommended) For future software inventory support.
* `Vulnerability.Read.All`: (Recommended) For future vulnerability risk assessment.

## 2. Required Credentials
The module expects the following credentials to be available during the sync process:
* `mde_tenant_id`: The Directory (tenant) ID of your Entra ID instance.
* `mde_client_id`: The Application (client) ID of your registered app.
* `mde_client_secret`: A valid client secret for the application.

## 3. Execution
To run this module manually via the CLI:
```bash
cartography --mde-tenant-id <id> --mde-client-id <id> --mde-client-secret <secret>