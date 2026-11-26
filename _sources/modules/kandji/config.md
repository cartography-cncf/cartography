# Kandji Configuration

## Authentication

Follow the
[Kandji API documentation](https://support.kandji.io/support/solutions/articles/72000560412-kandji-api#Generate-an-API-Token)
to generate an API token. Store the token in `KANDJI_TOKEN`, or store it in
another environment variable and identify that variable with
`--kandji-token-env-var`.

```bash
export KANDJI_TOKEN="your-api-token"
```

## Configure Cartography

Provide the Kandji API URL with `--kandji-base-uri` and the tenant identifier
with `--kandji-tenant-id`. The tenant identifier is required to establish
tenant relationships.

## Run Cartography

```bash
cartography \
  --selected-modules kandji \
  --kandji-base-uri https://company.api.kandji.io \
  --kandji-tenant-id "<your-tenant-id>" \
  --kandji-token-env-var KANDJI_TOKEN
```

## Advanced Configuration

| Flag | Description |
|------|-------------|
| `--kandji-base-uri` | Kandji API base URI |
| `--kandji-tenant-id` | Kandji tenant identifier |
| `--kandji-token-env-var` | Name of the environment variable containing the API token |

## References

- [Kandji API token documentation](https://support.kandji.io/support/solutions/articles/72000560412-kandji-api#Generate-an-API-Token)
