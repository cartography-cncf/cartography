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

An unreadable endpoint never deletes anything and never overwrites anything. "We could not read this" is treated differently from a `200` returning an empty list or omitting a field: only the latter is real data.

- For resources (keys, branches, buckets, secrets, poolers, findings, ...), an unreadable list skips both the load and the cleanup, so the previously-ingested nodes stay in the graph rather than being erased.
- For the posture properties rolled up onto `SupabaseProject` and `SupabaseDatabase` (`ssl_enforced`, `legacy_api_keys_enabled`, `pitr_enabled`, the allowed CIDR lists, and so on), an unreadable endpoint carries the stored value forward instead of writing null. Nulling these on a transient `403` would silently downgrade a known-bad configuration to an apparently clean one.

The tradeoff is that a feature deliberately turned off keeps its last known value until the endpoint is readable again. The node's `lastupdated` is still refreshed, so the staleness is visible; a stale value that keeps its original meaning beats a null that reads as "not configured".

Projects removed upstream are cleaned up only after every surviving project's children have been synced, and the cleanup cascades so a deleted project takes its database, keys, buckets, functions and findings with it. Organizations are not cleaned up: like `GCPOrganization`, the node declares no relationships of its own, and Cartography deliberately leaves such nodes for manual management.

### Which projects get synced

Projects are enumerated from `GET /v1/organizations/{slug}/projects`, following its offset pagination to the end. That endpoint is the only organization-scoped one, so it is the authority for which projects exist and therefore for what cleanup may remove.

`GET /v1/projects` returns only "projects you've previously created", so it is used purely to enrich each project with the `database` object (host, version, engine, release channel) that the organization-scoped listing omits. A project created by another member of the organization is still ingested, but without those database fields no `SupabaseDatabase` node is created for it and a warning is logged.

### Rate limits

The Management API allows 120 requests per minute by default. The module issues roughly 20 requests per project, 3 per organization, plus one shared enrichment request, and retries `429` responses with exponential backoff.
