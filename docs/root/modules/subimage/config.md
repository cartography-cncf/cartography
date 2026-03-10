## SubImage Configuration

Follow these steps to analyze SubImage objects with Cartography.

1. Prepare your SubImage API credentials.
    1. Obtain a WorkOS M2M client ID and client secret from your SubImage tenant. The M2M application must have **admin** scope to allow syncing API keys from `/api/api-keys/subimage`.
    1. Populate environment variables with these credentials. You can pass the environment variable names via CLI with the `--subimage-client-id-env-var` and `--subimage-client-secret-env-var` parameters.
1. Pass your SubImage tenant URL with `--subimage-tenant-url`.
1. Pass your AuthKit URL with `--subimage-authkit-url`.
