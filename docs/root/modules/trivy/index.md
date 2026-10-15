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
across all scans, and the ontology fields `_ont_base_severity` and
`_ont_vuln_status` follow those node values. For per-target questions, read the
same four properties on the `AFFECTS` relationship from the finding to the
`Image` or `FilesystemSnapshot`. They hold the raw Trivy values reported for
that target.

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

## Operating System Per Scan Target

A `TrivyPackage` node is shared by every image and filesystem snapshot with a
package of the same name and version, and those can run different
distributions. The operating system Trivy detected in each scan target
(`Metadata.OS`) is therefore recorded on the `DEPLOYED` relationship from each
package to that target:

- `os_family`: the OS family, such as `debian`, `ubuntu` or `alpine`.
- `os_name`: the version as Trivy reported it, such as `12.7` or `trixie/sid`
  for Debian and `24.04` for Ubuntu.
- `os_release`: for Debian only, the major release (`12` for `12.7`, `13` for
  `trixie/sid`), which matches `release_version` on
  [Debian security tracker](../debian/index.md) entries.

Every package of a target carries the target's OS, language packages
included. To keep to the distribution's own packages, filter on the package's
`class_name` (`os-pkgs`), as the [queries](queries.md) page shows. The
package's `type` does not work for this: it is on the shared node, so a package
with the same name and version in a Debian and an Ubuntu image carries the
type of whichever report was ingested last.

See [configuration](config.md) for report requirements and source options,
[queries](queries.md) for example queries, and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
schema
queries
```
