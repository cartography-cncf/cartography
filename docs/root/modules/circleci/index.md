# CircleCI

Cartography discovers CircleCI projects from each organization's pipeline feed
because CircleCI API v2 does not provide an endpoint that lists every project
in an organization. The feed covers recently built projects followed by the
token owner, approximately 250 projects per organization. Add projects without
recent pipeline activity explicitly with `--circleci-project-slugs`.

Because discovery is partial, `CircleCIProject` nodes are upserted but are not
automatically deleted when they disappear from the recent feed. Sub-resources
of every synced project, including environment variables, keys, and webhooks,
are fully enumerated and cleaned up. Use `lastupdated` to identify stale
project nodes.

CircleCI does not return clear-text secret values through the API. Context
environment variables expose no value, and project environment variables
expose only a masked value. Cartography stores only the value returned by the
API.

```{toctree}
config
schema
```
