# Opsgenie Configuration

## Authentication

Create an account-level API integration in Opsgenie (**Settings** > **Integrations** > **API**) and copy its API key. Store the key in an environment variable.

Configure the integration as follows:

- Enable **Limit to Read-Only Access**. Cartography only sends `GET` requests.
- Disable **Restrict Access to Configurations**. Users, teams, and schedules are configuration domains, so a restricted key is refused for them.

Cartography reads these endpoints:

- `GET /v2/account`
- `GET /v2/teams` and `GET /v2/teams/{id}` (for team membership)
- `GET /v2/users`
- `GET /v2/schedules`

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
