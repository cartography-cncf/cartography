# Sweet Security Configuration

Configure a Sweet API token and a stable tenant identifier.

## Authentication

1. In the [Sweet app](https://app.sweet.security), click your name, and then
   click **Settings**.
2. Click **API Tokens**, and then create a token with a read-only role and an
   expiration date.
3. Store the API key and its secret in environment variables.

Cartography exchanges the key and secret for a JSON Web Token (JWT) at
`POST /v1/auth/token`. The JWT is valid for one day.

## Required Permissions

The token's role must allow the following read operations:

| Operation | Used for |
|-----------|----------|
| `GET /v1/aws/account` | AWS account connections |
| `GET /v1/aws/organization` | AWS organization connections |
| `GET /v1/vulnerability` | Runtime vulnerabilities |
| `GET /v1/attack` | Attack chains |

## Configure Cartography

The Sweet API has no endpoint that returns the tenant's own ID, so you set one
with `--sweet-tenant-id`. Pick a value that stays the same across runs, such
as your Sweet tenant name. It becomes the `SweetTenant` node ID that scopes
cleanup. Use a different value for each tenant you sync into the same graph.

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--sweet-tenant-id` |  | Yes | Stable identifier for the Sweet tenant. Cartography skips the module if this option isn't set. |
| `--sweet-api-key-env-var` | `SWEET_API_KEY` | No | Name of the environment variable that contains the API key. The variable itself must be set. |
| `--sweet-api-secret-env-var` | `SWEET_API_SECRET` | No | Name of the environment variable that contains the API secret. The variable itself must be set. |
| `--sweet-api-url` | `https://eapi.sweet.security` | No | Sweet API origin, an HTTPS URL without a path. |

When `--sweet-tenant-id` is set, the run fails if either credential variable is
empty or unset, or if `--sweet-api-url` is not a valid HTTPS origin. This keeps
a misconfigured run from looking like a successful sync.

## Run Cartography

```bash
export SWEET_API_KEY="..."
export SWEET_API_SECRET="..."

cartography \
  --selected-modules sweet \
  --sweet-tenant-id my-sweet-tenant
```

## Troubleshooting

- HTTP `401` from `/v1/auth/token`: Check that the API key and secret are
  correct and that the token hasn't expired.
- HTTP `403`: Check that the token's role can read the endpoints in
  [Required Permissions](#required-permissions).
- HTTP `429`: Cartography retries with backoff and honors `Retry-After`. If
  rate limiting persists, the run fails. The feed that failed, and the feeds
  after it, keep their existing data because their cleanup doesn't run. Feeds
  that finished earlier in the run (AWS connections sync first, then
  vulnerabilities, then attack chains) are already updated.

## References

- [Sweet Security API reference](https://eapi.sweet.security/docs)
