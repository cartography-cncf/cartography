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

## Severity Per Scan Target

A `TrivyImageFinding` node is shared by every image and filesystem snapshot that
carries the vulnerability, and Trivy can rate the same vulnerability differently
in each of them: a Debian package and an Alpine package with the same CVE often
carry different severities. The node's `severity`, `severity_source`, `status`
and `data_source_id` come from the last package row ingested for the finding,
across all scans. The ontology fields `_ont_base_severity` and `_ont_vuln_status`
follow those node values, so per-image questions should read the `AFFECTS`
relationship instead.

Each `AFFECTS` relationship from a finding to an `Image` or `FilesystemSnapshot`
carries the rating Trivy reported for that scan target, as raw Trivy strings
rather than normalized values:

- `severity`: uppercase Trivy severity, such as `LOW` or `CRITICAL`.
- `severity_source`: the advisory source Trivy used for the severity, such as
  `debian`, `ubuntu`, `ghsa` or `nvd`. Absent when Trivy fell back to its
  default severity without naming a source.
- `status`: the fix status in Trivy's vocabulary, such as `affected`, `fixed` or
  `will_not_fix`.
- `data_source_id`: the Trivy advisory database that matched the package.

When several packages in one target carry the same finding, the target takes the
rating of one package, chosen by, in order:

1. the highest severity;
2. a severity from a named distribution or ecosystem source over an `nvd` or
   unnamed one;
3. no fix available (`affected`, `will_not_fix`, `fix_deferred`, ...) over a
   fix available (`fixed`, where the installed version is still vulnerable),
   and `fixed` over `not_affected`;
4. an operating system package over a language package;
5. report order.

For example, to list the rating of one CVE on every image it affects:

```cypher
MATCH (f:TrivyImageFinding {cve_id: 'CVE-2026-27171'})-[r:AFFECTS]->(img:Image)
RETURN img.`_ont_digest`, r.severity, r.severity_source, r.status
```

See [configuration](config.md) for report requirements and source options, and
the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
