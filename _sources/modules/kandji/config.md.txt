## Kandji Configuration

Follow these steps to analyze Kandji device objects in Cartography.

1. Prepare an API token for Kandji
    1. Follow [Kandji documentation](https://support.kandji.io/support/solutions/articles/72000560412-kandji-api#Generate-an-API-Token) to generate a API token.
    1. Populate `KANDJI_TOKEN` environment variable with the API token. Alternately, you can pass a different environment variable name containing the API token
    via CLI with the `--kandji-token-env-var` parameter.
    1. Provide the Kandji API URL using the `--kandji-base-uri` and a Kandji Tenant (required for establishing relationship) using the `--kandji-tenant-id` parameter.
