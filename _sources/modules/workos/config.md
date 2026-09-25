# WorkOS Configuration

## Authentication

Get your WorkOS client ID from the [WorkOS
Dashboard](https://dashboard.workos.com/get-started) and create an API key on
the dashboard's API keys page.

Store both values in environment variables.

## Configure Cartography

Pass the name of the API key environment variable with
`--workos-apikey-env-var` and the client ID with `--workos-client-id`.

## Run Cartography

```bash
export WORKOS_API_KEY="<api-key>"
export WORKOS_CLIENT_ID="<client-id>"

cartography \
  --selected-modules workos \
  --workos-apikey-env-var WORKOS_API_KEY \
  --workos-client-id "$WORKOS_CLIENT_ID"
```
