# Tailscale Configuration

## Authentication

### OAuth client

An OAuth client is recommended because it is tag-scoped, is not tied to a user,
and is exchanged at sync time for a short-lived bearer token. This matches
Tailscale's [recommended pattern for service
integrations](https://tailscale.com/kb/1215/oauth-clients).

Create an OAuth client at [Settings > OAuth
clients](https://login.tailscale.com/admin/settings/oauth). Put the client ID
and secret in two environment variables.

### API access token

Create a long-lived API access token tied to a user account at [Settings >
Keys](https://login.tailscale.com/admin/settings/keys). Export it in an
environment variable.

## Required Permissions

An OAuth client needs these read-only scopes:

- `devices:core:read`: `/tailnet/:org/devices`
- `devices:posture_attributes:read`: `/device/:id/attributes`
- `users:read`: `/tailnet/:org/users`
- `policy_file:read`: `/tailnet/:org/acl`
- `feature_settings:read`: `/tailnet/:org/settings` and
  `/tailnet/:org/posture/integrations`

See [trust credentials](https://tailscale.com/docs/reference/trust-credentials)
for the canonical scope list.

## Configure Cartography

Pass `--tailscale-org <tailnet-id>` for either authentication method. Copy the
**Tailnet ID**, such as `T1234CNTRL`, from [Settings >
General](https://login.tailscale.com/admin/settings/general).

Tailnets created before October 2025 also have a **Legacy ID**, such as
`example.com`, and the Tailscale API still accepts it. If you already sync
with the legacy ID, keep it.

````{warning}
Cartography uses this value as the `TailscaleTailnet` node ID, and Tailscale
gives no way to tell that two IDs name the same tailnet. Switching an existing
sync from the legacy ID to the Tailnet ID creates a second tailnet node. The old
node stays in the graph, still linked to its devices, users, and other nodes,
and nodes that exist only under it are never cleaned up.

After the first sync with the new ID, delete the old tailnet and the nodes that
only it owns:

```cypher
MATCH (old:TailscaleTailnet {id: "example.com"})
OPTIONAL MATCH (old)-[:RESOURCE]->(n)
WHERE NOT EXISTS {
    MATCH (n)<-[:RESOURCE]-(owner:TailscaleTailnet)
    WHERE owner <> old
}
DETACH DELETE n, old
```
````

For OAuth, pass the environment variable names with
`--tailscale-oauth-client-id-env-var` and
`--tailscale-oauth-client-secret-env-var`. For an API access token, pass the
environment variable name with `--tailscale-token-env-var`.

## Run Cartography

With an OAuth client:

```bash
export TS_OAUTH_CLIENT_ID="<client id>"
export TS_OAUTH_CLIENT_SECRET="<client secret>"

cartography \
  --selected-modules tailscale \
  --tailscale-oauth-client-id-env-var TS_OAUTH_CLIENT_ID \
  --tailscale-oauth-client-secret-env-var TS_OAUTH_CLIENT_SECRET \
  --tailscale-org T1234CNTRL
```

With an API access token:

```bash
export TAILSCALE_TOKEN="<token>"

cartography \
  --selected-modules tailscale \
  --tailscale-token-env-var TAILSCALE_TOKEN \
  --tailscale-org T1234CNTRL
```

## Advanced Configuration

For self-hosted instances, set `--tailscale-base-url`. It defaults to
`https://api.tailscale.com/api/v2`, and the same base URL is used for the OAuth
token endpoint.

Cartography exchanges OAuth credentials at `{base_url}/oauth/token` using the
RFC 6749 `client_credentials` grant and uses the returned access token for the
rest of the sync.

If both `--tailscale-token-env-var` and the OAuth client flags are set, the
OAuth client is used and a warning is logged.
