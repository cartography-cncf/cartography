# GSuite Configuration

:::{important} Deprecated Module
The `gsuite` module is a standalone legacy pipeline scheduled for removal in
Cartography v1.0.0. Selecting it still runs the legacy ingestion.
:::

## Authentication

The legacy module supports three authentication methods:

- `delegated`: a service-account JSON file with domain-wide delegation.
- `oauth`: base64-encoded OAuth credentials.
- `default`: Google Application Default Credentials.

The service account or OAuth client requires these scopes:

- `https://www.googleapis.com/auth/admin.directory.user.readonly`
- `https://www.googleapis.com/auth/admin.directory.group.readonly`
- `https://www.googleapis.com/auth/admin.directory.group.member`

For delegated authentication, set `GSUITE_DELEGATED_ADMIN` to the delegated
administrator email address.

## Configure Cartography

Select the authentication method with `--gsuite-auth-method`. Valid values are
`delegated`, `oauth`, and `default`; the default is `delegated`.

For `delegated` and `oauth`, store the credential value in an environment
variable and pass its name with `--gsuite-tokens-env-var`. The default variable
name is `GSUITE_GOOGLE_APPLICATION_CREDENTIALS`.

## Run Cartography

With delegated service-account authentication:

```bash
export GSUITE_GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export GSUITE_DELEGATED_ADMIN="admin@example.com"

cartography \
  --selected-modules gsuite \
  --gsuite-auth-method delegated \
  --gsuite-tokens-env-var GSUITE_GOOGLE_APPLICATION_CREDENTIALS
```

With Application Default Credentials:

```bash
cartography \
  --selected-modules gsuite \
  --gsuite-auth-method default
```

## Migration

Migrate to the [Google Workspace module](../googleworkspace/config.md) before
Cartography v1.0.0. The Google Workspace guide documents the replacement CLI
options, credential variables, APIs, and scopes.
