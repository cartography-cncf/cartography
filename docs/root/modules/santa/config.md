## Santa Configuration

Follow these steps to analyze Santa machine and execution data from Zentral with Cartography.

1. Generate a Zentral API token with permissions required by the inventory and Santa export endpoints.
1. Set `SANTA_TOKEN` in your environment (or pass a different variable name with `--santa-token-env-var`).
1. Pass Zentral base URL with `--santa-base-url`.
1. Optionally set the inventory source name with `--santa-source-name` (defaults to `Santa`).
1. Optionally tune lookback and request timeout with `--santa-event-lookback-days` and `--santa-request-timeout`.

### CLI Example

```bash
export SANTA_TOKEN='<zentral-api-token>'

cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules santa \
  --santa-base-url https://zentral.example.com \
  --santa-token-env-var SANTA_TOKEN \
  --santa-source-name Santa \
  --santa-event-lookback-days 30 \
  --santa-request-timeout 60
```

## Required Zentral Permissions

- `inventory.view_machinesnapshot` for `/api/inventory/machines/export_snapshots/`
- Permission for the Santa events export endpoint (`/api/santa/events/export/`) when available

## Endpoint Dependency

Cartography Santa ingestion is intentionally fail-fast for app-on-machine data:

- If Zentral does not expose `/api/santa/events/export/` (for example 404/405), Santa ingestion raises an explicit error.
- Machine snapshot ingestion depends on Zentral inventory export tasks (`task_result_url` + `download_url`) and does not require local CSV exports.
