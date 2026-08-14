# Orca Security Configuration

Configure an organization-wide, read-only Orca Security API token and the API
origin for your Orca region.

## Authentication

Create an API token by following the API-token instructions available in your
Orca tenant. Store the token in a secret manager or environment variable; do
not put it on the command line or commit it to a configuration file.

Role names and the token-configuration interface can differ between Orca
tenants. Verify the exact role configuration against the API-token
documentation available from your tenant. Cartography needs only the
organization-wide read capabilities listed below and does not need permissions
to create, update, or delete Orca resources.

## Required Permissions

The token must authorize the following operations across the entire Orca
organization:

| Operation | Required access |
|-----------|-----------------|
| `GET /api/user/action` | Read the current organization's ID and name. |
| `POST /api/serving-layer/query` | Query the `Inventory`, `Alert`, and `VulnerabilityV2` datasets. |

The Serving Layer query uses HTTP `POST`, but it is a read-only query. Do not
grant create, update, or delete permissions for this integration.

Before the first production sync, use the authenticated Serving Layer Request
Builder for the tenant to confirm that an Alert full-graph response includes
the related `Inventory.id`. Cartography only creates an alert `AFFECTS` edge
when that exact identifier is present; alerts without it remain
organization-owned and are not correlated by name, type, or IP address.

Do not restrict the token to only a subset of the organization's accounts,
business units, or assets. The module performs a complete organization sync;
partial visibility would produce an incomplete graph and make snapshot-based
cleanup unsafe.

## Configure Cartography

Set `--orca-api-endpoint` to the HTTPS regional API origin shown for your Orca
tenant, for example `https://api.orcasecurity.io`. Supply only the origin: do
not include `/api` or an individual route because Cartography appends the API
paths it uses.

By default, Cartography reads the token from `ORCASECURITY_API_TOKEN`. Use
`--orca-api-token-env-var` to choose a different environment variable name.

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--orca-api-endpoint` |  | Yes | Regional Orca Security API origin, without `/api` or a route. |
| `--orca-api-token-env-var` | `ORCASECURITY_API_TOKEN` | Yes | Environment variable holding the Orca Security API token. |

## Run Cartography

```bash
export ORCASECURITY_API_TOKEN="..."

cartography \
  --selected-modules orca \
  --orca-api-endpoint https://api.orcasecurity.io
```

An HTTP `401` usually indicates an invalid or expired token. An HTTP `403`, or
missing datasets in the response, indicates that the token lacks one of the
required organization-wide read capabilities or is scoped too narrowly.

## References

- [Orca Security Terraform API client](https://github.com/orcasecurity/terraform-provider-orcasecurity/blob/master/orcasecurity/api_client/api_client.go)
- [Orca Security organization API contract](https://github.com/orcasecurity/terraform-provider-orcasecurity/blob/master/orcasecurity/api_client/organizations.go)
- [Managing Orca API tokens](https://docs.orcasecurity.io/docs/managing-api-tokens)
- [Orca Serving Layer API](https://docs.orcasecurity.io/docs/serving-layer-api)
