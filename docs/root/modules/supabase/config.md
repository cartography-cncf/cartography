## Supabase Configuration

Follow these steps to analyze Supabase objects with Cartography.

1. Prepare your Supabase personal access token
    1. Create a [personal access token](https://supabase.com/dashboard/account/tokens). The token inherits your own permissions, so use an account with read access to every organization you want to inventory.
    1. Populate an environment variable with the token. Pass the environment variable name via CLI with `--supabase-access-token-env-var`.
1. Optionally restrict the sync to specific organizations by passing a comma-separated list of organization slugs with `--supabase-organizations`. When omitted, every organization the token can see is synced.
1. Optionally override the API base URL with `--supabase-base-url` (default: `https://api.supabase.com`).

### What the module reads

Cartography only issues `GET` requests against the [Management API](https://supabase.com/docs/reference/api/introduction) and never fetches secret material:

- Project API keys are listed without the `reveal` parameter. Note that the endpoint returns the full key value anyway, including the `service_role` secret, so the value does pass through Cartography's memory; it is dropped during transformation and only the key id, name, type, prefix and server-side hash are stored.
- Edge function secrets are stored by name and last-updated timestamp; the values returned by the API are dropped before ingestion.
- The `jwt_secret` field from the PostgREST config, the pooler connection strings, the auth captcha secret, SMTP credentials and webhook hook secrets are all dropped.
- The pgsodium root key endpoint and the saved SQL snippets endpoint are never called.

### Plan-gated endpoints

Several endpoints require a paid plan or a GitHub integration: database branches, custom hostnames, vanity subdomains, network restrictions and point-in-time recovery. When they answer `402`, `403` or `404`, or a `400` carrying the `entitlement_required` error code (which is what the custom-hostname and vanity-subdomain endpoints actually return on a free-tier organization), the module logs a warning and continues, so a free-tier project syncs cleanly with those properties left unset.

An unreadable endpoint never deletes anything. "We could not list this" is treated differently from a `200` returning an empty list: only the latter runs a cleanup. So losing an entitlement, having a token scope revoked or hitting a transient `403` leaves the previously-ingested keys, branches, buckets, secrets and findings in the graph rather than silently erasing them. Stale data is recoverable on the next successful sync; deleted data is not.

### Rate limits

The Management API allows 120 requests per minute by default. The module issues roughly 20 requests per project plus 2 per organization, and retries `429` responses with exponential backoff.
