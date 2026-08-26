# Notion

The Notion module inventories people and bot connections in one or more Notion
workspaces through the public Notion API. Optional Enterprise SCIM credentials
enrich people with membership and profile data and add groups, memberships, and
reporting relationships. People, groups, and bot connections map to the
`UserAccount`, `UserGroup`, and `ThirdPartyApp` ontologies.

The public API does not distinguish workspace members from guests and does not
expose roles, account status, or groups. Without SCIM, the module therefore
leaves those attributes unknown rather than inferring them.

```{toctree}
config
schema
```
