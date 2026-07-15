# Salesforce Configuration

## Prerequisites

In Salesforce Setup, open **My Domain** and deploy a domain. Note its URL, such as `https://mycompany.my.salesforce.com`. The client credentials flow requires this host as the login URL.

Create a dedicated read-only integration user. The Salesforce Integration user license is designed for API-only access, although a standard license also works.

## Authentication

Cartography authenticates to the Salesforce REST API with an OAuth 2.0 External Client App, or a classic Connected App on older organizations.

In **App Manager**, create an External Client App:

1. Set a name and contact email.
1. Under **API (Enable OAuth Settings)**, enable OAuth.
1. Set a callback URL, such as `https://login.salesforce.com/services/oauth2/callback`. Salesforce requires this even though Cartography does not use it for these flows.
1. Add the **Manage user data via APIs (api)** OAuth scope. Also add `refresh_token` or `offline_access` for the JWT bearer flow.
1. Create the app and allow a few minutes for it to propagate.

### Client Credentials

1. Open **Settings** > **OAuth Settings** > **Edit**. Under **Flow Enablement**, enable the client credentials flow. For a classic Connected App, this setting is directly in the OAuth settings.
1. Open **Policies** > **Edit** and set **Run As** to the dedicated integration user. For a classic Connected App, use **Manage** > **Edit Policies**.
1. Open **Settings** > **OAuth Settings** > **Consumer Key and Secret** and copy the consumer key and secret. A classic Connected App exposes these under **Manage Consumer Details**.

### JWT Bearer

1. Generate an RSA key pair and upload the certificate under **Use digital signatures** in the app's OAuth settings.
1. Set **Permitted Users** to **Admin approved users are pre-authorized**, then assign the integration user or profile.
1. Copy the app's consumer key.

## Required Permissions

Create a permission set for the integration user with:

- **API Enabled**.
- **View Setup and Configuration**, to read `Profile`, `PermissionSet`, `PermissionSetAssignment`, and `ConnectedApplication`.
- **Manage Users**, so `OAuthToken` returns all users' tokens. Without it, the query is limited to the integration user's tokens and produces incomplete `AUTHORIZED` relationships.
- Read access to `Organization`, `User`, `UserRole`, `Group`, and `GroupMember`.

Do not grant create, edit, delete, or **Modify All Data** permissions. Assign the permission set to the integration user and use that user as the app's **Run As** user or `--salesforce-username`.

## Configure Cartography

### Client Credentials

Provide:

- `--salesforce-client-id`: App consumer key.
- `--salesforce-client-secret-env-var`: Name of the environment variable containing the consumer secret. The default is `SALESFORCE_CLIENT_SECRET`.
- `--salesforce-login-url`: My Domain URL.

### JWT Bearer

Provide:

- `--salesforce-client-id`: App consumer key.
- `--salesforce-username`: Integration username.
- `--salesforce-private-key-env-var`: Name of the environment variable containing the PEM-encoded private key. The default is `SALESFORCE_PRIVATE_KEY`.

## Run Cartography

This client credentials example uses a My Domain URL:

```bash
export SALESFORCE_CLIENT_SECRET='<consumer-secret>'
cartography \
  --selected-modules salesforce \
  --salesforce-login-url 'https://mycompany.my.salesforce.com' \
  --salesforce-client-id '<consumer-key>' \
  --salesforce-client-secret-env-var SALESFORCE_CLIENT_SECRET
```

## Advanced Configuration

Set `--salesforce-login-url` according to the authentication flow and organization:

- Production or Developer edition with JWT bearer: `https://login.salesforce.com`, which is the default.
- Sandbox with JWT bearer: `https://test.salesforce.com`.
- Client credentials: Your My Domain URL.

Cartography resolves the organization's instance URL from the token response.

## Troubleshooting

If **Enable Client Credentials Flow** is unavailable, deploy **My Domain** and enable **Allow OAuth Client Credentials Flows** under **OAuth and OpenID Connect Settings**.
