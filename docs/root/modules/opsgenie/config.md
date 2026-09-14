# Opsgenie Configuration

## Authentication

Create an Opsgenie API key with read-only Configuration Access. Store the key in an environment variable.

## Configure Cartography

Use `--opsgenie-api-key-env-var` to provide the name of the environment variable containing the API key.

Opsgenie accounts in the EU region should also set `--opsgenie-api-url https://api.eu.opsgenie.com`.

## Run Cartography

```bash
export OPSGENIE_API_KEY='<api-key>'
cartography \
  --selected-modules opsgenie \
  --opsgenie-api-key-env-var OPSGENIE_API_KEY
```

## Advanced Configuration

Use `--opsgenie-request-timeout` to set the request timeout in seconds.
