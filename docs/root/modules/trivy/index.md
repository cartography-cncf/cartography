# Trivy

The Trivy module ingests vulnerability, package, and fix data from Trivy JSON
container image scan reports. Findings and packages attach to canonical
ontology `Image` nodes by image digest, independent of the source registry.

Cartography currently supports matching Trivy reports to images ingested from
AWS ECR, Google Artifact Registry, and GitLab Container Registry. Load the
registry's Cartography module before Trivy so the corresponding canonical image
nodes exist.

See [configuration](config.md) for report requirements and source options, and
the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
