## OpenAI Configuration

Follow these steps to analyze OpenAI objects with Cartography.

1. Prepare your OpenAI API Key.
    1. Create an **READ ONLY** Admin API Key in [OpenAI Plateform API web UI](https://platform.openai.com/settings/organization/admin-keys)
    1. Populate an environment variable with the API Key. You can pass the environment variable name via CLI with the `--openai-apikey-env-var` parameter.
1. Got to `https://platform.openai.com/settings/organization/general`, get your organization ID (e.g. `org-xxxxxxxxxx`) and pass it via CLI with the `--openai-org-id` parameter.
