# Orca Security

```{toctree}
config
schema
```

Cartography ingests Orca alerts and per-target CVE findings. Organizations,
alerts, and vulnerability findings use the `Tenant`, `SecurityIssue`, and `CVE`
ontology labels.

Closed and dismissed alerts aren't ingested. After a complete sync, cleanup
removes alerts that were closed or dismissed since the previous sync. A
reopened alert returns on the next sync.

The module retains exact Orca and provider target identifiers as finding
properties. It doesn't ingest Orca Inventory. A vulnerability finding links with
`AFFECTS` to the AWS EC2 instance, Lambda function, or AMI that its provider
identifier names exactly, when Cartography has synced that asset.

Each vulnerable package with a package URL becomes an `OrcaPackage` node, which
the finding links to with `AFFECTS`. The ontology packages sync maps each
`OrcaPackage` to a `PackageVersion`, so the finding also `AFFECTS` the canonical
package version that other scanners report.
