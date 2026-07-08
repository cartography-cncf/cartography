## Salesforce Configuration

Follow these steps to enable the Salesforce integration with Cartography.

Cartography reads Salesforce data through the REST API using SOQL. It authenticates
with an OAuth 2.0 app (an **External Client App**, or the classic **Connected App** on
older orgs). Two flows are supported; pick whichever fits your org:

- **Client credentials** (simplest, server-to-server): consumer key + consumer secret.
- **JWT bearer**: consumer key + integration username + a signed private key.

### 1. Enable My Domain

In Setup, go to **My Domain** and make sure a domain is deployed. Note the URL, e.g.
`https://mycompany.my.salesforce.com`. The client credentials flow **requires** the
My Domain host as the login URL; `login.salesforce.com` will not work for it.

### 2. Create the app

In Setup, go to **App Manager** → **New External Client App** (on older orgs, use
**New Connected App**):

1. Set a name (e.g. `Cartography`) and a contact email.
1. Under **API (Enable OAuth Settings)**, check **Enable OAuth**.
1. Set a **Callback URL** (required even though the flows below don't use it), e.g.
   `https://login.salesforce.com/services/oauth2/callback`.
1. Add the **Manage user data via APIs (api)** OAuth scope (add `refresh_token` /
   `offline_access` as well if you use the JWT bearer flow).
1. Create the app, then wait a few minutes for it to propagate.

### 3. Configure a flow

**Client credentials flow (recommended for a quick start):**

On an **External Client App** the flow is enabled in **Settings** first, then the
run-as user is set in **Policies** (the flow only appears under Policies once enabled):

1. Open the app's **Settings** tab → **OAuth Settings** → **Edit** → under **Flow
   Enablement**, check **Enable Client Credentials Flow**. Save. (On a classic
   Connected App, this checkbox lives directly in the OAuth settings instead.)
1. Open the **Policies** tab → **Edit**. A **Client Credentials Flow** section now
   appears → set **Run As** to a user with **API Enabled** and read access to the
   ingested objects (a System Administrator is the simplest choice on a test org).
   Save. (On a classic Connected App this is under **Manage** → **Edit Policies**.)
1. Pass:
   - `--salesforce-client-id` : the app **Consumer Key**
   - the consumer secret in the environment variable named by
     `--salesforce-client-secret-env-var` (default `SALESFORCE_CLIENT_SECRET`)

```{note}
If **Enable Client Credentials Flow** is greyed out, deploy **My Domain** first and
make sure **Allow OAuth Client Credentials Flows** is enabled under Setup → **OAuth
and OpenID Connect Settings**.
```

**JWT bearer flow (server-to-server, no stored secret):**

1. Generate an RSA key pair and upload the certificate to the app's OAuth settings
   (**Use digital signatures**).
1. Pre-authorize the integration user (set **Permitted Users** to *Admin approved
   users are pre-authorized* and assign the user/profile).
1. Pass:
   - `--salesforce-client-id` : the app **Consumer Key**
   - `--salesforce-username` : the integration username
   - the PEM-encoded private key in the environment variable named by
     `--salesforce-private-key-env-var` (default `SALESFORCE_PRIVATE_KEY`)

### 4. Get the consumer key and secret

On the app, open **Settings** → **OAuth Settings** → **Consumer Key and Secret** (a
classic Connected App exposes these under **Manage Consumer Details**). Verify your
identity when prompted and copy the values.

### 5. Set the login URL

Use `--salesforce-login-url` to point at the right token endpoint:

- Production / Developer edition (JWT bearer): `https://login.salesforce.com` (default)
- Sandbox (JWT bearer): `https://test.salesforce.com`
- Client credentials flow: your My Domain URL, e.g. `https://mycompany.my.salesforce.com`

Cartography resolves the org's instance URL automatically from the token response.

### Example

```bash
export SALESFORCE_CLIENT_SECRET='<consumer secret>'
cartography \
  --selected-modules salesforce \
  --neo4j-uri bolt://localhost:7687 \
  --salesforce-login-url 'https://mycompany.my.salesforce.com' \
  --salesforce-client-id '<consumer key>'
```

The integration user needs read access to the objects Cartography ingests:
`Organization`, `User`, `Profile`, `PermissionSet`, `PermissionSetAssignment`,
`UserRole`, `Group`, `GroupMember`, `ConnectedApplication`, and `OAuthToken`.
