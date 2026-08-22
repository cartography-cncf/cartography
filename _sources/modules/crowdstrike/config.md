# CrowdStrike Configuration

## Authentication

Create a CrowdStrike Falcon API client by following the documentation for your
instance. Store its client ID and client secret in separate environment
variables.

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
