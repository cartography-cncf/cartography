# Sentra Configuration

Create a Sentra API key, then provide it to Cartography in an environment
variable.

## Authentication

1. In Sentra, open **Settings**.
1. Select **API Keys**.
1. Generate an API key. Sentra displays the key only once.

Cartography sends the key in the `X-Sentra-API-Key` header.

## Required Permissions

The API key must be able to read the following endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/core/users/current` | Identifies the Sentra organization the key belongs to. |
| `POST /api/core/classes/search` | Reads data classes. |
| `POST /api/core/data-stores/search` | Reads data stores. |
| `POST /api/core/alerts/search` | Reads alerts. |

## Configure Cartography

| Option | Default | Required | Description |
|---|---|---|---|
| `--sentra-api-key-env-var` | `SENTRA_API_KEY` | Yes | Environment variable holding the Sentra API key. |
| `--sentra-api-url` | `https://app.sentra.io` | No | Sentra API base URL. |

## Run Cartography

```bash
export SENTRA_API_KEY="..."

cartography --selected-modules sentra
```

To link Sentra data stores to AWS resources, sync AWS in the same run, before
Sentra:

```bash
cartography --selected-modules aws,sentra
```
