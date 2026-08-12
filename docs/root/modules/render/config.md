## Render Configuration

Follow these steps to analyze a [Render](https://render.com) account with Cartography.

1. Create an API key from your Render account settings page. See
   [Render's API documentation](https://render.com/docs/api) for how the platform API is
   organized.
1. Populate an environment variable with the API key.
1. Pass the environment variable name with the `--render-api-key-env-var` flag.

```bash
RENDER_API_KEY=<your-api-key> cartography --render-api-key-env-var RENDER_API_KEY
```

### A note on API key scope

A Render personal API key authorizes every action available to the account it belongs to,
across **every workspace that account can reach** — there is no read-only or
workspace-scoped key. Cartography syncs every workspace (`owner`) the configured key can
list from `GET /v1/owners`, so a key belonging to an account in several workspaces will
sync all of them in a single run.

### Resources synced

- `RenderTenant` (a Render workspace/`owner`)
- `RenderProject`
- `RenderEnvironment`
- `RenderService` (web services, background workers, cron jobs, private services, and
  static sites)
- `RenderPostgres`
- `RenderDisk`
- `RenderCustomDomain`
- `RenderSecretFile`
- `RenderKeyValue` (Valkey/Redis-compatible instances)
- `RenderEnvGroup` (shared env var/secret file groups, linked to the services that use them)
- `RenderIPAllowRule` (network access control: the CIDR blocks allowed to reach each
  environment, service, Postgres instance, and Key Value instance)
- `RenderDedicatedIP` (static outbound IPv4 addresses for a workspace/region)

Render's Private Link connections are not ingested: as of this writing they have no
public REST API (dashboard-only) and require a Pro workspace or higher, so there is
nothing to sync regardless of plan.

### A workspace that drops out of view is not deleted

If the configured API key loses access to a workspace it previously synced — the key was
scoped down, a team membership was revoked, etc. — Cartography does not delete that
workspace's `RenderTenant` node or anything under it. Losing access is not the same as the
workspace being deleted. Render API visibility is credential-dependent, so this module does
not cascade-delete a tenant's subtree just because the configured key can no longer see it;
that avoids a temporarily misconfigured key wiping real graph history. If a workspace is
genuinely gone for good, its nodes need to be removed manually.

### Secret values are never ingested

Two Render APIs return secret material inline with their metadata, and Cartography
deliberately never stores that material:

- `GET /services/{serviceId}/secret-files` returns each secret file's full plaintext
  `content` alongside its `name`. Only `name` is ingested — `content` is discarded in
  `cartography/intel/render/secretfiles.py` before it ever reaches the graph, is never
  logged, and is never persisted anywhere.
- `GET /env-groups` returns only group metadata (name, linked services) — env var values
  and secret file contents are not included in that response and Cartography never calls
  the separate endpoints that would return them.

## References

- [Render API documentation](https://render.com/docs/api)
- [Render API reference](https://api-docs.render.com)
