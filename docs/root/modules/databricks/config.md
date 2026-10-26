# Databricks Configuration

## Authentication

Choose one workspace authentication method:

### OAuth M2M

Create a dedicated workspace service principal with a client ID and OAuth
secret. Store the secret in an environment variable. Cartography requests the
`all-apis` OAuth scope automatically.

### Personal Access Token

When generating the personal access token, select **Other APIs** and
**all APIs (not recommended)**. Store the token in an environment variable,
prefer a short lifetime, and revoke it after testing.

## Required Permissions

Grant the workspace user or service principal the workspace admin role. Full
ingestion requires workspace admin privileges to enumerate SCIM users, groups,
service principals, and the token management API.

Cartography inventory requests use read-only `GET` operations. Databricks API
scopes can authorize both reads and mutations, and `all-apis` does not override
the principal's permissions.

## Configure Cartography

Pass the workspace URL with `--databricks-workspace-url`.

For OAuth M2M, pass the client ID with `--databricks-client-id` and the secret
environment variable name with `--databricks-client-secret-env-var`.

For a personal access token, pass its environment variable name with
`--databricks-token-env-var`.

## Run Cartography

Run with OAuth M2M:

```bash
cartography \
  --selected-modules databricks \
  --databricks-workspace-url "$DATABRICKS_WORKSPACE_URL" \
  --databricks-client-id "$DATABRICKS_CLIENT_ID" \
  --databricks-client-secret-env-var DATABRICKS_CLIENT_SECRET
```

Run with a personal access token:

```bash
cartography \
  --selected-modules databricks \
  --databricks-workspace-url "$DATABRICKS_WORKSPACE_URL" \
  --databricks-token-env-var DATABRICKS_TOKEN
```

## Advanced Configuration

### Account-Level Coverage

Account API coverage is available for AWS and GCP. Create an account-level
service principal with an OAuth secret and grant it the account admin role.

Pass `--databricks-account-id`, `--databricks-account-client-id`, and the
secret environment variable name with
`--databricks-account-client-secret-env-var`. All three options must be
provided together.

The account host defaults to `https://accounts.cloud.databricks.com`. Override
it with `--databricks-account-host`, for example
`https://accounts.gcp.databricks.com`.

The Azure Account API is not currently wired into this module. Azure workspace
resources are covered by the `azure` module, and account-level identity
federates through Entra.

### Syncing Several Workspaces Into One Graph

Each run covers one workspace. To sync several workspaces into one graph from
Python, call `start_databricks_ingestion` once per workspace with the same
`update_tag` and `databricks_skip_cleanup=True` on the `Config`, then call
`cartography.intel.databricks.cleanup_databricks` once with the results of the
runs that succeeded. Deferring cleanup keeps one workspace's run from pruning
data that another workspace has not loaded yet, and leaves a failed
workspace's data in place.

Unity Catalog objects are cleaned once per metastore. When a workspace fails,
pass its metastore id in `skip_metastore_ids` so objects only that workspace
lists are kept until its next successful run.

### Workspace Identity

`DatabricksWorkspace` nodes are keyed on the numeric workspace ID, which the
workspace API reports in its `x-databricks-org-id` response header and the
account API reports as `workspace_id`. The host is kept in the `host`
property. Earlier versions keyed workspaces on their host, which split one
workspace into two nodes when its host was not the
`<deployment>.cloud.databricks.com` form, and prefixed every workspace-scoped
node ID with the host. The first sync after upgrading deletes each host-keyed
workspace node and the resources under it, then reloads them under the
numeric ID. Queries or saved views that reference workspace IDs or
workspace-scoped node IDs by host need updating.

### Clean Room Coverage

Cartography lists clean rooms only when the metastore enables external
OpenSharing. Clean room ingestion is skipped when external access is disabled.

## References

- [Databricks API scope reference](https://docs.databricks.com/api/workspace/api/scopes)
