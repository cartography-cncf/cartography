## Databricks Configuration

Follow these steps to analyze Databricks objects with Cartography.

1. Pass your workspace URL via `--databricks-workspace-url`, e.g. `https://dbc-xxxx.cloud.databricks.com`.
1. Provide credentials with one of the following:
    - **OAuth M2M (recommended)**: create a dedicated workspace service principal with a client ID and OAuth secret, then pass `--databricks-client-id` and the env var name holding the secret via `--databricks-client-secret-env-var`. Cartography requests the `all-apis` OAuth scope automatically.
    - **Personal Access Token (PAT)**: when generating the PAT, select **Other APIs** and **all APIs (not recommended)**. Populate an environment variable with the PAT and pass its name via `--databricks-token-env-var`. Prefer a short lifetime and revoke the token after testing.
1. Grant the user or service principal the workspace admin role. Full ingestion requires workspace admin privileges to enumerate SCIM users, groups, service principals, and the token management API.

Cartography's inventory requests use read-only `GET` operations. The credential itself is not read-only: Databricks API scopes authorize families of operations that can include both reads and mutations, and `all-apis` does not override the principal's permissions. See the [Databricks API scope reference](https://docs.databricks.com/api/workspace/api/scopes).

### Account-level coverage (AWS / GCP)

The Databricks Account API (`accounts.cloud.databricks.com` on AWS, `accounts.gcp.databricks.com` on GCP) is enabled separately. Azure has its own account API (`accounts.azuredatabricks.net`), but it is not yet wired into this module: on Azure the workspace resource is provisioned through Azure Resource Manager and covered by the `azure` module, and account-level identity federates through Entra. So the `--databricks-account-*` flags below apply to AWS and GCP today.

1. Create an account-level service principal with an OAuth secret and grant it the account admin role.
1. Pass `--databricks-account-id`, `--databricks-account-client-id`, and the env var name holding the secret via `--databricks-account-client-secret-env-var`. The account host defaults to `https://accounts.cloud.databricks.com`; override it with `--databricks-account-host` (e.g. `https://accounts.gcp.databricks.com`).

When the account flags are set, Cartography also ingests account SCIM users / groups / service principals, workspace assignments, federation policies, and the workspace cloud configurations (credentials, storage, network, encryption keys, VPC endpoints, log delivery, budgets), linking them to the AWS / GCP resources already in the graph. All three account flags must be provided together; when none are set the module runs workspace-only.
