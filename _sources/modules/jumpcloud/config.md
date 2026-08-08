# JumpCloud Configuration

## Authentication

1. Log in to the [JumpCloud Admin Console](https://console.jumpcloud.com).
2. Open your profile in the lower-left corner and select **My API key**.
3. Generate an API key and store it in an environment variable such as
   `JUMPCLOUD_API_KEY`.

## Configure Cartography

In the Admin Console, open **Settings**, select **General**, and copy the
**Organization ID** value.

Set the API key environment variable before running Cartography:

```bash
export JUMPCLOUD_API_KEY="your-api-key"
```

## Run Cartography

```bash
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules jumpcloud \
  --jumpcloud-api-key-env-var JUMPCLOUD_API_KEY \
  --jumpcloud-org-id "<your-org-id>"
```

## Advanced Configuration

| Flag | Description |
|------|-------------|
| `--jumpcloud-api-key-env-var` | Name of the environment variable containing the JumpCloud API key used for `x-api-key` authentication |
| `--jumpcloud-org-id` | JumpCloud organization ID used as the required tenant identifier |

## References

- [JumpCloud Admin Console](https://console.jumpcloud.com)
