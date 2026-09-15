# Tenable Configuration

## Authentication

Cartography requires Tenable access and secret keys. By default, it reads them
from the `TENABLE_ACCESS_KEY` and `TENABLE_SECRET_KEY` environment variables.
Create API keys from the Tenable Vulnerability Management user interface as
described in Tenable's
[Generate API Keys](https://docs.tenable.com/vulnerability-management/Content/Settings/my-account/GenerateAPIKey.htm)
documentation.

## Required Permissions

The Tenable user needs either the Basic role or a custom role with the
`VM.VM_EXPLORE.VM_EXPLORE.EXPORT` privilege. Vulnerability exports also require
Can View access to the assets being exported. Administrator users can export
without explicit Can View access.

See Tenable's API documentation for
[asset exports](https://developer.tenable.com/reference/export-assets-v2) and
[vulnerability exports](https://developer.tenable.com/reference/exports-vulns-request-export).

## Configure Cartography

| Option | Default | Purpose |
| --- | --- | --- |
| `--tenable-access-key-env-var` | `TENABLE_ACCESS_KEY` | Environment variable containing the access key. |
| `--tenable-secret-key-env-var` | `TENABLE_SECRET_KEY` | Environment variable containing the secret key. |
| `--tenable-url` | `https://cloud.tenable.com` | Tenable API base URL. |
| `--tenable-tenant-id` | URL without its leading scheme | Stable graph scope for this Tenable tenant. |
| `--tenable-findings-lookback-days` | `180` | Number of days included in findings exports. |

## Run Cartography

```bash
export TENABLE_ACCESS_KEY="<access-key>"
export TENABLE_SECRET_KEY="<secret-key>"

cartography --selected-modules tenable
```

## Advanced Configuration

### Tenant ID

`--tenable-tenant-id` sets the identifier of the `TenableTenant` node that
scopes all resources imported from the configured Tenable instance. Set a
stable, unique value when importing multiple Tenable tenants.

When this option is omitted, Cartography derives the ID from the effective base
URL by removing a leading `https://` or `http://`. For the default URL, the ID
is `cloud.tenable.com`. This is a normalized URL string, not a tenant or
container UUID discovered from the Tenable API. Any port, path, query, or
trailing slash in a custom base URL remains part of the derived ID.

```{warning}
Tenable plugin and cloud-detail identifiers are not currently tenant-qualified.
Do not import multiple Tenable tenants into the same graph when those identifiers
may overlap. A future migration will add full tenant isolation without changing
existing graph identifiers in place.
```

### Findings lookback

`--tenable-findings-lookback-days` controls how many days of findings each sync
requests. It defaults to `180` and must be at least `1`. The export is filtered
by the finding's last-seen time, and cleanup removes stale findings that are no
longer returned within the configured window.
