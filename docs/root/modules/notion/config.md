# Notion Configuration

Configure at least one Notion workspace and API token before running this
module.

## Authentication

Create a Notion personal access token or internal connection with the **Read
user information including email addresses** capability. Store the token in a
secret manager or environment variable; base64 encoding the module config does
not encrypt it.

## Required Permissions

| Capability | Purpose |
|------------|---------|
| Read user information including email addresses | Inventory workspace people and bot connections and map people by email |

The module does not request access to page or database content.

## Configure Cartography

Cartography accepts a base64-encoded JSON object so multiple workspaces and
their credentials can be configured together:

```python
import base64
import json

config = {
    "workspaces": [
        {
            "workspace_id": "stable-workspace-id",
            "workspace_name": "Engineering",
            "api_token": "ntn_your_token_here",
            "scim_token": "optional_enterprise_scim_token",
        },
    ],
}

print(base64.b64encode(json.dumps(config).encode()).decode())
```

Set the output in an environment variable:

```bash
export NOTION_CONFIG="eyJ3b3Jrc3BhY2VzIjogW3siLi4u"
```

Workspace IDs must be unique within the configuration. User and bot node IDs
are scoped by this value so the same Notion identity can safely appear in more
than one workspace.

`scim_token` is optional and requires a Notion Enterprise workspace. Organization
owners generate one token per workspace under **Manage organization** →
**General** → **SCIM provisioning**. When omitted, Cartography does not modify or
clean previously ingested SCIM properties, groups, memberships, or reporting
relationships.

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
| `401 Unauthorized` from `/scim/v2` | Replace the revoked or invalid workspace-specific Enterprise SCIM token. |
| Missing email properties | Notion omits email unless the connection has the appropriate user capability. |
| Invalid configuration error | Confirm the environment variable contains base64-encoded JSON with a non-empty `workspaces` list. |

## References

- [Notion list users API](https://developers.notion.com/reference/get-users)
- [Notion user object](https://developers.notion.com/reference/user)
- [Notion SCIM provisioning](https://www.notion.com/help/provision-users-and-groups-with-scim)
- [Notion token security](https://developers.notion.com/guides/get-started/handling-api-keys)
