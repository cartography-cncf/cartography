# LangSmith Configuration

Cartography needs one LangSmith credential: a personal access token (`lsv2_pt_…`) that
belongs to a user with organization-level read access.

## Prerequisites

- A LangSmith organization. Custom roles and attribute-based access policies are
  Enterprise features. If your plan doesn't include them, those parts of the graph are
  empty.
- A user who holds the permissions listed in [Required Permissions](#required-permissions).
  The Organization Admin role holds all of them, and it's the role that the module was
  validated with. A custom role that grants the same read permissions also works.

## Authentication

### Personal access token

1. In LangSmith, go to **Settings > Personal access tokens**.
1. Create a token.
1. Store the token in an environment variable:

   ```bash
   export LANGSMITH_PAT="lsv2_pt_..."
   ```

```{note}
A workspace service key (`lsv2_sk_…`) doesn't work. It can't reach the
organization-scoped routes or the organization-wide token inventory.
```

If your organization sets a maximum lifetime for personal access tokens, the token
expires and the sync fails with `401`. Rotate the token before it expires.

## Required Permissions

| Permission | Enables |
| --- | --- |
| `organization:read` | Organizations, members, workspaces, service accounts, SSO settings, SCIM tokens, and access policies |
| `organization:read-metadata` | Organization settings and the role catalog |
| `workspaces:read` | Workspace members, secret key names, resource tags, OAuth clients, and MCP servers |

## Optional Permissions

| Permission | Enables | If absent |
| --- | --- | --- |
| `organization:pats:read` | The organization-wide personal access token inventory | Cartography logs a warning and skips other members' tokens. |
| `deployments:read` | Deployments, agents, OAuth providers, and agent credentials | Cartography logs a warning and skips the agent-to-user OAuth graph for that workspace. |

LangSmith evaluates permissions per workspace. If the token holds `workspaces:read` in
only some workspaces, the graph covers only those workspaces, and Cartography logs a
warning for each workspace that it skips.

Cartography keeps nodes that the token could read before but can't read now. If you
narrow the token's access, stale data stays in the graph until you restore access.

## Configure Cartography

| Option | Default | Purpose |
| --- | --- | --- |
| `--langsmith-pat-env-var` | None | The name of the environment variable that holds the personal access token. Required to enable the module. |
| `--langsmith-api-url` | `https://api.smith.langchain.com` | The LangSmith control plane base URL. |
| `--langsmith-host-api-url` | `https://api.host.langchain.com` | The LangGraph Platform (api-host) base URL. |
| `--langsmith-org-id` | None | The UUID of a single organization to sync. If you omit it, Cartography syncs every organization that the token can see. |

Cartography reads the token from the named environment variable. Don't pass the token on
the command line.

For the EU region, override both URLs:

```bash
--langsmith-api-url https://eu.api.smith.langchain.com \
--langsmith-host-api-url https://eu.api.host.langchain.com
```

## Run Cartography

```bash
LANGSMITH_PAT="lsv2_pt_..." cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules langsmith \
  --langsmith-pat-env-var LANGSMITH_PAT
```

## Advanced Configuration

### Self-hosted deployments

Self-hosted LangSmith serves the LangGraph Platform API from an `/api-host` path on the
same host, not from a separate domain:

```bash
--langsmith-api-url https://langsmith.internal.example.com \
--langsmith-host-api-url https://langsmith.internal.example.com/api-host
```

If the agent-auth endpoints return `405 Method Not Allowed`, add the `/api-host` suffix
to `--langsmith-host-api-url`.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `403 Forbidden` on workspace routes | The token has no role in that workspace. Cartography logs a warning, continues, and skips cleanup for the affected node types. |
| Timeouts logged for some routes | LangSmith was slow or unreachable. Cartography logs a warning, keeps the existing nodes for those routes, and retries on the next run. |
| No `LangSmithAgentCredential` nodes | The token lacks `deployments:read`, or no agent has completed an OAuth flow yet. |
| No `LangSmithApiKey` nodes with `key_type = pat` for other members | The token lacks `organization:pats:read`. |
| `401 Unauthorized` on every route | The token expired, or LangSmith deactivated the identity that owns it. LangSmith rejects tokens that belong to a deactivated identity. |
| No custom `LangSmithRole` nodes | Your plan doesn't include custom roles. |
| Deleted agents stay in the graph | A deployment isn't `READY` or has no URL, so Cartography can't list its agents. Agent cleanup resumes when every deployment serves again or is deleted. |

## References

- [LangSmith API reference](https://docs.langchain.com/langsmith/smith-api-ref)
- [Manage your organization using the API](https://docs.langchain.com/langsmith/manage-organization-by-api)
- [Organization and workspace operations reference](https://docs.langchain.com/langsmith/organization-workspace-operations)
- [Role-based access control](https://docs.langchain.com/langsmith/rbac)
- [Set up Agent Auth](https://docs.langchain.com/langsmith/agent-auth)
