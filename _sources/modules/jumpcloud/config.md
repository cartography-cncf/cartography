## JumpCloud Configuration

Follow these steps to analyze JumpCloud objects with Cartography.

1. Generate a JumpCloud API key.
    1. Log in to the [JumpCloud Admin Console](https://console.jumpcloud.com).
    1. Navigate to your profile (bottom-left) → **My API key**.
    1. Generate **API Key**.
    1. Store the key in an environment variable, e.g. `JUMPCLOUD_API_KEY`.

1. Find your JumpCloud Organization ID.
    1. In the Admin Console, navigate to **Settings** → **General**.
    1. Copy the **Organization ID** value.

1. Run Cartography with the JumpCloud options:

    ```bash
    export JUMPCLOUD_API_KEY="your-api-key"

    cartography \
      --neo4j-uri bolt://localhost:7687 \
      --jumpcloud-api-key-env-var JUMPCLOUD_API_KEY \
      --jumpcloud-org-id "<your-org-id>"
    ```

### CLI Reference

| Flag | Description |
|------|-------------|
| `--jumpcloud-api-key-env-var` | Name of the environment variable containing the JumpCloud API key (x-api-key auth) |
| `--jumpcloud-org-id` | JumpCloud organization ID used as the tenant identifier (required) |
