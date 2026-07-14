# Tenable Configuration

Cartography requires Tenable access and secret keys. By default, it reads them
from the `TENABLE_ACCESS_KEY` and `TENABLE_SECRET_KEY` environment variables.

```bash
export TENABLE_ACCESS_KEY="<access-key>"
export TENABLE_SECRET_KEY="<secret-key>"

cartography --selected-modules tenable
```

Use `--tenable-access-key-env-var` and `--tenable-secret-key-env-var` to select
different environment variable names. `--tenable-url` sets the API base URL and
defaults to `https://cloud.tenable.com`.

## Tenant ID

`--tenable-tenant-id` sets the identifier of the `TenableTenant` node that
scopes all resources imported from the configured Tenable instance. Set a
stable, unique value when importing multiple Tenable tenants.

When this option is omitted, Cartography derives the ID from the effective base
URL by removing a leading `https://` or `http://`. For the default URL, the ID
is `cloud.tenable.com`. This is a normalized URL string, not a tenant or
container UUID discovered from the Tenable API. Any port, path, query, or
trailing slash in a custom base URL remains part of the derived ID.

## Findings lookback

`--tenable-findings-lookback-days` controls how many days of findings each sync
requests. It defaults to `180` and must be at least `1`. The export is filtered
by the finding's last-seen time, and cleanup removes stale findings that are no
longer returned within the configured window.
