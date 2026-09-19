# Zendesk Configuration

Configure a Zendesk Support subdomain and an OAuth access token authorized to read
staff and legacy API-token metadata.

## Authentication

Use a dedicated account with the permissions below and obtain an OAuth access token using
Zendesk's [OAuth setup guide](https://developer.zendesk.com/documentation/authentication/api-tokens-to-oauth/).
Supply the token through an environment variable; Cartography authenticates with
`Authorization: Bearer`. The module does not create, revoke, or automatically
refresh credentials. Supply a valid token again after expiry or revocation.
The OAuth credential authenticates Cartography; the inventory contains legacy
API tokens, not OAuth access tokens.

## Required Permissions

For `ListApiTokens`, Zendesk's
[official OpenAPI specification](https://developer.zendesk.com/zendesk/oas.yaml)
allows **administrators or agents with the Manage APIs permission**. Full
administrator access is therefore not required. On Enterprise plans, use a
[custom agent role](https://support.zendesk.com/hc/en-us/articles/4408882153882-Creating-custom-roles-and-assigning-agents)
with Manage APIs and permission to view team members for the staff inventory.
Manage APIs includes credential-management capabilities on the account; it is not
a read-only role permission.

Restrict the collector's OAuth token to the **`read`** scope. The module only issues
GET requests to the Users and API Tokens endpoints. Zendesk does not document a
dedicated legacy-token inventory OAuth scope in its scope reference. A
`users:read` token alone does not document access to the token inventory.

## Configure Cartography

| Option | Value |
| --- | --- |
| `--zendesk-subdomain` | Subdomain only, e.g. `acme` for `https://acme.zendesk.com`. URLs and custom hostnames are not accepted. |
| `--zendesk-oauth-token-env-var` | Name of the environment variable holding the OAuth access token, e.g. `ZENDESK_OAUTH_TOKEN`. |
| `--selected-modules` | Include `zendesk`. |

If either the subdomain or token is missing, the module logs that it is unconfigured
and skips ingestion.

## Run Cartography

```bash
export ZENDESK_OAUTH_TOKEN='your-oauth-access-token'
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules zendesk \
  --zendesk-subdomain acme \
  --zendesk-oauth-token-env-var ZENDESK_OAUTH_TOKEN
```

## Troubleshooting

- `401`: Check that the OAuth access token is valid and belongs to the configured
  Zendesk account.
- `403`: Check the token's `read` scope and the authenticating user's administrator
  role or Manage APIs permission.
- `404` from the API Tokens endpoint: Zendesk documents this when API token access
  is disabled. The module raises the error and preserves the previous token
  inventory; it does not interpret an unavailable inventory as an empty one.
  The endpoint is also scheduled for removal on April 30, 2027.
- `429`: Zendesk rate-limited the request. Rerun after the response's `Retry-After`
  interval; failed collections retain their previously ingested graph data.

## References

- [Users API](https://developer.zendesk.com/api-reference/ticketing/users/users/)
- [Official OpenAPI specification: ListApiTokens and ApiTokenObject](https://developer.zendesk.com/zendesk/oas.yaml)
- [Managing legacy API tokens](https://support.zendesk.com/hc/en-us/articles/4408889192858-Managing-API-token-access-to-the-Zendesk-API)
- [Security and authentication](https://developer.zendesk.com/api-reference/introduction/security-and-auth/)
- [OAuth grants and scopes](https://developer.zendesk.com/api-reference/ticketing/oauth/grant_type_tokens/)
- [Cursor pagination](https://developer.zendesk.com/api-reference/introduction/pagination/)
