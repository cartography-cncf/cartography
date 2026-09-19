# Zendesk

The Zendesk module ingests a small security inventory for Zendesk Support:

- CX agents and administrators, including light agents and suspended staff.
- Legacy API-token metadata across the account: active status, description,
  creation/update times, last use, creator ID, and assigned user ID when available.

`ZendeskTenant` contains both resource types through `RESOURCE` relationships.
`ZendeskUser` connects to `ZendeskAPIToken` through `CREATED` when the creator is
in the staff inventory. Creator identity does not describe who can authenticate
with the token. Tokens with missing or un-ingested creators remain attached to
the tenant. Customer profiles, tickets, OAuth clients, and OAuth-token inventory
are outside this initial scope. Full token values and truncated prefixes are
never loaded into the graph. OAuth is used only to authenticate Cartography.

The token inventory uses `GET /api/v2/api_tokens?include_users=true`, documented
as `ListApiTokens` in [Zendesk's official OpenAPI specification](https://developer.zendesk.com/zendesk/oas.yaml).
This endpoint returns one unpaginated `api_tokens` array. Zendesk schedules the
endpoint's removal for April 30, 2027. See
[Zendesk's legacy-token documentation](https://support.zendesk.com/hc/en-us/articles/4408889192858-Managing-API-token-access-to-the-Zendesk-API)
for the credential's security implications and retirement schedule.

Users carry the `UserAccount` ontology label, with normalized email, display name,
and last-login properties. Accounts carry the `Tenant` label. IDs include the
normalized subdomain so multiple accounts can coexist. Syncing removes stale
users and tokens only within the configured account, after successfully fetching
the complete collection. An API or pagination failure aborts that collection's
sync without cleaning it up. Collections sync independently; a token failure
does not roll back an already completed user sync. Tenant nodes are retained.
If an account's subdomain changes, it is treated as a new tenant.

See [configuration](config.md) for setup and [schema](schema.md) for graph fields.

```{toctree}
config
schema
```
