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

See [configuration](config.md) for report generation and source options,
[queries](queries.md) for dependency query examples, and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
schema
queries
```
