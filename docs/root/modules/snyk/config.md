# Snyk Configuration

Cartography needs a Snyk API token and the ID of one Snyk organization to sync.

## Authentication

Create or copy a Snyk API token from your Snyk account settings, then store it in
an environment variable:

```bash
export SNYK_TOKEN="<api token>"
```

## Required Permissions

| Permission | Purpose |
|---|---|
| `View Organization (org.read)` | Read organization metadata and issues. |
| `View Projects (org.project.read)` | List targets, projects, and project-linked issues. |
| `View Project history (org.project.snapshot.read)` | Read issue data associated with project scan history. |

## Configure Cartography

Find the organization ID in Snyk under **Organization Settings > General**.

| Option | Description |
|---|---|
| `--snyk-api-key-env-var` | Environment variable holding the Snyk API token. Required to enable the module. |
| `--snyk-org-id` | Snyk organization ID to sync. Required. |
| `--snyk-base-url` | Snyk REST API base URL. Defaults to `https://api.snyk.io/rest`; use the regional URL for region-locked tokens. |

## Run Cartography

```bash
cartography \
  --selected-modules snyk \
  --snyk-api-key-env-var SNYK_TOKEN \
  --snyk-org-id 00000000-0000-4000-8000-000000000000
```

## Advanced Configuration

Snyk API tokens are region-locked. Use `--snyk-base-url` when your organization is
hosted outside the default region, for example `https://api.us.snyk.io/rest`,
`https://api.eu.snyk.io/rest`, or `https://api.au.snyk.io/rest`.

This module syncs one Snyk organization per run. To ingest several organizations
into the same graph, run Cartography once per organization with a different
`--snyk-org-id`. Resource cleanup is scoped to the Snyk organization ID so those
runs do not delete each other's resources.

## References

- [Snyk REST API getting started](https://docs.snyk.io/snyk-api/rest-api/getting-started-with-the-rest-api)
- [Snyk Organizations API](https://docs.snyk.io/snyk-api/reference/orgs)
- [Snyk Targets API](https://docs.snyk.io/snyk-api/reference/targets)
- [Snyk Projects API](https://docs.snyk.io/snyk-api/reference/projects)
- [Snyk Issues API](https://docs.snyk.io/snyk-api/reference/issues)
