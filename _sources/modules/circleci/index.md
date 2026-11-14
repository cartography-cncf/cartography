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

## Supply-chain code-to-cloud edges

For environments where a container image carries neither SLSA provenance nor layer
history (so the existing `provenance` / `dockerfile_analysis` match methods cannot fire)
and lives on a generic registry (no GHCR-style package ownership), the CircleCI
supply-chain matcher adds a low-confidence fallback `PACKAGED_FROM` edge from an `Image` to
its code repository. Pipeline runs are read transiently from the CircleCI API and are
never stored as nodes; only the edges are written.

The fallback `PACKAGED_FROM` edge carries `match_method` and `confidence` so consumers can
filter at their own threshold (the `PACKAGED_BY` edge carries only `match_method`). This
rung runs below the provenance / Dockerfile / package-owner ladder:

| match_method | Signal | Confidence |
|--------------|--------|------------|
| `circleci_tag_revision` | An `ImageTag` name exactly matches, or is a 7+ character hexadecimal prefix of, a `/pipeline`-feed run's `vcs.revision` (git SHA) that resolves to a single repo; that run names the repo. | medium (`0.5`) |

The `/pipeline` feed is filtered to a recent lookback window and is not a complete
inventory (CircleCI API v2 has no list-projects endpoint). `circleci_tag_revision` resolves
a specific image, so a partial feed usually only causes misses; a repo outside the window
that shares the same revision (or short-SHA prefix) can still cause an incorrect edge,
though this is rare and reflected in the medium confidence. Stale edges are cleaned only
for images the feed re-evaluated this run (a match that became ambiguous or repointed to a
different repo); an image whose build has aged out of the window keeps its existing edge.

```
(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)
(:Image)-[:PACKAGED_FROM]->(:GitLabProject)
```

```{toctree}
config
schema
```
