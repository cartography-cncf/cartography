# Orca Security Configuration

Configure a read-only Orca API token and the API origin for your Orca region.

## Authentication

Create an API token by following the instructions for your Orca tenant. Orca
role names can vary by tenant, so grant the organization-wide read access
listed below.

## Required Permissions

The token must authorize these operations:

| Operation | Required access |
|-----------|-----------------|
| `GET /api/user/action` | Read the organization's ID and name. |
| `POST /api/serving-layer/query` | Query `Alert` and `VulnerabilityV2`, including related Inventory context. |

The token must cover the entire organization. Partial account, business-unit,
or asset access isn't supported because cleanup requires a complete snapshot.
`VulnerabilityV2` results must include `Inventory.AssetUniqueId`.

## Configure Cartography

Set `--orca-api-endpoint` to your regional HTTPS API origin without `/api` or a
route. Cartography reads the token from `ORCASECURITY_API_TOKEN` by default.

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--orca-api-endpoint` |  | Yes | Regional Orca API origin. |
| `--orca-api-token-env-var` | `ORCASECURITY_API_TOKEN` | No | Environment variable that contains the Orca API token. |

## Run Cartography

```bash
export ORCASECURITY_API_TOKEN="..."

cartography \
  --selected-modules orca \
  --orca-api-endpoint https://api.orcasecurity.io
```

## Troubleshooting

- HTTP `401`: Check whether the token is valid and unexpired.
- HTTP `403` or missing findings: Check the token's organization-wide read access.
- Missing `Inventory.AssetUniqueId`: Check the response in Orca's authenticated
  Serving Layer Request Builder.

## References

- [Orca Security Terraform API client](https://github.com/orcasecurity/terraform-provider-orcasecurity/blob/master/orcasecurity/api_client/api_client.go)
- [Orca Security organization API contract](https://github.com/orcasecurity/terraform-provider-orcasecurity/blob/master/orcasecurity/api_client/organizations.go)
- [Managing Orca API tokens](https://docs.orcasecurity.io/docs/managing-api-tokens)
- [Orca Serving Layer API](https://docs.orcasecurity.io/docs/serving-layer-api)
