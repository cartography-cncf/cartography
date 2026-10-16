# PagerDuty Configuration

## Authentication

Generate an API token by following the PagerDuty [Generating API Keys documentation](https://support.pagerduty.com/docs/generating-api-keys). Store the token in an environment variable.

## Configure Cartography

Use `--pagerduty-api-key-env-var` to provide the name of the environment variable containing the API token.

## Run Cartography

```bash
export PAGERDUTY_API_KEY='<api-token>'
cartography \
  --selected-modules pagerduty \
  --pagerduty-api-key-env-var PAGERDUTY_API_KEY
```

## Advanced Configuration

Use `--pagerduty-request-timeout` to set the request timeout in seconds.
