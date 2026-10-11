# Duo Configuration

## Authentication

Create [Duo Admin API credentials](https://duo.com/docs/adminapi). Store the
integration key and secret key in separate environment variables.

## Configure Cartography

Pass the Duo API hostname with `--duo-api-hostname`. Pass the integration key
environment variable name with `--duo-api-key-env-var` and the secret key
environment variable name with `--duo-api-secret-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules duo \
  --duo-api-hostname "$DUO_API_HOSTNAME" \
  --duo-api-key-env-var DUO_API_KEY \
  --duo-api-secret-env-var DUO_API_SECRET
```
