# Tenable Configuration

Follow these steps to ingest Tenable assets and vulnerability findings with Cartography.

1. Create Tenable API access and secret keys with permission to use the Export API.
1. Populate environment variables with the access key and secret key.
1. Pass the environment variable names with `--tenable-access-key-env-var` and `--tenable-secret-key-env-var`.
1. Select the module with `--selected-modules tenable`.

```bash
export TENABLE_ACCESS_KEY="your-tenable-access-key"
export TENABLE_SECRET_KEY="your-tenable-secret-key"
cartography \
  --selected-modules tenable \
  --tenable-access-key-env-var TENABLE_ACCESS_KEY \
  --tenable-secret-key-env-var TENABLE_SECRET_KEY
```

## Options

| CLI flag | Default | Required | Description |
|---|---|---|---|
| `--tenable-access-key-env-var` | `TENABLE_ACCESS_KEY` | Yes | Environment variable holding the Tenable API access key |
| `--tenable-secret-key-env-var` | `TENABLE_SECRET_KEY` | Yes | Environment variable holding the Tenable API secret key |
| `--tenable-url` | `https://cloud.tenable.com` | No | Base URL of the Tenable API endpoint |
| `--tenable-tenant-id` | hostname of `--tenable-url` | No | Identifier used to scope all graph nodes for this Tenable instance. Set this to the container UUID shown in your Tenable account settings when running multiple tenants or using a custom URL. Defaults to the hostname portion of `--tenable-url` (for example, `cloud.tenable.com`). |
| `--tenable-findings-lookback-days` | `180` | No | Number of days of vulnerability findings to retrieve on each sync. Cartography sends Tenable's `since` export filter with `now - lookback_days`, which Tenable applies to `last_found` for open/reopened findings and `last_fixed` for fixed findings. Stale findings outside this window are removed from the graph by the cleanup job. |
