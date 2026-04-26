## Sysdig Configuration

The Sysdig module uses the
[Sysdig Secure SysQL API](https://docs.sysdig.com/en/developer-tools/sysql-api/).

1. Create a Sysdig API token or service account token with read access to Search,
   Inventory, findings, risk, vulnerability, and runtime event data.
1. Store the token in an environment variable.
1. Run Cartography with `--selected-modules sysdig` and pass the token
   environment variable name with `--sysdig-api-token-env-var`.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sysdig-api-token-env-var` | Environment variable containing the Sysdig API token. | None |
| `--sysdig-api-url` | Sysdig API base URL. | `https://api.us1.sysdig.com` |
| `--sysdig-tenant-id` | Stable tenant id for Sysdig data. Defaults to the API hostname. | API hostname |
| `--sysdig-runtime-event-lookback-hours` | Lookback window for runtime event summaries. | `24` |
| `--sysdig-page-size` | SysQL query page size. | `1000` |

Example:

```bash
export SYSDIG_API_TOKEN=...
cartography \
  --selected-modules create-indexes,sysdig,ontology,analysis \
  --sysdig-api-token-env-var SYSDIG_API_TOKEN
```

The module calls `GET /api/sysql/v2/schema` once per sync and uses
`POST /api/sysql/v2/query` for paged SysQL queries.
