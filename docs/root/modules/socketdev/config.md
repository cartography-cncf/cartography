## Socket.dev Configuration

Follow these steps to ingest Socket.dev data with Cartography.

1. Create an API token in the Socket.dev dashboard under **Settings > API Tokens**. See [Socket.dev API Tokens](https://docs.socket.dev/docs/api-keys) for details.
1. Grant all **read** scopes to the token, including list scopes (e.g. `repo:list`, `repo:read`, `alert:list`, `alert:read`, `dependencies:read`). Cartography only reads data — no write scopes (`create`, `edit`, `delete`) are required.
1. Populate an environment variable with the token value.
1. Pass the environment variable name to the `--socketdev-token-env-var` CLI arg.

```bash
export SOCKETDEV_TOKEN="your-socket-dev-api-token"
cartography --socketdev-token-env-var SOCKETDEV_TOKEN --selected-modules socketdev
```

The module will automatically discover your organization and sync repositories, dependencies, and security alerts.
