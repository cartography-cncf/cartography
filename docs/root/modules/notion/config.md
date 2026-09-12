# Notion Configuration

Configure at least one Notion connection token before running this module. A
Notion personal access token (PAT) is not a connection token and will not work.

## Authentication

For a manual Cartography deployment, create an internal Notion connection:

1. In Notion, open **Settings**, select **Connections**, and choose **Develop
   your own connections**.
2. In the Creator dashboard, select **Internal connections** and create a
   connection for the workspace.
3. On its **Configuration** tab, enable **Read user information including email
   addresses**.
4. Copy its **Installation access token** into Cartography's `api_token` field.

Do not create a personal access token. PATs act as one user and Notion does not
allow them to call the List all users endpoint required by this module.

For a hosted, multi-workspace deployment, use a public OAuth connection instead.
Configure the same user-information capability before users authorize it, then
store each valid OAuth access token in the corresponding workspace entry. The
hosting service is responsible for the OAuth flow, secure token storage, and
token refresh; Cartography does not perform OAuth authorization itself.

Store tokens in a secret manager or environment variable; base64 encoding the
module config does not encrypt it. Cartography discovers the workspace ID and,
when Notion exposes it, the workspace name from each connection token. Public
connections may use the stable workspace ID as the tenant name.

## Required Permissions

| Capability | Purpose |
|------------|---------|
| Read user information including email addresses | Inventory workspace people and bot connections and map people by email |

## Optional Permissions

| Capability | Feature |
|------------|---------|
| Read content | Discover metadata for connection-visible pages published to the web when `sync_public_pages` is enabled |

No insert, update, or comment capability is required. Public-page sync is
disabled by default because Notion search can be high-cardinality and is not an
authoritative workspace inventory.

## Configure Cartography

Cartography accepts a base64-encoded JSON object so multiple workspaces and
their credentials can be configured together:

```python
import base64
import json

config = {
    "workspaces": [
        {
            "api_token": "ntn_your_token_here",
            "sync_public_pages": False,
        },
    ],
}

print(base64.b64encode(json.dumps(config).encode()).decode())
```

Set the output in an environment variable:

```bash
export NOTION_CONFIG="eyJ3b3Jrc3BhY2VzIjogW3siLi4u"
```

Each token must resolve to a unique workspace. User, bot, and page node IDs are
scoped by the workspace ID returned by Notion, so the same identity can safely
appear in more than one workspace.

Set `sync_public_pages` to `true` only when the connection has Read content and
the additional search cost is acceptable. Grant the connection access to the
desired root pages from its **Content access** tab; access is inherited by their
children. Search responses are processed in
bounded batches so high-cardinality workspaces do not require retaining every
page object in memory. The sync stores page metadata such as
title, URL, public URL, timestamps, parent ID, and creator. It never stores page
body or comment content.

## Run Cartography

```bash
cartography \
  --selected-modules notion \
  --notion-config-env-var NOTION_CONFIG
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `403 Forbidden` from `/v1/users` | Enable the connection's read-user capability, including email access if ontology mapping is required. |
| Personal access token error | Use an internal connection secret or public OAuth connection token. Notion personal access tokens cannot list workspace users. |
| `403 Forbidden` from `/v1/search` | Disable `sync_public_pages` or grant the connection Read content. |
| Missing email properties | Notion omits email unless the connection has the appropriate user capability. |
| Invalid configuration error | Confirm the environment variable contains base64-encoded JSON with a non-empty `workspaces` list. |

## References

- [Notion list users API](https://developers.notion.com/reference/get-users)
- [Notion retrieve token bot API](https://developers.notion.com/reference/get-self)
- [Notion internal connections](https://developers.notion.com/guides/get-started/internal-connections)
- [Notion public connections](https://developers.notion.com/guides/get-started/public-connections)
- [Notion personal access token limitations](https://developers.notion.com/guides/get-started/personal-access-tokens)
- [Notion search limitations](https://developers.notion.com/reference/search-optimizations-and-limitations)
- [Notion user object](https://developers.notion.com/reference/user)
- [Notion token security](https://developers.notion.com/guides/get-started/handling-api-keys)
