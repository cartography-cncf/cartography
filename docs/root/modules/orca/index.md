# Orca Security

```{toctree}
config
schema
```

Cartography ingests the security findings that are unique to Orca Security:
organization-wide alerts and per-target CVE occurrences. Orca
organizations use the shared `Tenant` ontology label, alerts use
`SecurityIssue`, and vulnerability findings use `CVE`. This allows the CVE
metadata module to enrich Orca vulnerability findings directly.

Each organization owns its alerts and vulnerability findings through
`RESOURCE` relationships. An alert represents Orca's prioritization and
workflow state. An `OrcaVulnerabilityFinding` represents one CVE occurrence on
one Orca target, scoped to an installed package when Orca supplies package
context. Two targets affected by the same CVE remain distinct findings.

The module does not enumerate Orca Inventory or create duplicate `OrcaAsset`
nodes. Its Alert and VulnerabilityV2 queries request the related Inventory
object only as finding context. Exact Orca and provider-native target
identifiers, account and region context, and the raw Orca target type are
retained as finding properties. They do not create an `AFFECTS` relationship in
the current module.

Future provider linking can use an explicit allowlist of Orca target types and
authoritative provider-native identifiers to connect findings to the canonical
AWS, Azure, or GCP assets already in Cartography. Names, IP addresses, and other
fuzzy attributes must not be used for that correlation.
