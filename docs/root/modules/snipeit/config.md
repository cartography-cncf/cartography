## SnipeIT Configuration

Follow these steps to analyze SnipeIT users and assets in Cartography.

1. Prepare an API token for SnipeIT
    1. Follow [SnipeIT documentation](https://snipe-it.readme.io/reference/generating-api-tokens) to generate a API token.
    1. Populate `CARTOGRAPHY_SNIPEIT__TOKEN` environment variable with the API token.
    1. Provide the SnipeIT API URL using `CARTOGRAPHY_SNIPEIT__BASE_URL` and a SnipeIT Tenant (required for establishing relationship) using the `CARTOGRAPHY_SNIPEIT__TENANT_ID` environment variable.

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_SNIPEIT__TOKEN** | `str` | Token with which to authenticate to SnipeIT. |
| **CARTOGRAPHY_SNIPEIT__BASE_URL** | `str` | Your SnipeIT base URI. |
| **CARTOGRAPHY_SNIPEIT__TENANT_ID** | `str` | An ID for the SnipeIT tenant. |
