## Endor Labs Schema

### EndorLabsNamespace

Represents an Endor Labs [namespace](https://docs.endorlabs.com/), the top-level tenant for all Endor Labs resources.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Namespace identifier |
| **name** | Namespace name |

#### Relationships

- An EndorLabsNamespace contains EndorLabsProject's

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsProject)
    ```

- An EndorLabsNamespace contains EndorLabsPackageVersion's

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsPackageVersion)
    ```

- An EndorLabsNamespace contains EndorLabsDependencyMetadata's

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsDependencyMetadata)
    ```

- An EndorLabsNamespace contains EndorLabsFinding's

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsFinding)
    ```

### EndorLabsProject

Represents a project scanned by Endor Labs.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique project UUID |
| **name** | Project name (e.g. acme/frontend-app) |
| namespace | Tenant namespace |
| description | Project description |
| platform_source | Source platform (e.g. PLATFORM_SOURCE_GITHUB) |
| git_http_clone_url | Git HTTP clone URL |
| scan_state | Current scan state (e.g. SCAN_STATE_IDLE) |

#### Relationships

- An EndorLabsProject belongs to an EndorLabsNamespace

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsProject)
    ```

- An EndorLabsProject has EndorLabsPackageVersion's

    ```
    (EndorLabsPackageVersion)-[FOUND_IN]->(EndorLabsProject)
    ```

- An EndorLabsProject has EndorLabsFinding's

    ```
    (EndorLabsFinding)-[FOUND_IN]->(EndorLabsProject)
    ```

### EndorLabsPackageVersion

Represents a specific version of a package discovered in an Endor Labs project.

> **Ontology Mapping**: This node has the extra label `Dependency`. It is linked to the abstract `Package` ontology node via `(:Package)-[:DETECTED_AS]->(:EndorLabsPackageVersion)` using the `normalized_id` field for cross-tool matching with Trivy, Syft, and Socket.dev.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique package version UUID |
| **name** | Full package identifier (e.g. npm://lodash@4.17.21) |
| namespace | Tenant namespace |
| ecosystem | Package ecosystem (e.g. ECOSYSTEM_NPM, ECOSYSTEM_PYPI) |
| package_name | Package name without ecosystem prefix |
| version | Package version |
| purl | Package URL for cross-tool identification |
| **normalized_id** | Normalized package ID for cross-tool matching |
| release_timestamp | Package release date |
| call_graph_available | Whether call graph analysis is available |
| project_uuid | Parent project UUID |

#### Relationships

- An EndorLabsPackageVersion belongs to an EndorLabsNamespace

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsPackageVersion)
    ```

- An EndorLabsPackageVersion is found in an EndorLabsProject

    ```
    (EndorLabsPackageVersion)-[FOUND_IN]->(EndorLabsProject)
    ```

- A Package is detected as an EndorLabsPackageVersion (ontology link)

    ```
    (Package)-[DETECTED_AS]->(EndorLabsPackageVersion)
    ```

### EndorLabsDependencyMetadata

Represents a dependency relationship between two package versions in Endor Labs.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique dependency metadata UUID |
| **name** | Dependency package identifier |
| namespace | Tenant namespace |
| direct | Whether this is a direct dependency |
| reachable | Whether the dependency is reachable |
| scope | Dependency scope (e.g. SCOPE_RUNTIME) |
| project_uuid | Parent project UUID |
| importer_uuid | UUID of the importing package version |
| dependency_name | Name of the dependency |

#### Relationships

- An EndorLabsDependencyMetadata belongs to an EndorLabsNamespace

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsDependencyMetadata)
    ```

- An EndorLabsDependencyMetadata is imported by an EndorLabsPackageVersion

    ```
    (EndorLabsDependencyMetadata)-[IMPORTED_BY]->(EndorLabsPackageVersion)
    ```

- An EndorLabsDependencyMetadata depends on an EndorLabsPackageVersion

    ```
    (EndorLabsDependencyMetadata)-[DEPENDS_ON]->(EndorLabsPackageVersion)
    ```

### EndorLabsFinding

Represents a security finding from Endor Labs. Findings cover vulnerabilities, supply chain risks, license issues, malware, and more.

> **Ontology Mapping**: This node has the extra label `Risk` to enable cross-platform queries for security findings across different systems (e.g., SocketDevAlert, TrivyImageFinding, AWSInspectorFinding).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique finding UUID |
| **name** | Finding name |
| namespace | Tenant namespace |
| summary | Finding description |
| **level** | Severity level: FINDING_LEVEL_CRITICAL, HIGH, MEDIUM, LOW |
| finding_categories | Finding categories (VULNERABILITY, SUPPLY_CHAIN, LICENSE_RISK, MALWARE, SECRETS, SAST) |
| finding_tags | Finding tags (e.g. REACHABLE_FUNCTION, FIX_AVAILABLE) |
| target_dependency_name | Affected package name |
| target_dependency_version | Affected package version |
| target_dependency_package_name | Fully qualified package name (e.g. npm://lodash@4.17.21) |
| proposed_version | Recommended upgrade version |
| remediation | Fix guidance |
| remediation_action | Action type: UPGRADE, REMOVE, REPLACE, REVIEW |
| project_uuid | Parent project UUID |
| **cve_id** | CVE identifier (when finding is a vulnerability) |
| create_time | Finding creation timestamp |

#### Relationships

- An EndorLabsFinding belongs to an EndorLabsNamespace

    ```
    (EndorLabsNamespace)-[RESOURCE]->(EndorLabsFinding)
    ```

- An EndorLabsFinding is found in an EndorLabsProject

    ```
    (EndorLabsFinding)-[FOUND_IN]->(EndorLabsProject)
    ```

- A CVE is linked to an EndorLabsFinding

    ```
    (CVE)-[LINKED_TO]->(EndorLabsFinding)
    ```
