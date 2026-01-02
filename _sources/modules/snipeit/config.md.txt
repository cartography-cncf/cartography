## SnipeIT Configuration

Follow these steps to analyze SnipeIT users and assets in Cartography.

1. Prepare an API token for SnipeIT
    1. Follow [SnipeIT documentation](https://snipe-it.readme.io/reference/generating-api-tokens) to generate a API token.
    1. Populate `SNIPEIT_TOKEN` environment variable with the API token. Alternately, you can pass a different environment variable name containing the API token
    via CLI with the `--snipeit-token-env-var` parameter.
    1. Provide the SnipeIT API URL using the `--snipeit-base-uri` and a SnipeIT Tenant (required for establishing relationship) using the `--snipeit-tenant-id` parameter.
