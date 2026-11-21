# Zendesk

The Zendesk module ingests a small security inventory for Zendesk Support:

- CX agents and administrators, including light agents and suspended staff.
- Legacy API-token metadata across the account: active status, description,
  creation/update times, last use, creator ID, and assignee when available.

`ZendeskTenant` contains both resource types through `RESOURCE` relationships.
`ZendeskAPIToken` connects to its assigned `ZendeskUser` through `OWNED_BY`.
Separately, `ZendeskUser` connects to tokens it created through `CREATED`.
These relationships are added when the corresponding user is in the staff
inventory; tokens remain attached to the tenant when a user is absent.
Customer profiles, tickets, OAuth clients, and OAuth-token inventory are outside
this initial scope. Full token values and truncated prefixes are never loaded
into the graph. OAuth is used only to authenticate Cartography.

The token inventory uses `GET /api/v2/api_tokens?include_users=true`, documented
as `ListApiTokens` in [Zendesk's official OpenAPI specification](https://developer.zendesk.com/zendesk/oas.yaml).
This endpoint returns one unpaginated `api_tokens` array. Zendesk schedules the
endpoint's removal for April 30, 2027. See
[Zendesk's legacy-token documentation](https://support.zendesk.com/hc/en-us/articles/4408889192858-Managing-API-token-access-to-the-Zendesk-API)
for the credential's security implications and retirement schedule.

Users carry the `UserAccount` ontology label, with email, display name, active
status derived from suspension, and last-login properties. Tokens carry the
`APIKey` label, with description mapped to name and normalized creation,
modification, and last-use timestamps. Accounts carry the `Tenant` label.
IDs include the normalized subdomain so multiple accounts can coexist.

Syncing removes stale users and tokens only within the configured account,
after successfully fetching the complete collection. A `404` from the API Tokens
endpoint means token access is disabled: the module cleans up that account's
token inventory and continues. A `403` warns and skips token load and cleanup,
preserving the previous inventory. Other API or pagination failures propagate
without cleaning up the failed collection. Collections sync independently;
a token failure does not roll back an already completed user sync. Tenant nodes
are retained.
If an account's subdomain changes, it is treated as a new tenant.

See [configuration](config.md) for setup and [schema](schema.md) for graph fields.

```{toctree}
config
schema
```
