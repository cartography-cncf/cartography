## Kandji Configuration

Follow these steps to analyze Kandji device objects in Cartography.

1. Prepare an API token for Kandji
    1. Follow [Kandji documentation](https://support.kandji.io/support/solutions/articles/72000560412-kandji-api#Generate-an-API-Token) to generate a API token.
    1. Populate `CARTOGRAPHY_KANDJI__TOKEN` environment variable with the API token.
    1. Provide the Kandji API URL using the `CARTOGRAPHY_KANDJI__BASE_URL` and a Kandji Tenant (required for establishing relationship) using the `CARTOGRAPHY_KANDJI__TENANT_ID` variable.


### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_KANDJI__BASE_URL** | `str` | Your Kandji base URI (e.g. https://company.api.kandji.io.) |
| **CARTOGRAPHY_KANDJI__TENANT_ID** | `str` | Your Kandji tenant id (e.g. company). |
| **CARTOGRAPHY_KANDJI__TOKEN `str` | Token with which to authenticate to Kandji. |
