## Tailscale Configuration

Cartography supports two ways to authenticate to the Tailscale API:

- **OAuth client (recommended)** — tag-scoped, not tied to a user, exchanged at sync time for a short-lived bearer token. Matches Tailscale's [recommended pattern for service integrations](https://tailscale.com/kb/1215/oauth-clients).
- **API access token** — long-lived, tied to a user account.

In both cases, pass `--tailscale-org <tailnet-name>` (find it under [Settings → General](https://login.tailscale.com/admin/settings/general)). For self-hosted instances, set `--tailscale-base-url` (default `https://api.tailscale.com/api/v2`); the same base URL is used for the OAuth token endpoint.

### OAuth client (recommended)

1. Create an OAuth client at [Settings → OAuth clients](https://login.tailscale.com/admin/settings/oauth) with the read-only scopes cartography needs:

    - `devices:core:read` — `/tailnet/:org/devices`
    - `devices:posture_attributes:read` — `/device/:id/attributes`
    - `users:read` — `/tailnet/:org/users`
    - `policy_file:read` — `/tailnet/:org/acl`
    - `feature_settings:read` — `/tailnet/:org/settings` and `/tailnet/:org/posture/integrations`

    See [trust credentials](https://tailscale.com/docs/reference/trust-credentials) for the canonical scope list.
2. Put the client ID and secret in two environment variables and pass their names to cartography:

    ```bash
    export TS_OAUTH_CLIENT_ID="<client id>"
    export TS_OAUTH_CLIENT_SECRET="<client secret>"

    cartography \
      --tailscale-oauth-client-id-env-var TS_OAUTH_CLIENT_ID \
      --tailscale-oauth-client-secret-env-var TS_OAUTH_CLIENT_SECRET \
      --tailscale-org example.com
    ```

Cartography will exchange the credentials at `{base_url}/oauth/token` (RFC 6749 `client_credentials` grant) and use the returned access token for the rest of the sync.

### API access token

1. Create an API access token at [Settings → Keys](https://login.tailscale.com/admin/settings/keys).
2. Export it (e.g. `TAILSCALE_TOKEN`) and pass `--tailscale-token-env-var TAILSCALE_TOKEN`.

If both `--tailscale-token-env-var` and the OAuth client flags are set, the OAuth client is used and a warning is logged.
