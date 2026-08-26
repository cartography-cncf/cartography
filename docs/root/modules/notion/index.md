# Notion

The Notion module inventories people and bot connections in one or more Notion
workspaces through the public Notion API. People are mapped to Cartography's
`UserAccount` ontology and bot connections are mapped to `ThirdPartyApp`.

The public API does not distinguish workspace members from guests and does not
expose roles, account status, or groups. The module therefore leaves those
attributes unknown rather than inferring them.

```{toctree}
config
schema
```
