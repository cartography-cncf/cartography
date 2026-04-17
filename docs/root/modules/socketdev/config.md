## Socket.dev Configuration

Follow these steps to ingest Socket.dev data with Cartography.

1. Create an API token in the Socket.dev dashboard under **Settings > API Tokens**. See [Socket.dev API Tokens](https://docs.socket.dev/docs/api-keys) for details.
1. Populate an environment variable with the token value.
1. Pass the environment variable name to the `--socketdev-token-env-var` CLI arg.

```bash
export SOCKETDEV_TOKEN="your-socket-dev-api-token"
cartography --socketdev-token-env-var SOCKETDEV_TOKEN
```

The module will automatically discover your organization and sync repositories, dependencies, and security alerts.
