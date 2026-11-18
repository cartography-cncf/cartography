# Bitbucket Cloud Configuration

Cartography needs a Bitbucket Cloud credential and at least one workspace slug to sync workspaces, projects, repositories, and members.

```{note}
`--bitbucket-workspaces` is required. Bitbucket permanently removed the "list every workspace I can see" endpoint in 2026 (Atlassian's CHANGE-2770). Cartography must now always be provided with the workspace slug(s).
```

## Authentication

### API token or Access token

Both use the same `Authorization: Bearer <token>` header, so either works with `--bitbucket-auth-method token` (the default):

- An **API token** is tied to a user account. Create one from your Atlassian account settings under "API tokens with scopes", selecting Bitbucket as the app and granting the scopes listed below.
- An **Access token** is tied to a repository, project, or workspace instead of a user, so it keeps working if the creating user's account is later deactivated. Create a **workspace-level** access token from the workspace's settings under "Access tokens" - a repository- or project-level token can't see anything outside its own scope, so it can't complete a full sync.

Store the token in an environment variable and point Cartography at it:

```bash
export BITBUCKET_TOKEN=<your token>
cartography --bitbucket-token-env-var BITBUCKET_TOKEN ...
```

### OAuth client

Bitbucket Cloud has no client-credentials grant (no machine-to-machine mode with zero human interaction), so this needs one manual, one-time step to obtain a refresh token. After that, Cartography exchanges the refresh token for a new ~2-hour access token automatically for the life of every sync - you never repeat the manual step unless the refresh token is revoked.

1. **Create the OAuth client.** In the workspace, go to workspace settings > Apps and features > OAuth clients > Create OAuth Client.
   - **Details** tab: give it a name, e.g. `cartography`.
   - **Authorization** tab: set the grant type to **Authorization Code**, and enter a callback URL. Any URL works, even one that doesn't resolve to anything, such as `https://localhost/callback` - you only need to read the `code` parameter off the URL you get redirected to in step 2, not have anything actually running there.
   - **Scopes** tab: check the scopes listed under [Required Permissions](#required-permissions) above.
   - Save. Bitbucket shows the client's **Key** (client ID) and **Secret** - the secret is only shown once, so save it now.

2. **Get an authorization code.** Visit this URL in a browser, signed in as a user with access to the workspace, substituting the client key:

   ```text
   https://bitbucket.org/site/oauth2/authorize?client_id=<client key>&response_type=code
   ```

   Approve the consent screen. You'll be redirected to your callback URL with a `code` query parameter, e.g. `https://localhost/callback?code=<code>` - the browser will likely show a connection error at that point, which is expected. Copy the `code` value out of the address bar. It's single-use and expires within a couple of minutes, so move on to the next step right away.

3. **Exchange the code for a refresh token.** Run this once, from a machine you trust with the client secret:

   ```bash
   curl -X POST -u "<client id>:<client secret>" \
       https://bitbucket.org/site/oauth2/access_token \
       -d grant_type=authorization_code \
       -d code="<code from step 2>"
   ```

   The response is JSON containing a `refresh_token` field. Save it - this is the long-lived credential Cartography actually uses.

4. **Run Cartography** with the client key, client secret, and refresh token:

   ```bash
   export BITBUCKET_OAUTH_CLIENT_SECRET=<client secret>
   export BITBUCKET_OAUTH_REFRESH_TOKEN=<refresh token from step 3>
   cartography \
       --bitbucket-auth-method oauth \
       --bitbucket-oauth-client-id <client key> \
       --bitbucket-oauth-client-secret-env-var BITBUCKET_OAUTH_CLIENT_SECRET \
       --bitbucket-oauth-refresh-token-env-var BITBUCKET_OAUTH_REFRESH_TOKEN \
       ...
   ```

## Required Permissions

### API Token

For an API token, grant these read-only scopes:

| Scope                         | Used for                                      |
| ----------------------------- | --------------------------------------------- |
| `read:workspace:bitbucket`    | Reading workspaces and workspace membership.  |
| `read:project:bitbucket`      | Listing projects within a workspace.          |
| `read:repository:bitbucket`   | Listing repositories within a workspace.      |

### Access Token

For an Access token, create a **workspace-level** token and grant these scopes:

| Scope              | Used for                                  |
| ------------------ | ----------------------------------------- |
| Account: Read      | Listing workspace members.                |
| Projects: Read     | Listing projects within a workspace.      |
| Repositories: Read | Listing repositories within a workspace.  |

### OAuth Client

For an OAuth client, grant these scopes:

| Scope                        | Used for                                      |
| ---------------------------- | --------------------------------------------- |
| Account: Read                | Listing workspace members.                    |
| Projects: Read               | Listing projects within a workspace.          |
| Repositories: Read           | Listing repositories within a workspace.      |

All permissions above are read-only; Cartography never writes to Bitbucket.

## Configure Cartography

| Option                                       | Environment variable indirection             | Default | Description                                                              |
| --------------------------------------------- | --------------------------------------------- | ------- | -------------------------------------------------------------------------- |
| `--bitbucket-workspaces`                      | -                                              | none    | Comma-separated workspace slugs to sync. Required.                        |
| `--bitbucket-auth-method`                     | -                                              | `token` | Either `token` or `oauth`.                                                |
| `--bitbucket-token-env-var`                    | Reads a Bitbucket API or Access token          | none    | Required when `--bitbucket-auth-method token`.                            |
| `--bitbucket-oauth-client-id`                  | -                                              | none    | Required when `--bitbucket-auth-method oauth`.                            |
| `--bitbucket-oauth-client-secret-env-var`      | Reads the OAuth client secret                  | none    | Required when `--bitbucket-auth-method oauth`.                            |
| `--bitbucket-oauth-refresh-token-env-var`      | Reads the OAuth refresh token                  | none    | Required when `--bitbucket-auth-method oauth`.                            |

## Run Cartography

```bash
export BITBUCKET_TOKEN=<your token>
cartography \
    --neo4j-uri <uri> \
    --selected-modules bitbucket \
    --bitbucket-workspaces my-workspace \
    --bitbucket-token-env-var BITBUCKET_TOKEN
```

List every workspace in one run, for example `--bitbucket-workspaces team-a,team-b`. A user who belongs to several workspaces is a single node, so syncing workspaces in separate runs can remove that user's other workspace memberships until those workspaces sync again.

## Troubleshooting

| Symptom                                    | Likely cause                                                        |
| ------------------------------------------- | --------------------------------------------------------------------- |
| `401 Unauthorized`                          | Token or refresh token is invalid or expired.                        |
| `404 Not Found` on a configured workspace   | The slug is misspelled, or the credential does not belong to that workspace. |
| `403 Forbidden` listing workspace members   | An OAuth client or Access token is missing **Account: Read**, or an API token is missing `read:workspace:bitbucket`. Cartography logs a warning and skips user cleanup for every workspace in that run, rather than deleting users it could not read. |
| `429 Too Many Requests`                     | Bitbucket Cloud rate limit hit. Cartography retries with backoff automatically. |

## References

- [Bitbucket Cloud REST API](https://developer.atlassian.com/cloud/bitbucket/rest/)
- [Using API tokens](https://support.atlassian.com/bitbucket-cloud/docs/using-api-tokens/)
- [Access tokens](https://support.atlassian.com/bitbucket-cloud/docs/access-tokens/)
- [Use OAuth on Bitbucket Cloud](https://support.atlassian.com/bitbucket-cloud/docs/use-oauth-on-bitbucket-cloud/)
