## Modal Configuration

Follow these steps to analyze a [Modal](https://modal.com) workspace with Cartography.

1. Create an API token in the Modal dashboard under Settings -> API Tokens, or with
   `modal token new`. You will get a token id (starting with `ak-`) and a token secret
   (starting with `as-`). The secret is shown only once.
1. Populate an environment variable with the token secret. You can pass the environment
   variable name with the `--modal-token-secret-env-var` flag.
1. Pass the token id with the `--modal-token-id` flag. The workspace to sync is derived
   from the token itself, so there is nothing else to identify.
1. Optionally restrict which environments have their contents synced with
   `--modal-environments`, a comma-separated list of environment names.

### A note on token privilege

Modal has **no read-only API token scope**. A token carries every privilege of the
identity it belongs to, so a personal token grants Cartography your full access to the
workspace. Prefer creating a dedicated
[service user](https://modal.com/docs/guide/service-users) and granting it the `viewer`
environment role on the environments you want inventoried. The workspace node records
which credential performed the sync (`synced_with_principal_type`), so you can check this
from the graph.

### A note on the Modal API

Modal publishes no REST management API: everything goes through gRPC behind the Python
client. Only part of the inventory is reachable through Modal's documented public helpers,
so this module talks to Modal's **internal gRPC protocol** for the rest. That protocol is
unversioned and can change in any Modal release, which is why the dependency is pinned to
`modal>=1.5.3,<2`. The lower bound matters too: the RPC used for per-environment RBAC only
exists from 1.5.3. All of it is isolated in `cartography/intel/modal/util.py`, so a
protocol break should require changes in that one file.

### A note on secrets

Modal never returns secret **values** through any read API, so Cartography cannot and does
not store them. Only metadata (name, creation time, last-used time) is ingested.

More importantly, the mapping from an app or function to the secrets it consumes is
**write-only** in Modal's API: `Function.secret_ids` is sent when a function is deployed
but is never returned when reading it back. Cartography therefore **cannot** produce
`(:ModalFunction)-[:USES_SECRET]->(:ModalSecret)` edges. Secret consumption can only be
determined from your source code.

### A note on web endpoint authentication

Whether a web endpoint requires proxy authentication (`requires_proxy_auth`) is also
write-only and cannot be read back. Cartography records a function's `web_url` but
**cannot tell you whether that URL is protected**. Treat every non-null
`ModalFunction.web_url` as potentially reachable without authentication, and confirm out of
band.

### A note on function configuration

For the same reason, a deployed function's GPU, CPU, memory, region, cloud, mounted volumes,
`block_network`, `untrusted`, proxy and schedule/cron settings are not readable and are
absent from `ModalFunction`. Sandboxes **do** expose their resources, regions and tunnels;
functions do not.

### A note on scoping and completeness

- When `--modal-environments` is set, every environment is still ingested as a
  `ModalEnvironment` node, but only the listed environments have their contents refreshed.
  Resources in the other environments keep their previous data with a stale `lastupdated`.
  This is deliberate: loading only the selected subset would let the workspace-scoped
  environment cleanup delete the other environment nodes while their children survived as
  orphans.
- When an environment is deleted in Modal, its environment-scoped resources are removed
  from the graph along with it. This is a deliberate cascade: those resources are cleaned up
  by traversing their environment node, so deleting the environment first would leave them
  behind as orphans that still read as live.
- Custom domains require a paid Modal add-on. On workspaces without it the API answers
  `UNIMPLEMENTED`. Cartography treats that as "we learned nothing", not as "there are none", so
  it skips both the load and the cleanup and leaves any previously-ingested domains untouched.
- Only **named** images are enumerable. Anonymous build images, which is what an inline
  `modal.Image.debian_slim()` produces, are not returned by the API, so a sandbox's `HAS_IMAGE`
  edge often has nothing to resolve to.
- Both sandbox generations are ingested. Modal's ordinary sandbox listing returns only v1, so
  Cartography additionally calls the v2 listing, which is per app. Each sandbox records which
  generation it is in `sandbox_version`.
- Billing and cost data, and app deployment history, are out of scope for this module.
