# LangSmith Configuration

Cartography needs one LangSmith credential: a **personal access token** (`lsv2_pt_…`)
belonging to a user with organization-level read access.

## Prerequisites

- A LangSmith organization. RBAC custom roles and attribute-based access policies are
  Enterprise features; if your plan does not include them, those parts of the graph
  are simply empty.
- The account creating the token must be able to read organization settings. In
  practice this means **Organization Admin**.

## Authentication

### Personal access token

Create one in the LangSmith UI under **Settings → Personal access tokens**, or with
`POST /api/v1/api-key`. Store it in an environment variable:

```bash
export LANGSMITH_PAT="lsv2_pt_..."
```

```{note}
A workspace service key (`lsv2_sk_…`) is **not** sufficient. Organization-scoped
routes and the organization-wide token inventory are unreachable with one, and
`/api/v1/orgs` and `/api/v1/orgs/permissions` accept only a bearer token, which
service keys cannot provide.
```

If your organization sets a maximum personal access token lifetime, the token will
expire and the sync will start failing with `401`. Rotate it on that cadence.

## Required Permissions

| Permission | Enables |
| --- | --- |
| `organization:read` | Organizations, members, workspaces, service accounts, SSO settings, SCIM tokens, access policies |
| `organization:read-metadata` | Organization settings and the role catalog |
| `workspaces:read` | Workspace members, secrets key names, resource tags, OAuth clients, MCP servers |

## Optional Permissions

| Permission | Enables | If absent |
| --- | --- | --- |
| `organization:pats:read` | The organization-wide personal access token inventory | Other members' tokens are not ingested; a warning is logged |
| `deployments:read` | Deployments, agents, OAuth providers and agent credentials | The agent-to-user OAuth graph is not built for that workspace; a warning is logged |

Permissions are evaluated per workspace. A token that holds `workspaces:read` in
only some workspaces produces a graph covering only those workspaces; each skipped
workspace logs a warning rather than failing the sync.

## Configure Cartography

| Option | Default | Purpose |
| --- | --- | --- |
| `--langsmith-pat-env-var` | none | Name of the environment variable holding the personal access token. Required to enable the module. |
| `--langsmith-api-url` | `https://api.smith.langchain.com` | LangSmith control plane base URL. |
| `--langsmith-host-api-url` | `https://api.host.langchain.com` | LangGraph Platform (api-host) base URL. |
| `--langsmith-org-id` | none | Restrict the sync to a single organization UUID. Omit to sync every organization the token can see. |

The token is read from the named environment variable, never passed on the command
line.

For the EU region, or a self-hosted instance, override both URLs:

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

Self-hosted LangSmith serves the LangGraph Platform API under an `/api-host` path on
the same host rather than on a separate domain:

```bash
--langsmith-api-url https://langsmith.internal.example.com \
--langsmith-host-api-url https://langsmith.internal.example.com/api-host
```

A `405 Method Not Allowed` from the agent-auth endpoints means
`--langsmith-host-api-url` is missing the `/api-host` suffix.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `403 Forbidden` on workspace routes | The token lacks a role in that workspace. The sync logs a warning and continues. |
| No `LangSmithAgentCredential` nodes | The token lacks `deployments:read`, or no agent has completed an OAuth flow yet. |
| No other members' `LangSmithApiKey` nodes with `key_type = pat` | The token lacks `organization:pats:read`. |
| `401 Unauthorized` on every route | The token expired, or the owning identity was deactivated — LangSmith rejects tokens belonging to a disabled identity. |
| Empty `LangSmithRole` custom roles | RBAC is not enabled on the organization's plan. |

## References

- [LangSmith API reference](https://docs.langchain.com/langsmith/smith-api-ref)
- [Manage your organization using the API](https://docs.langchain.com/langsmith/manage-organization-by-api)
- [Organization and workspace operations reference](https://docs.langchain.com/langsmith/organization-workspace-operations)
- [Role-based access control](https://docs.langchain.com/langsmith/rbac)
- [Set up Agent Auth](https://docs.langchain.com/langsmith/agent-auth)
