## Crowdstrike Configuration

Follow these steps to analyze Crowdstrike falcon objects in Cartography.

1. Prepare an API key for crowdstrike falcon
1. Crowdstrike's documentation is private, so please see your instance's documentation on how to generate an API key.
1. Populate environment variables `CARTOGRAPHY_CROWDSTRIKE__CLIENT_ID` and `CARTOGRAPHY_CROWDSTRIKE__CLIENT_SECRET`.
1. If you are using a self-hosted version of crowdstrike, you can change the API url, by defining `CARTOGRAPHY_CROWDSTRIKE__API_URL`.

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_CROWDSTRIKE__CLIENT_ID** | `str` | The crowdstrike client id for authentication. |
| **CARTOGRAPHY_CROWDSTRIKE__CLIENT_SECRET** | `str` | The crowdstrike secret key for authentication. |
| **CARTOGRAPHY_CROWDSTRIKE__API_URL** | `str` | The crowdstrike URL, if using self-hosted. Defaults to the public crowdstrike API URL otherwise. |
