# Pylon configuration

To sync a Pylon organization, give Cartography a Pylon API token. Cartography
reads the organization, its users, its API token identities and bots, its
roles, and its teams. It doesn't read customer data such as accounts, contacts,
or issues.

## Authentication

Only Pylon Admins can create API tokens. To create a token:

1. In Pylon, go to **Settings > Integrations & dev > API**.
1. On the **Tokens** tab, click **Create API Token**, and enter a name.
1. Leave **Act as user or bot** empty, and pick a role for the token. See
   [Required permissions](#required-permissions).
1. Optional: Add the public egress IP addresses of the host that runs
   Cartography to the token's **IP allowlist**.
1. Click **Create**, and copy the token. Pylon shows it only once.

Pylon API tokens have no scopes, and they don't expire. A token can do only
what its role allows. A token that acts as a user or bot uses that account's
current role instead, and Pylon deletes the token when that user is
deactivated. To keep the sync running when people leave, give the token its
own identity or have it act as a [bot](https://docs.usepylon.com/pylon-docs/developer/api/authentication#bots).

The `pylon_admin_service_accounts` rule flags active token identities and bots
with the built-in Admin role because both appear as service accounts without
email addresses. A token acting as a user escapes detection because Pylon
returns only the user's identity and email.

## Required permissions

Cartography only reads data. It calls these endpoints:

| API endpoint | Cartography data | Likely role permission |
| --- | --- | --- |
| `GET /me` | `PylonOrganization` | Any valid token |
| `GET /user-roles` | `PylonRole` | **Users**: View |
| `GET /users?include_deactivated=true` | `PylonUser`, `PylonServiceAccount` | **Users**: View |
| `GET /teams` | `PylonTeam` | **Teams**: View |

The Pylon API reference doesn't list the permission that each endpoint needs,
so the permissions in the table are inferred from the role's permission
categories. A token with the Admin role can read every endpoint. To follow
least privilege on the Enterprise plan, create a custom role with view access
to **Users** and **Teams** and no other access, and check that a sync
succeeds.

`GET /users` also returns API tokens that have their own identity and bots.
These have no email address, so Cartography loads them as
`PylonServiceAccount` nodes with their roles. The API doesn't return a token's
value, creator, last use, or IP allowlist; check those in
**Settings > Integrations & dev > API**.

## Configure Cartography

| CLI option | Description |
| --- | --- |
| `--pylon-api-token-env-var` | Name of the environment variable that holds the Pylon API token. If you omit this option or the variable is unset or empty, Cartography logs an info message and skips Pylon. |
| `--pylon-base-url` | Pylon API base URL. Optional. By default, tokens that start with `pylon_api_eu_` use `https://api.eu.usepylon.com`, and every other token uses `https://api.usepylon.com`. |

## Run Cartography

```bash
export PYLON_API_TOKEN="pylon_api_..."
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules pylon \
  --pylon-api-token-env-var PYLON_API_TOKEN
```

## Troubleshooting

- **`401` with `wrong_region_token`**: The token belongs to the other region.
  Set `--pylon-base-url` to the URL that the error message names.
- **`401` with `invalid_api_token`**: The token was deleted or rotated, or the
  request came from an address outside the token's IP allowlist.
- **`403` on `/user-roles`, `/users`, or `/teams`**: The token's role can't
  view users or teams. Change the token's role in
  **Settings > Integrations & dev > API**.
- **`429`**: Pylon shares each endpoint's per-minute rate limit across every
  token in the organization. Cartography retries with the `Retry-After` delay.

## References

- [Pylon API authentication](https://docs.usepylon.com/pylon-docs/developer/api/authentication)
- [Pylon roles and user management](https://docs.usepylon.com/pylon-docs/platform/roles-and-user-management)
- [Pylon API reference](https://docs.usepylon.com/pylon-docs/developer/api/api-reference)
