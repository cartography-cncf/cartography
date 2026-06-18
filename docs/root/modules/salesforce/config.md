## Salesforce Configuration

Follow these steps to analyze Salesforce people and their permissions with Cartography.

Cartography syncs the Salesforce organization (tenant), its users, profiles, and permission sets, plus the relationships between them. Other Salesforce content (objects, records, sharing rules, etc.) is out of scope for this module.

### 1. Create a Connected App (or External Client App)

In Salesforce **Setup → App Manager → New Connected App** (or **Setup → External Client App Manager → New External Client App**, the newer equivalent), enable OAuth settings. Add at least the **Manage user data via APIs (`api`)** OAuth scope. The app's **Consumer Key** is your client ID. Choose one of the two supported OAuth flows below.

### 2a. Option A: Client Credentials flow (recommended)

1. In the app's OAuth settings, **Enable Client Credentials Flow** and set the **Run As** user to one with permission to read users, profiles, and permission sets (e.g. a System Administrator, or a user with the *View Setup and Configuration* permission).
    - The **Run As** field expects the user's **Username**, not their email address. In Developer / scratch orgs the username typically has a suffix (e.g. `you@example.com.myorg` or `you.xxxx@agentforce.com`) — copy the exact value from **Setup → Users**. Using the email here causes a "no client credentials user enabled" error at sync time.
    - For an **External Client App**, the Run As user is configured on the app's **Settings → OAuth Settings → Client Credentials Flow** section (not the legacy Connected Apps screen).
2. Note the app's **Consumer Key** (client ID) and **Consumer Secret**.
3. Put the consumer secret in an environment variable.

Run Cartography with:

```bash
cartography \
    --salesforce-instance-url https://mydomain.my.salesforce.com \
    --salesforce-client-id <CONSUMER_KEY> \
    --salesforce-client-secret-env-var SALESFORCE_CLIENT_SECRET
```

### 2b. Option B: JWT Bearer flow

1. Generate an X.509 certificate / private key pair and upload the certificate to the connected app (**Use digital signatures**).
2. Pre-authorize the run-as Salesforce user for the connected app.
3. Put the PEM-encoded private key in an environment variable.

Run Cartography with:

```bash
cartography \
    --salesforce-instance-url https://mydomain.my.salesforce.com \
    --salesforce-client-id <CONSUMER_KEY> \
    --salesforce-username <RUN_AS_USERNAME> \
    --salesforce-private-key-env-var SALESFORCE_PRIVATE_KEY
```

### Flow selection

The module picks the flow automatically based on the credentials you supply: if a client secret is provided it uses the Client Credentials flow; otherwise, if a username and private key are provided it uses the JWT Bearer flow. If neither set is present, the Salesforce module is skipped.

### Notes

- `--salesforce-instance-url` is your Salesforce **My Domain** login URL.
- Profile-owned permission sets (Salesforce's internal representation of a profile's permissions) are not synced as `SalesforcePermissionSet` nodes; a user's base permissions are represented by the `HAS_PROFILE` relationship, and only standalone permission sets become `HAS_PERMISSION_SET` relationships.
- Salesforce-internal system users (for example `AutomatedProcess` and `CloudIntegrationUser` user types) reference internal profiles that are not returned by the `Profile` API. These users are still synced as `SalesforceUser` nodes, but will not have a `HAS_PROFILE` relationship.

### Troubleshooting

- **`invalid_grant: no client credentials user enabled`** at sync start: the Client Credentials flow has no valid Run As user. Confirm the flow is enabled and that the **Run As** field contains a valid, active user **Username** (not an email) — see step 2a.
