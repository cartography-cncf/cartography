# Airbyte Configuration

## Authentication

Create an application in the Airbyte admin panel. The application has the
permissions of the user who creates it.

Store its client secret in an environment variable. Pass the client ID with
`--airbyte-client-id` and the environment variable name with
`--airbyte-client-secret-env-var`.

## Configure Cartography

For a self-hosted Airbyte instance, set its API base URL with
`--airbyte-api-url`. The default is `https://api.airbyte.com/v1`.

## Run Cartography

```bash
cartography \
  --selected-modules airbyte \
  --airbyte-client-id "$AIRBYTE_CLIENT_ID" \
  --airbyte-client-secret-env-var AIRBYTE_CLIENT_SECRET
```
