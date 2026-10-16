# CrowdStrike Configuration

## Authentication

Create a CrowdStrike Falcon API client by following the documentation for your
instance. Store its client ID and client secret in separate environment
variables.

The API client page lives in different menus depending on the Falcon console
version, for example **Support and resources → API clients and keys**,
**Support and resources → Client Management**, or **Support Apps → API Clients**
on older consoles.

### API scopes

Grant the API client these read-only scopes:

| Scope | Used for |
| --- | --- |
| **Hosts: Read** | `CrowdstrikeHost` nodes (`QueryDevicesByFilterScroll`, `GetDeviceDetails`). Hosts also feed the `Device` ontology, and vulnerabilities attach to them through `HAS_VULNERABILITY`. |
| **Vulnerabilities: Read** | `CrowdstrikeSpotlightVulnerability` and `CrowdstrikeFinding` nodes (`combinedQueryVulnerabilities`). Optional: only tenants licensed for Falcon Spotlight can grant it. |

A missing **Hosts: Read** scope makes the sync fail with HTTP 403; the error
names the refused operation. Without **Vulnerabilities: Read**, the sync logs a
warning, loads hosts only, and leaves previously synced vulnerabilities in
place. Scope changes apply to the existing client ID and secret, so there is no
need to rotate credentials after adding one.

## Configure Cartography

Pass the client ID environment variable name with
`--crowdstrike-client-id-env-var` and the client secret environment variable
name with `--crowdstrike-client-secret-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules crowdstrike \
  --crowdstrike-client-id-env-var CROWDSTRIKE_CLIENT_ID \
  --crowdstrike-client-secret-env-var CROWDSTRIKE_CLIENT_SECRET
```

## Advanced Configuration

For a self-hosted CrowdStrike instance, set the API URL with
`--crowdstrike-api-url`.
