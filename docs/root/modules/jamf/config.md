# Jamf Configuration

Cartography requires a Jamf Pro base URI, username, and password.

1. Set the Jamf base URI with `--jamf-base-uri`, for example
   `https://hostname.jamfcloud.com`.
2. Set the Jamf username with `--jamf-user`.
3. Store the Jamf password in an environment variable and pass its name with
   `--jamf-password-env-var`.

For example:

```bash
export JAMF_PASSWORD="<password>"

cartography \
  --selected-modules jamf \
  --jamf-base-uri https://hostname.jamfcloud.com \
  --jamf-user cartography \
  --jamf-password-env-var JAMF_PASSWORD
```

Cartography first requests a bearer token from `/api/v1/auth/token`. If that
endpoint returns HTTP 404 or 405, it falls back to Basic authentication for
compatibility with older Jamf deployments.

## Canonical Device projection

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
