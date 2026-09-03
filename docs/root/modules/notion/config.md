# Notion Configuration

Configure at least one Notion connection token before running this module.

## Authentication

Create an internal Notion connection with the **Read user information including
email addresses** capability. Public OAuth connection tokens are also supported.
Personal access tokens are not supported because Notion does not allow them to
list workspace users.

Store tokens in a secret manager or environment variable; base64 encoding the
module config does not encrypt it. Cartography discovers the workspace ID and
name from each connection token.

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
the additional search cost is acceptable. The sync stores page metadata such as
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
- [Notion personal access token limitations](https://developers.notion.com/guides/get-started/personal-access-tokens)
- [Notion search limitations](https://developers.notion.com/reference/search-optimizations-and-limitations)
- [Notion user object](https://developers.notion.com/reference/user)
- [Notion token security](https://developers.notion.com/guides/get-started/handling-api-keys)
