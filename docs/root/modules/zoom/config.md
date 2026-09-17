# Zoom Configuration

Configure an account-level Server-to-Server OAuth app to inventory a Zoom account.

## Prerequisites

- A Zoom account owner or administrator who can create and activate a
  Server-to-Server OAuth app and assign its user-read scope.
- Access to the app's account ID, client ID, and client secret.

## Authentication

Create a **Server-to-Server OAuth** app in the
[Zoom App Marketplace](https://marketplace.zoom.us/), add the scope below, and
activate the app. Copy the account ID, client ID, and client secret from its
credentials page. The account ID is the app's OAuth account identifier, not an
email, vanity domain, or display account number.

Cartography exchanges these credentials at `https://zoom.us/oauth/token` with
the `account_credentials` grant. Tokens last approximately one hour; Cartography
renews them automatically. No interactive login or refresh token is needed.

## Required Permissions

| Granular OAuth scope | Read operation |
| --- | --- |
| `user:read:list_users:admin` | `GET /v2/users` for active, inactive, and pending users |

The older `user:read:admin` scope is also accepted by the endpoint, but the
granular scope above is sufficient. No write, meeting, recording, billing,
group-list, or role-list scopes are required.

## Configure Cartography

| Option | Value |
| --- | --- |
| `--zoom-account-id` | Account ID from the OAuth app |
| `--zoom-client-id` | Client ID from the OAuth app |
| `--zoom-client-secret-env-var` | Name of the environment variable containing the secret; defaults to `ZOOM_CLIENT_SECRET` |

```bash
export ZOOM_CLIENT_SECRET='your-client-secret'
```

## Run Cartography

```bash
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules zoom,ontology \
  --zoom-account-id your-account-id \
  --zoom-client-id your-client-id
```

## Advanced Configuration

Run Cartography separately for each account using that account's OAuth app.
Cleanup is scoped to the configured account. This module targets Zoom's commercial
`zoom.us` service; Zoom for Government endpoints are not supported.

## Troubleshooting

- **401**: Check the credentials and app activation. An expired API token is
  renewed once automatically; repeated authorization failures abort the sync.
- **403 or insufficient scope**: Add `user:read:list_users:admin` to the active
  app and verify the app owner's permissions.
- **429**: Zoom's Users API has the `MEDIUM` rate-limit label. Requests honor
  `Retry-After` and retry up to three times. A sustained rate limit aborts the
  sync without deleting prior users; retry after the quota resets.
- **Incomplete/repeated pagination**: Retry the sync. Page tokens expire after
  15 minutes, and a truncated list is not safe for stale-user cleanup.

## References

- [Zoom Users API: List users](https://developers.zoom.us/docs/api/users/#tag/users/GET/users)
- [Zoom Users API specification](https://developers.zoom.us/api-hub/users/methods/endpoints.json)
- [Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/s2s-oauth/)
- [OAuth scopes](https://developers.zoom.us/docs/integrations/oauth-scopes-overview/)
- [API rate limits](https://developers.zoom.us/docs/api/rest/rate-limits/)
