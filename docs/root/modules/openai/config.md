## OpenAI Configuration

Follow these steps to analyze OpenAI objects with Cartography.

1. Prepare your OpenAI API Key.
    1. Create an **READ ONLY** Admin API Key in [OpenAI Plateform API web UI](https://platform.openai.com/settings/organization/admin-keys)
    1. Populate the `CARTOGRAPHY_OPENAI__APIKEY` environment variable with the API Key.
1. Got to `https://platform.openai.com/settings/organization/general`, get your organization ID (e.g. `org-xxxxxxxxxx`) and pass it using `CARTOGRAPHY_OPENAI__ORG_ID` environment variable.

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_OPENAI__APIKEY** | `str` | The OpenAI Admin API Key for authentication. |
| **CARTOGRAPHY_OPENAI__ORG_ID** | `str` | The ID of the OpenAI organization to sync. |
