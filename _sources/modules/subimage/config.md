# SubImage Configuration

## Authentication

Obtain a WorkOS M2M client ID and client secret from your SubImage tenant.
Populate environment variables with these credentials. Pass the environment
variable names with `--subimage-client-id-env-var` and
`--subimage-client-secret-env-var`.

## Required Permissions

The M2M application must have **admin** scope to allow syncing API keys from
`/api/api-keys/subimage`.

## Configure Cartography

Pass your SubImage tenant URL with `--subimage-tenant-url` and your AuthKit URL
with `--subimage-authkit-url`.

## Run Cartography

```bash
export SUBIMAGE_CLIENT_ID="<client-id>"
export SUBIMAGE_CLIENT_SECRET="<client-secret>"

cartography \
  --selected-modules subimage \
  --subimage-client-id-env-var SUBIMAGE_CLIENT_ID \
  --subimage-client-secret-env-var SUBIMAGE_CLIENT_SECRET \
  --subimage-tenant-url "https://<subimage-tenant-url>" \
  --subimage-authkit-url "https://<authkit-url>"
```
