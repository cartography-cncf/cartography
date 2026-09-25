# Trivy

The Trivy module ingests vulnerability, package, and fix data from Trivy JSON
container image and source filesystem scan reports. Findings and packages attach
to canonical ontology `Image` or `FilesystemSnapshot` nodes.

Cartography currently supports matching Trivy reports to images ingested from
AWS ECR, Google Artifact Registry, and GitLab Container Registry. Load the
registry's Cartography module before Trivy so the corresponding canonical image
nodes exist.

Git repository scans match `FilesystemSnapshot` nodes by the repository URL and
exact commit recorded in Trivy metadata. The corresponding provider module must
create the snapshot before Trivy ingestion runs.

## Finding Identifiers

Trivy findings can carry CVE, GitHub advisory, Debian advisory, RustSec, and
other identifiers. Cartography preserves every reported identifier in
`vulnerability_ids`, with the primary `VulnerabilityID` first, and extracts
dedicated `cve_id` and `ghsa_id` values when present.

Every finding uses the `Risk` label. The `CVE` label is applied only when a CVE
identifier is present.

See [configuration](config.md) for report requirements and source options, and
the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
