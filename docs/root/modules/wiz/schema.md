# Wiz Schema

Cartography ingests Wiz resources, issues, and vulnerability findings from the Wiz GraphQL API. All Wiz-owned nodes are scoped directly to `WizTenant`; Wiz projects are stored as metadata on records in this first version.

## WizTenant

Represents a Wiz tenant/API endpoint.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for tenant accounts across different systems.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Identifier used to scope Wiz data |
| graphql_url | Wiz GraphQL API endpoint |

### Relationships

```cypher
(WizTenant)-[:RESOURCE]->(WizResource)
(WizTenant)-[:RESOURCE]->(WizIssue)
(WizTenant)-[:RESOURCE]->(WizVulnerabilityFinding)
```

## WizResource

Represents a resource as observed by Wiz. This is not the canonical cloud resource node; it preserves Wiz's resource identity and metadata.

> **Ontology Mapping**: This node has the extra label `Asset`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Wiz resource ID |
| **name** | Resource name |
| **external_id** | Native cloud identifier when Wiz provides one |
| **resource_type** | Wiz resource type |
| **cloud_platform** | Cloud platform reported by Wiz |
| status | Resource status |
| **region** | Cloud region |
| **cloud_account_id** | Wiz cloud account ID |
| cloud_account_name | Cloud account name |
| cloud_account_provider | Cloud account provider |
| **cloud_account_external_id** | Native cloud account/subscription/project identifier |
| **project_ids** | Wiz project IDs associated with this resource |
| **project_names** | Wiz project names associated with this resource |
| tags | Flattened tag strings |
| created_at | Creation timestamp reported by Wiz |
| updated_at | Last update timestamp reported by Wiz |
| is_open_to_all_internet | Whether Wiz reports the resource open to all internet |
| is_accessible_from_internet | Whether Wiz reports the resource accessible from the internet |
| has_access_to_sensitive_data | Whether Wiz reports access to sensitive data |
| has_admin_privileges | Whether Wiz reports admin privileges |
| has_high_privileges | Whether Wiz reports high privileges |
| has_sensitive_data | Whether Wiz reports sensitive data |

### Relationships

```cypher
(WizResource)<-[:RESOURCE]-(WizTenant)
```

## WizIssue

Represents a Wiz issue instance, such as a cloud configuration issue, toxic combination, or threat detection.

> **Ontology Mapping**: This node has the extra label `Risk`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Wiz issue ID |
| **name** | Best available issue name from the source rule or control |
| **status** | Issue status |
| **severity** | Issue severity |
| **issue_type** | Wiz issue type |
| created_at | Issue creation timestamp |
| updated_at | Last update timestamp |
| due_at | Due timestamp |
| resolved_at | Resolution timestamp |
| status_changed_at | Last status-change timestamp |
| **control_id** | Wiz control ID |
| control_name | Control name |
| control_description | Control description |
| resolution_recommendation | Control remediation guidance |
| **source_rule_id** | Source rule ID |
| source_rule_name | Source rule name |
| **resource_id** | Affected Wiz resource ID |
| resource_name | Affected resource name |
| **resource_type** | Affected resource type |
| resource_native_type | Affected resource native type |
| resource_cloud_platform | Affected resource cloud platform |
| **resource_external_id** | Native identifier for the affected resource |
| **project_ids** | Wiz project IDs associated with the issue |
| **project_names** | Wiz project names associated with the issue |
| service_ticket_urls | URLs for linked service tickets |

### Relationships

```cypher
(WizIssue)<-[:RESOURCE]-(WizTenant)
(WizIssue)-[:AFFECTS]->(WizResource)
```

## WizVulnerabilityFinding

Represents a Wiz vulnerability finding instance on a specific Wiz resource.

> **Ontology Mapping**: This node has the extra label `Risk`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Wiz finding ID, or a deterministic composite ID when Wiz does not provide one |
| **name** | Finding name |
| **cve_id** | CVE identifier extracted from exact CVE text when present |
| cve_description | CVE description |
| **cvss_severity** | CVSS severity |
| score | Wiz vulnerability score |
| exploitability_score | Exploitability score |
| impact_score | Impact score |
| has_exploit | Whether an exploit is known |
| has_cisa_kev_exploit | Whether a CISA KEV exploit is known |
| **status** | Finding status |
| **vendor_severity** | Vendor severity |
| first_detected_at | First detection timestamp |
| last_detected_at | Last detection timestamp |
| resolved_at | Resolution timestamp |
| description | Finding description |
| remediation | Remediation guidance |
| detailed_name | Package or vulnerable component name |
| version | Vulnerable version |
| fixed_version | Fixed version |
| detection_method | Wiz detection method |
| link | External vulnerability link |
| portal_url | Wiz portal URL |
| location_path | Vulnerable path |
| resolution_reason | Resolution reason |
| **resource_id** | Affected Wiz resource ID |
| resource_name | Affected resource name |
| **resource_type** | Affected resource type |
| resource_region | Affected resource region |
| resource_cloud_platform | Affected resource cloud platform |
| **resource_external_id** | Native identifier for the affected resource |
| resource_status | Affected resource status |
| **subscription_external_id** | Cloud account/subscription/project external ID |
| subscription_name | Cloud account/subscription/project name |
| **project_ids** | Wiz project IDs associated with the finding |
| **project_names** | Wiz project names associated with the finding |

### Relationships

```cypher
(WizVulnerabilityFinding)<-[:RESOURCE]-(WizTenant)
(WizVulnerabilityFinding)-[:AFFECTS]->(WizResource)
(WizVulnerabilityFinding)-[:LINKED_TO]->(CVE)
```
