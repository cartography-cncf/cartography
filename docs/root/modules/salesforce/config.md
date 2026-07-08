## Salesforce Configuration

Follow these steps to enable the Salesforce integration with Cartography.

Cartography reads Salesforce data through the REST API using SOQL. It authenticates
with a [connected app](https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm)
via OAuth 2.0. Two flows are supported; pick whichever fits your org.

### 1. Create a connected app

1. In Salesforce Setup, go to **App Manager** and create a **New Connected App**.
1. Enable **OAuth Settings** and grant it at least the `api` scope (and `refresh_token`
   if using the JWT bearer flow).
1. Assign the connected app to a user (the "run as" / integration user) that has read
   access to the objects Cartography ingests (User, Profile, PermissionSet,
   PermissionSetAssignment, UserRole, Group, GroupMember, ConnectedApplication,
   OAuthToken). The **View Setup and Configuration** and **API Enabled** permissions
   are required.

### 2. Choose an authentication flow

**JWT bearer flow (recommended, server-to-server):**

1. Generate an RSA key pair and upload the certificate to the connected app under
   **Use digital signatures**.
1. Pre-authorize the integration user (Manage Connected App → set **Permitted Users**
   to *Admin approved users are pre-authorized*).
1. Pass:
   - `--salesforce-client-id` : the connected app **Consumer Key**
   - `--salesforce-username` : the integration username
   - the PEM-encoded private key in the environment variable named by
     `--salesforce-private-key-env-var` (default `SALESFORCE_PRIVATE_KEY`)

**Client credentials flow:**

1. In the connected app, enable **Client Credentials Flow** and select a run-as user.
1. Pass:
   - `--salesforce-client-id` : the connected app **Consumer Key**
   - the consumer secret in the environment variable named by
     `--salesforce-client-secret-env-var` (default `SALESFORCE_CLIENT_SECRET`)

### 3. Set the login URL

Use `--salesforce-login-url` to point at the right token endpoint:

- Production / Developer edition: `https://login.salesforce.com` (default)
- Sandbox: `https://test.salesforce.com`
- Or your org's My Domain URL, e.g. `https://mycompany.my.salesforce.com`

Cartography resolves the org's instance URL automatically from the token response.
