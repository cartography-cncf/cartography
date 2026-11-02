# Jamf Configuration

## Authentication

Cartography authenticates with either a Jamf Pro API client (recommended) or a
username and password.

### API client

In Jamf Pro, create an API role with read privileges for computers, mobile
devices, smart computer groups, static computer groups, smart mobile device
groups and static mobile device groups, then an API client assigned to that role.
Store the client secret in an environment variable:

```bash
export JAMF_CLIENT_SECRET="<client secret>"
```

Cartography exchanges the client ID and secret at `/api/oauth/token` and
requests a new token before each one expires, so the client's token lifetime
can be short.

### Username and password

Store the password in an environment variable:

```bash
export JAMF_PASSWORD="<password>"
```

Cartography first requests a bearer token from `/api/v1/auth/token`. If that
endpoint returns HTTP 404 or 405, it falls back to Basic authentication for
compatibility with older Jamf deployments.

## Configure Cartography

Set the Jamf base URI with `--jamf-base-uri`, for example
`https://hostname.jamfcloud.com`. For an API client, set `--jamf-client-id` and
pass the secret's environment variable name with `--jamf-client-secret-env-var`.
For a user, set `--jamf-user` and pass the password environment variable name
with `--jamf-password-env-var`. When both are given, the API client is used.

## Run Cartography

```bash
cartography \
  --selected-modules jamf \
  --jamf-base-uri https://hostname.jamfcloud.com \
  --jamf-client-id <client id> \
  --jamf-client-secret-env-var JAMF_CLIENT_SECRET
```

## Advanced Configuration

Jamf records can contribute to canonical ontology `Device` nodes. To use Jamf
as a device source of truth, include it in `--ontology-devices-source`:

```bash
cartography \
  --selected-modules jamf,ontology \
  --jamf-base-uri https://hostname.jamfcloud.com \
  --jamf-user cartography \
  --jamf-password-env-var JAMF_PASSWORD \
  --ontology-devices-source jamf
```

Multiple device sources can be provided as a comma-separated list, for example
`--ontology-devices-source jamf,tailscale`.
