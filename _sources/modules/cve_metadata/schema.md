## CVE Metadata Schema

### CVEMetadata

Enrichment metadata for a [CVE](../cve/schema.md) node, sourced from NVD and EPSS.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The CVE ID (e.g., CVE-2024-22075) |
| description | The english description of the vulnerability |
| references | Reference URLs |
| problem\_types | A list of CWE identifiers |
| cvss\_version | The CVSS version used (4.0, 3.1, 3.0, or 2.0) |
| vector\_string | The CVSS vector string |
| attack\_vector | The CVSS attack vector |
| attack\_complexity | The CVSS attack complexity |
| privileges\_required | The CVSS privileges required |
| user\_interaction | The CVSS user interaction |
| scope | The CVSS scope |
| confidentiality\_impact | The CVSS confidentiality impact |
| integrity\_impact | The CVSS integrity impact |
| availability\_impact | The CVSS availability impact |
| base\_score | The CVSS base score |
| base\_severity | The CVSS severity (CRITICAL, HIGH, MEDIUM, LOW) |
| exploitability\_score | The CVSS exploitability score |
| impact\_score | The CVSS impact score |
| published\_date | The date the CVE was published |
| last\_modified\_date | The date the CVE was last modified |
| vuln\_status | The vulnerability analysis status |
| is\_kev | Whether this CVE is in the CISA KEV catalog (indexed) |
| cisa\_exploit\_add | Date added to CISA KEV catalog (if applicable) |
| cisa\_action\_due | CISA remediation due date (if applicable) |
| cisa\_required\_action | CISA required remediation action (if applicable) |
| cisa\_vulnerability\_name | CISA vulnerability name (if applicable) |
| epss\_score | EPSS probability of exploitation (0.0-1.0) |
| epss\_percentile | EPSS percentile ranking (0.0-1.0) |

### CVEMetadataFeed

Represents the CVE metadata enrichment feed. Used as a sub-resource for lifecycle management.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Feed identifier (CVE\_METADATA) |
| source\_nvd | Whether NVD enrichment was enabled for this sync |
| source\_epss | Whether EPSS enrichment was enabled for this sync |

#### Relationships

- A CVEMetadata enriches a CVE

    ```
    (:CVEMetadata)-[:ENRICHES]->(:CVE)
    ```

- A CVEMetadataFeed is the resource for CVEMetadata nodes

    ```
    (:CVEMetadataFeed)-[:RESOURCE]->(:CVEMetadata)
    ```
