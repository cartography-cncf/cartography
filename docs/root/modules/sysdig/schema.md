## Sysdig Schema

### SysdigTenant::Tenant

Represents the Sysdig Secure tenant or API endpoint scope.

| Field | Description |
|-------|-------------|
| **id** | Tenant id. Defaults to the Sysdig API hostname. |
| name | Tenant display name. |
| api_url | Sysdig API base URL. |

### SysdigResource

Represents a Sysdig-observed resource. This node is intentionally not assigned
broad ontology labels because Sysdig resources can describe many kinds of cloud,
Kubernetes, container, and workload objects.

### SysdigImage::Image

Represents a container image when Sysdig provides a stable image digest.

### SysdigPackage

Represents a package involved in a Sysdig vulnerability finding.
`normalized_id` follows the existing package ontology convention:
`{type}|{namespace/}{normalized_name}|{version}`.

### SysdigVulnerabilityFinding::Risk::CVE

Represents a Sysdig vulnerability assertion. It includes CVE id, severity,
status, fix availability, in-use context, exploitability, image digest, package
context, and affected resource id when Sysdig provides those fields.

Relationships:

```text
(SysdigVulnerabilityFinding)-[:AFFECTS]->(SysdigResource)
(SysdigVulnerabilityFinding)-[:AFFECTS]->(Image)
(SysdigVulnerabilityFinding)-[:AFFECTS]->(SysdigPackage)
```

### SysdigSecurityFinding::SecurityIssue

Represents posture, compliance, or other schema-discovered security findings
that map cleanly to Cartography's `SecurityIssue` semantics.

### SysdigRiskFinding::SecurityIssue

Represents Sysdig risk findings, preserving Sysdig's correlated risk assertion
without introducing a new canonical risk ontology type.

### SysdigRuntimeEventSummary::SecurityIssue

Represents aggregated runtime detections. The module groups runtime events by
resource id, rule name, policy id, severity, source, and engine, then stores
`first_seen`, `last_seen`, `event_count`, `rule_tags`, and representative
event metadata.

The module does not ingest raw runtime/Falco events in v1.
