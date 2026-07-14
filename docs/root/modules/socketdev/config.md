# Socket.dev Configuration

Cartography requires a Socket.dev API token with read access to the resources
being ingested.

1. Create an API token in the Socket.dev dashboard under **Settings > API
   Tokens**. See [Socket.dev API
   Tokens](https://docs.socket.dev/docs/api-keys) for details.
2. Grant all read scopes, including the list and read scopes for repositories,
   alerts, and dependencies. Cartography does not require create, edit, or
   delete scopes.
3. Store the token in an environment variable and pass that variable's name
   with `--socketdev-token-env-var`.

```bash
export SOCKETDEV_TOKEN="<token>"

cartography --socketdev-token-env-var SOCKETDEV_TOKEN --selected-modules socketdev
```

The module discovers every organization visible to the token, then syncs
repositories, dependencies, security alerts, and available fixes. The
dependencies endpoint is account-scoped, so those records are associated with
the first discovered organization.
