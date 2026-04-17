## Socket.dev Schema

### SocketDevOrganization

Represents a Socket.dev [Organization](https://docs.socket.dev/reference), the top-level tenant for all Socket.dev resources.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique organization identifier |
| **slug** | Organization slug used in API URLs |
| name | Organization display name |
| plan | Subscription plan (e.g. enterprise, team) |
| image | Organization image URL |

#### Relationships

- A SocketDevOrganization contains SocketDevRepository's

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevRepository)
    ```

- A SocketDevOrganization contains SocketDevDependency's

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevDependency)
    ```

- A SocketDevOrganization contains SocketDevAlert's

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevAlert)
    ```

### SocketDevRepository

Represents a repository monitored by Socket.dev for supply chain security.

> **Ontology Mapping**: This node has the extra label `CodeRepository` to enable cross-platform queries for code repositories across different systems (e.g., GitHubRepository, GitLabProject).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique repository identifier |
| **name** | Repository name |
| **slug** | Repository slug |
| description | Repository description |
| visibility | Repository visibility (public or private) |
| archived | Whether the repository is archived |
| default_branch | Default branch name |
| homepage | Repository homepage URL |
| created_at | Repository creation timestamp |
| updated_at | Repository last update timestamp |

#### Relationships

- A SocketDevRepository belongs to a SocketDevOrganization

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevRepository)
    ```

- A SocketDevRepository has SocketDevDependency's

    ```
    (SocketDevDependency)-[FOUND_IN]->(SocketDevRepository)
    ```

- A SocketDevRepository has SocketDevAlert's

    ```
    (SocketDevAlert)-[FOUND_IN]->(SocketDevRepository)
    ```

### SocketDevDependency

Represents an open-source dependency tracked by Socket.dev across the organization's repositories.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique dependency identifier |
| **name** | Package name (e.g. lodash, express) |
| version | Package version |
| ecosystem | Package ecosystem (e.g. npm, pypi, maven, golang) |
| namespace | Package namespace (if applicable) |
| direct | Whether this is a direct dependency (true) or transitive (false) |
| repo_slug | Repository slug where the dependency was found |

#### Relationships

- A SocketDevDependency belongs to a SocketDevOrganization

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevDependency)
    ```

- A SocketDevDependency is found in a SocketDevRepository

    ```
    (SocketDevDependency)-[FOUND_IN]->(SocketDevRepository)
    ```

### SocketDevAlert

Represents a security alert from Socket.dev. Alerts cover vulnerabilities (CVE), supply chain risks (malware, typosquatting), quality issues, maintenance concerns, and license violations.

> **Ontology Mapping**: This node has the extra label `Risk` to enable cross-platform queries for security findings across different systems (e.g., TrivyImageFinding, S1AppFinding, AWSInspectorFinding).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique alert identifier |
| key | Alert deduplication key |
| **type** | Alert type (e.g. criticalCVE, malware, unmaintained, obfuscatedFile) |
| **category** | Alert category: vulnerability, supplyChainRisk, quality, maintenance, license |
| **severity** | Alert severity: low, medium, high, critical |
| status | Alert status: open or cleared |
| title | Human-readable alert title |
| description | Detailed alert description |
| dashboard_url | Link to the alert in the Socket.dev dashboard |
| created_at | Alert creation timestamp |
| updated_at | Alert last update timestamp |
| cleared_at | Timestamp when the alert was cleared (if applicable) |
| cve_id | CVE identifier (when category is vulnerability) |
| cvss_score | CVSS score 0-10 (when category is vulnerability) |
| epss_score | EPSS probability score (when category is vulnerability) |
| epss_percentile | EPSS percentile (when category is vulnerability) |
| is_kev | Whether this is a CISA Known Exploited Vulnerability |
| first_patched_version | First version that fixes the vulnerability |
| action | Alert action from security policy (error, warn, monitor, ignore) |
| repo_slug | Repository slug where the alert was found |
| branch | Branch where the alert was found |
| artifact_name | Affected package name |
| artifact_version | Affected package version |
| artifact_type | Affected package ecosystem |

#### Relationships

- A SocketDevAlert belongs to a SocketDevOrganization

    ```
    (SocketDevOrganization)-[RESOURCE]->(SocketDevAlert)
    ```

- A SocketDevAlert is found in a SocketDevRepository

    ```
    (SocketDevAlert)-[FOUND_IN]->(SocketDevRepository)
    ```
