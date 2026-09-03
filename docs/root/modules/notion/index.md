# Notion

The Notion module inventories members and bot connections in one or more Notion
workspaces through the public Notion API. Members are mapped to Cartography's
`UserAccount` ontology and bot connections are mapped to `ThirdPartyApp`.

Notion's user-list endpoint excludes guests. The public API does not expose
workspace roles, member account status, or groups, so the module leaves those
attributes unknown.

An optional public-page sync records metadata for connection-visible pages that
Notion reports as published to the web. It does not ingest page bodies, blocks,
comments, database rows, or data-source schemas. Notion search is not an
authoritative content inventory, so public-page discovery can have false
negatives. Previously observed pages are removed only when Notion positively
confirms that they are no longer public.

```{toctree}
config
schema
```
