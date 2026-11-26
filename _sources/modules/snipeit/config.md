# SnipeIT Configuration

## Authentication

Generate an API token by following the [SnipeIT API token documentation](https://snipe-it.readme.io/reference/generating-api-tokens). Store it in `SNIPEIT_TOKEN`, or another environment variable.

## Configure Cartography

Provide these options:

- `--snipeit-base-uri`: SnipeIT API base URI.
- `--snipeit-tenant-id`: SnipeIT tenant ID used to establish relationships.
- `--snipeit-token-env-var`: Name of the environment variable containing the API token. If omitted, Cartography uses `SNIPEIT_TOKEN`.

## Run Cartography

```bash
export SNIPEIT_TOKEN='<api-token>'
cartography \
  --selected-modules snipeit \
  --snipeit-base-uri '<snipeit-api-url>' \
  --snipeit-tenant-id '<tenant-id>'
```
