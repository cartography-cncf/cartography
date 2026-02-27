## Ubuntu Schema

### UbuntuCVEFeed

Represents the Ubuntu Security CVE data feed. This is a root node that serves as the parent for all UbuntuCVE nodes.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The feed identifier |
| name | The name of the feed |
| url | The URL of the Ubuntu Security API |

### UbuntuCVE

Representation of a CVE from the [Ubuntu Security API](https://ubuntu.com/security/cves). This node also carries the `CVE` label.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The CVE ID (e.g., CVE-2024-1234) |
| description | The CVE description |
| ubuntu\_description | Ubuntu-specific description of the vulnerability |
| priority | Ubuntu's priority rating (critical, high, medium, low, negligible) |
| status | The status of the CVE (e.g., active) |
| cvss3 | The CVSS v3 base score |
| published | The date the CVE was published |
| updated\_at | The date the CVE was last updated |
| codename | Ubuntu release codename |
| mitigation | Mitigation information if available |
| attack\_vector | CVSS v3 attack vector |
| attack\_complexity | CVSS v3 attack complexity |
| base\_score | CVSS v3 base score |
| base\_severity | CVSS v3 base severity |
| confidentiality\_impact | CVSS v3 confidentiality impact |
| integrity\_impact | CVSS v3 integrity impact |
| availability\_impact | CVSS v3 availability impact |

#### Relationships

- UbuntuCVE nodes are linked to their feed

    ```
    (UbuntuCVEFeed)-[:RESOURCE]->(UbuntuCVE)
    ```

### UbuntuSecurityNotice

Representation of a Ubuntu Security Notice (USN) from the [Ubuntu Security API](https://ubuntu.com/security/notices).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The USN ID (e.g., USN-6600-1) |
| title | The title of the security notice |
| summary | A brief summary of the notice |
| description | The full description of the notice |
| published | The date the notice was published |
| notice\_type | The type of notice (e.g., USN) |
| instructions | Instructions for remediation |
| is\_hidden | Whether the notice is hidden |

#### Relationships

- UbuntuSecurityNotice addresses one or more CVEs

    ```
    (UbuntuSecurityNotice)-[:ADDRESSES]->(UbuntuCVE)
    ```
