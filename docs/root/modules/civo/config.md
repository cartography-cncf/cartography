# Civo Configuration

## Authentication

Create an [API key](https://dashboard.civo.com/security) and store it in an
environment variable.

## Configure Cartography

Pass the API key environment variable name with `--civo-api-key-env-var`.

## Run Cartography

```bash
export CIVO_API_KEY="<api key>"

cartography \
  --selected-modules civo \
  --civo-api-key-env-var CIVO_API_KEY
```

## Advanced Configuration

Override the API base URL with `--civo-base-url`. It defaults to
`https://api.civo.com`.
