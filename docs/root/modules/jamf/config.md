# Jamf Configuration

## Authentication

Cartography requires a Jamf Pro username and password. Store the password in an
environment variable:

```bash
export JAMF_PASSWORD="<password>"
```

Cartography first requests a bearer token from `/api/v1/auth/token`. If that
endpoint returns HTTP 404 or 405, it falls back to Basic authentication for
compatibility with older Jamf deployments.

## Configure Cartography

Set the Jamf base URI with `--jamf-base-uri`, for example
`https://hostname.jamfcloud.com`. Set the username with `--jamf-user` and pass
the password environment variable name with `--jamf-password-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules jamf \
  --jamf-base-uri https://hostname.jamfcloud.com \
  --jamf-user cartography \
  --jamf-password-env-var JAMF_PASSWORD
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
