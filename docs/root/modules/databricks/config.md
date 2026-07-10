## Databricks Configuration

Follow these steps to analyze Databricks objects with Cartography.

1. Pass your workspace URL via `--databricks-workspace-url`, e.g. `https://dbc-xxxx.cloud.databricks.com`.
1. Provide credentials with one of the following:
    - **Personal Access Token (PAT)**: populate an environment variable with the PAT and pass its name via `--databricks-token-env-var`.
    - **OAuth M2M (workspace service principal)**: create a workspace-level service principal with a client ID and secret, then pass `--databricks-client-id` and the env var name holding the secret via `--databricks-client-secret-env-var`.

The principal used by Cartography needs workspace admin privileges to enumerate SCIM users, groups, service principals, and to read the token management API.

Account-level coverage (Accounts API, federation policies, workspace assignments, cross-cloud links to AWS/GCP/Azure) is added in follow-up PRs and will introduce dedicated `--databricks-account-*` options.
