# Socket.dev Configuration

## Authentication

Create an API token in the Socket.dev dashboard under **Settings > API
Tokens**. See [Socket.dev API
Tokens](https://docs.socket.dev/docs/api-keys) for details.

## Required Permissions

Cartography requires a Socket.dev API token with read access to the resources
being ingested. Grant all read scopes, including the list and read scopes for
repositories, alerts, and dependencies. Cartography does not require create,
edit, or delete scopes.

## Configure Cartography

Store the token in an environment variable and pass that variable's name with
`--socketdev-token-env-var`.

## Run Cartography

```bash
export SOCKETDEV_TOKEN="<token>"

cartography --socketdev-token-env-var SOCKETDEV_TOKEN --selected-modules socketdev
```
