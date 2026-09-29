# Zoom Configuration

Configure an account-level Server-to-Server OAuth app to inventory a Zoom account.

## Prerequisites

- A Zoom account owner or administrator who can create and activate a
  Server-to-Server OAuth app and assign its user-read scope.
- Access to the app's account ID, client ID, and client secret.

A Zoom Workplace Basic account can create this app and read its user inventory.
Zoom's user-management web portal may require a payment method on file before
you can manage additional users on a Basic account; this is separate from
authenticating the read-only connector.

## Authentication

1. Sign in to the [Zoom App Marketplace](https://marketplace.zoom.us/) with the
   account you want to inventory. In the current Marketplace interface, select
   **Developers**, then **+** → **Build app** on the **Created apps** page.
   First-time developers are prompted to review and accept the Marketplace
   Terms of Use and, separately, the API License and Terms of Use.
2. Select **Server to Server OAuth App**, click **Create**, enter an app name,
   and click **Create** again. This creates an account-level app for internal use;
   Marketplace publication and OAuth redirect URLs are not required.
3. On **App Credentials**, copy the **Account ID**, **Client ID**, and **Client
   Secret**. The account ID is the app's OAuth account identifier, not an email,
   vanity domain, or display account number.
4. On **Information**, fill in the short description, company name, and developer
   contact name and email. These fields save automatically.
5. Continue through **Feature** without enabling event subscriptions. The token
   on that page is for webhook verification; it is not the client secret or an
   API access token used by Cartography.
6. On **Scopes**, click **Add Scopes**, search for
   `user:read:list_users:admin`, select **View users** with that exact scope,
   and click **Done**. Leave the scope required, and describe how your deployment
   uses and stores user data in the scope-description field.
7. On **Activation**, click **Activate your app**. Creating credentials or saving
   a scope alone does not activate the app. Confirm that Zoom displays
   **Your app is activated on the account**.

Cartography exchanges these credentials at `https://zoom.us/oauth/token` with
the `account_credentials` grant. Tokens last approximately one hour; Cartography
renews them automatically. You do not need to create or paste a bearer access
token, supply a refresh token, or complete an interactive login when running
Cartography.

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
  --ontology-users-source zoom \
  --zoom-account-id your-account-id \
  --zoom-client-id your-client-id
```

The example uses Zoom as the source for canonical `User` nodes in a standalone
test. For an existing graph, use your normal `--ontology-users-source` setting.

## Verify the sync

Look for the Zoom stage starting and finishing, plus loaded `ZoomAccount` and
`ZoomUser` counts. When `ontology` is selected, canonical `User` nodes and
`HAS_ACCOUNT` relationships should also be present. For example:

```cypher
MATCH (:ZoomAccount)-[:RESOURCE]->(u:ZoomUser)
RETURN u.status AS status, u.plan_type AS plan_type, count(*) AS users;
```

An empty inactive or pending list is valid. A second complete sync updates the
same users without duplicating them. Only users absent from all three status
lists are removed from the current account's scope.

For temporary testing, use a disposable graph. After testing, deactivate the app
on its **Activation** page and remove local credentials and provider data.

## Advanced Configuration

Run Cartography separately for each account using that account's OAuth app.
Cleanup is scoped to the configured account. This module targets Zoom's commercial
`zoom.us` service; Zoom for Government endpoints are not supported.

## Troubleshooting

- **401**: Check the credentials and app activation. An expired API token is
  renewed once automatically; repeated authorization failures abort the sync.
- **403 or insufficient scope**: Add `user:read:list_users:admin` to the active
  app and verify the app owner's permissions.
- **429**: Zoom's Users API has the `MEDIUM` rate-limit label. Requests retry
  up to three times, capping each `Retry-After` delay at eight seconds. A sustained
  rate limit aborts the sync without deleting prior users; retry after the quota resets.
- **Incomplete/repeated pagination**: Retry the sync. Page tokens expire after
  15 minutes. Each status list has a safety limit of 10,000 pages; hitting it or
  receiving a truncated list aborts the sync before stale-user cleanup.

## References

- [Zoom Users API: List users](https://developers.zoom.us/docs/api/users/#tag/users/GET/users)
- [Zoom Users API specification](https://developers.zoom.us/api-hub/users/methods/endpoints.json)
- [Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/s2s-oauth/)
- [OAuth scopes](https://developers.zoom.us/docs/integrations/oauth-scopes-overview/)
- [API rate limits](https://developers.zoom.us/docs/api/rest/rate-limits/)
