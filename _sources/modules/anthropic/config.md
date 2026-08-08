# Anthropic Configuration

## Authentication

Create an Admin API key in the
[Anthropic Console](https://console.anthropic.com/settings/admin-keys) and store
it in an environment variable.

## Configure Cartography

Pass the name of the environment variable containing the Admin API key with
`--anthropic-apikey-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-apikey-env-var ANTHROPIC_API_KEY
```
