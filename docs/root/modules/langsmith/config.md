# LangSmith Configuration

Cartography needs one LangSmith credential with organization-level read access: a
service key (`lsv2_sk_…`) or a personal access token (`lsv2_pt_…`).

## Prerequisites

- A LangSmith organization. Custom roles and attribute-based access policies are
  Enterprise features. If your plan doesn't include them, those parts of the graph are
  empty.
- A role that holds the permissions listed in [Required Permissions](#required-permissions).
  The Organization Admin role holds all of them. A custom role that grants the same read
  permissions also works.

## Authentication

### Service key

A service key belongs to the organization rather than to a person, so it keeps working
when people leave.

1. In LangSmith, go to **Settings > API Keys** and create a service key.
1. Give it an organization role that holds the [required permissions](#required-permissions),
   and an expiry.
1. Store the key in an environment variable:

   ```bash
   export LANGSMITH_PAT="lsv2_sk_..."
   ```

A service key can't list tracing keys: LangSmith requires a user identity for that listing.
Cartography logs a warning and skips them.

### Personal access token

1. In LangSmith, go to **Settings > Personal access tokens** and create a token.
1. Store the token in an environment variable:

   ```bash
   export LANGSMITH_PAT="lsv2_pt_..."
   ```

A personal access token stops working when its owner is deactivated.

Either credential expires if your organization sets a maximum lifetime for it, and the sync
then fails with `401`. Rotate it before it expires.

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
| `rules:read` | Webhooks that automation rules send runs to | Cartography logs a warning and skips that workspace's webhooks. |
| `bulk-exports:read` | Bulk export destinations | Cartography logs a warning and skips that workspace's export destinations. |

LangSmith evaluates permissions per workspace. If the token holds `workspaces:read` in
only some workspaces, the graph covers only those workspaces, and Cartography logs a
warning for each workspace that it skips. Workspace resources belong to their workspace in
the graph, so a workspace that the token can't read keeps its nodes while every other
workspace is still cleaned up.

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
| `403 Forbidden` on workspace routes | The token has no role in that workspace. Cartography logs a warning, continues, and skips cleanup in that workspace only. |
| Timeouts logged for some routes | LangSmith was slow or unreachable. Cartography logs a warning, keeps the existing nodes for those routes, and retries on the next run. |
| No `LangSmithAgentCredential` nodes | The token lacks `deployments:read`, or no agent has completed an OAuth flow yet. Agent auth looks connections up by assistant ID, so Cartography queries only agents whose ID is a UUID: registry agents with a user-chosen ID can't be looked up. |
| No `LangSmithApiKey` nodes with `key_type = pat` for other members | The token lacks `organization:pats:read`. |
| `401 Unauthorized` on every route | The token expired, or LangSmith deactivated the identity that owns it. LangSmith rejects tokens that belong to a deactivated identity. |
| No custom `LangSmithRole` nodes | Your plan doesn't include custom roles. |

When the organization disables public sharing, LangSmith serves none of its share links or
public repos, so Cartography doesn't list them and removes any `LangSmithPublicShare`
nodes.

## Security rules

Run the LangSmith rules against the ingested graph with `cartography-rules run`. See
[Running Rules](../../usage/rules.md) for connection options. All of them are
experimental.

| Rule | Flags |
| --- | --- |
| `langsmith_api_key_never_expires` | Unrevoked keys with no expiry. |
| `langsmith_api_key_unused` | Live keys and SCIM tokens unused for 90 days, or never used 30 days after creation. |
| `langsmith_key_lifetime_uncapped` | Organizations with no maximum lifetime for personal access tokens, service keys, or API keys. Plans without the setting also report no cap. |
| `langsmith_sso_not_enforced` | Organizations with SAML SSO configured that still accept other logins. |
| `langsmith_sso_default_role_can_deploy` | Just-in-time provisioning whose default role can deploy code, manage members, keys, or secrets, or send data out. |
| `langsmith_public_share` | Runs, datasets, threads, and repos readable without an account, in organizations that allow public sharing. |
| `langsmith_shareable_deployment` | Deployments any LangSmith user can run in Studio. |
| `langsmith_deployment_static_cloud_credentials` | Deployments whose environment holds long-lived cloud credentials, judged by secret name. |
| `langsmith_webhook_plaintext` | Enabled webhooks that deliver over `http`. |
| `langsmith_oauth_client_insecure_redirect` | OAuth clients that accept an `http` redirect URI: any for a confidential client, or a non-loopback one for a public client. |
| `langsmith_bulk_export_static_credentials` | Bulk export destinations that authenticate with a stored access key instead of an IAM role. |
| `langsmith_disabled_member_credentials` | Agent OAuth tokens and tracing keys that keep working after their member is deactivated. |

A rule that evaluated no assets had nothing to test, which doesn't mean the organization
is secure. For example, the agent-credential check needs `deployments:read`.

## References

- [LangSmith API reference](https://docs.langchain.com/langsmith/smith-api-ref)
- [Manage your organization using the API](https://docs.langchain.com/langsmith/manage-organization-by-api)
- [Organization and workspace operations reference](https://docs.langchain.com/langsmith/organization-workspace-operations)
- [Role-based access control](https://docs.langchain.com/langsmith/rbac)
- [Set up Agent Auth](https://docs.langchain.com/langsmith/agent-auth)
