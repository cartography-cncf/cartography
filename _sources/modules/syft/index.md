# Syft

The Syft module creates `SyftPackage` nodes with `DEPENDS_ON` dependency
relationships from [Syft](https://github.com/anchore/syft).

## Purpose

While Trivy provides vulnerability scanning and creates `TrivyPackage` nodes
with CVE findings, it lacks dependency relationship information. Syft
complements Trivy by creating `SyftPackage` nodes with `DEPENDS_ON`
relationships between them.

Dependency position is represented by graph structure rather than a stored
property. A package with no incoming `DEPENDS_ON` relationship is a root in the
scanned dependency graph. A package with an incoming `DEPENDS_ON` relationship
is nested below at least one other package.

Package identity is global (`normalized_id`), so the same `SyftPackage` can be
`DEPLOYED` to many `Image` nodes. Cataloger names and artifact paths for a given
image live on that `DEPLOYED` relationship as `found_by` and `locations`.
`SyftPackage.found_by` is no longer written; leftover node values are
last-writer-wins and are not image-scoped.

See [configuration](config.md) for report generation and source options,
[queries](queries.md) for dependency query examples, and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
schema
queries
```
