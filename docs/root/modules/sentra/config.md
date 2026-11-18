# Sentra configuration

Create a Sentra API key, and then provide it to Cartography in an environment
variable.

## Authentication

1. In Sentra, click **Settings**.
1. Click **API Keys**.
1. Generate an API key, and then copy it. Sentra displays the key only once.

Cartography sends the key in the `X-Sentra-API-Key` header.

## Required permissions

The API key must be able to read the following endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/core/users/current` | Identifies the Sentra organization that the key belongs to. |
| `POST /api/core/classes/search` | Reads data classes. |
| `POST /api/core/data-stores/search` | Reads data stores. |
| `POST /api/core/policies/search` | Reads policies. |
| `POST /api/core/alerts/search` | Reads alerts. |
| `GET /api/core/alerts/{alert_id}/violated_objects` | Reads the objects that violate the policy behind each data store alert. |

## Configure Cartography

| Option | Default | Required | Description |
|---|---|---|---|
| `--sentra-api-key-env-var` | `SENTRA_API_KEY` | Yes | Environment variable that holds the Sentra API key. |
| `--sentra-api-url` | `https://app.sentra.io` | No | Sentra API base URL. |

## Run Cartography

```bash
export SENTRA_API_KEY="API_KEY"

cartography --selected-modules sentra
```

Replace `API_KEY` with your Sentra API key.

A data store links with `MONITORS` to its AWS resource only when that resource
is already in the graph. To create these links, sync AWS before Sentra, either in
an earlier run or earlier in the same run:

```bash
cartography --selected-modules aws,sentra
```
