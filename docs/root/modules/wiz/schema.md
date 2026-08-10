# Wiz Schema

Cartography ingests Wiz issues and findings from the Wiz GraphQL API. All Wiz-owned nodes are scoped directly to `WizTenant`; affected resources and Wiz projects are stored as metadata on issues and findings in this first version.

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
(WizTenant)-[:RESOURCE]->(WizIssue)
(WizTenant)-[:RESOURCE]->(WizFinding)
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
| **resource_id** | Affected Wiz resource ID, stored as metadata |
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
```

## WizFinding

Represents a Wiz finding instance. `finding_type` identifies the source finding family, currently `VULNERABILITY`, `CONFIGURATION`, or `DETECTION`.

> **Ontology Mapping**: This node has the extra label `Risk`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Wiz finding ID, or a deterministic composite ID when Wiz does not provide one |
| **finding_type** | Wiz finding family |
| **name** | Finding name |
| **status** | Finding status |
| **severity** | Normalized Wiz severity when available |
| **vendor_severity** | Vendor severity for vulnerability findings |
| **result** | Configuration finding result |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |
| first_seen_at | First seen timestamp for configuration findings |
| first_detected_at | First detected timestamp for vulnerability findings |
| last_detected_at | Last detected timestamp for vulnerability findings |
| resolved_at | Resolution timestamp |
| description | Finding description |
| remediation | Remediation guidance |
| **cve_id** | CVE identifier extracted from exact CVE text when present |
| cve_description | CVE description |
| **cvss_severity** | CVSS severity |
| score | Wiz vulnerability score |
| exploitability_score | Exploitability score |
| impact_score | Impact score |
| has_exploit | Whether an exploit is known |
| has_cisa_kev_exploit | Whether a CISA KEV exploit is known |
| detailed_name | Package, component, or detailed finding name |
| version | Vulnerable version |
| fixed_version | Fixed version |
| detection_method | Wiz detection method |
| link | External vulnerability link |
| portal_url | Wiz portal URL |
| location_path | Vulnerable path |
| resolution_reason | Resolution reason |
| target_external_id | Configuration target external ID |
| **target_object_provider_unique_id** | Configuration target provider-unique ID |
| **rule_id** | Wiz rule ID |
| **rule_graph_id** | Wiz graph rule ID |
| rule_name | Wiz rule name |
| rule_description | Wiz rule description |
| rule_builtin | Whether a detection rule is built in |
| rule_as_control | Whether a configuration rule functions as a control |
| **resource_id** | Affected Wiz resource ID, stored as metadata |
| resource_name | Affected resource name |
| **resource_type** | Affected resource type |
| resource_native_type | Affected resource native type |
| resource_region | Affected resource region |
| resource_cloud_platform | Affected resource cloud platform |
| **resource_external_id** | Native identifier for the affected resource |
| resource_status | Affected resource status |
| **subscription_id** | Wiz subscription/account ID |
| **subscription_external_id** | Cloud account/subscription/project external ID |
| subscription_name | Cloud account/subscription/project name |
| **cloud_account_ids** | Cloud account IDs associated with a detection |
| **cloud_account_names** | Cloud account names associated with a detection |
| **cloud_organization_ids** | Cloud organization IDs associated with a detection |
| cloud_organization_names | Cloud organization names associated with a detection |
| **actor_ids** | Actor IDs associated with a detection |
| actor_names | Actor names associated with a detection |
| **origins** | Detection origins |
| triggering_event_ids | Detection triggering event IDs |
| **project_ids** | Wiz project IDs associated with the finding |
| **project_names** | Wiz project names associated with the finding |

### Relationships

```cypher
(WizFinding)<-[:RESOURCE]-(WizTenant)
(WizFinding)-[:LINKED_TO]->(CVE)
```
