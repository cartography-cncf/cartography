## Docker Scout Schema

### DockerScoutPublicImage
Representation of a public/base image that a container image is built on, as detected by Docker Scout.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the public image (e.g. `python:3.12-slim`) |
| name | Name of the public image (e.g. `python`) |
| tag | Tag of the public image (e.g. `3.12-slim`) |
| version | Version from OCI annotations |
| digest | Digest of the public image |

#### Relationships

- An ECRImage is built on a DockerScoutPublicImage.

    ```
    (ECRImage)-[BUILT_ON]->(DockerScoutPublicImage)
    ```

- A GCPArtifactRegistryContainerImage is built on a DockerScoutPublicImage.

    ```
    (GCPArtifactRegistryContainerImage)-[BUILT_ON]->(DockerScoutPublicImage)
    ```

- A GCPArtifactRegistryPlatformImage is built on a DockerScoutPublicImage.

    ```
    (GCPArtifactRegistryPlatformImage)-[BUILT_ON]->(DockerScoutPublicImage)
    ```

- A GitLabContainerImage is built on a DockerScoutPublicImage.

    ```
    (GitLabContainerImage)-[BUILT_ON]->(DockerScoutPublicImage)
    ```

### DockerScoutPackage
Representation of a package installed in a public/base image, as detected by Docker Scout.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the package (format: `version\|name`) |
| name | Name of the package |
| version | Version of the package |
| namespace | Package namespace (e.g. `debian`) |
| type | Package type (e.g. `deb`, `rpm`) |
| purl | Package URL (e.g. `pkg:deb/debian/libssl3@3.0.15`) |
| **normalized_id** | Normalized ID for cross-tool matching (format: `{type}\|{namespace/}{name}\|{version}`). Indexed. |
| layer_digest | Digest of the image layer containing the package |
| layer_diff_id | Diff ID of the image layer containing the package |

#### Relationships

- A DockerScoutPackage is deployed in an ECRImage.

    ```
    (DockerScoutPackage)-[DEPLOYED]->(ECRImage)
    ```

- A DockerScoutPackage is deployed in a GCPArtifactRegistryContainerImage.

    ```
    (DockerScoutPackage)-[DEPLOYED]->(GCPArtifactRegistryContainerImage)
    ```

- A DockerScoutPackage is deployed in a GCPArtifactRegistryPlatformImage.

    ```
    (DockerScoutPackage)-[DEPLOYED]->(GCPArtifactRegistryPlatformImage)
    ```

- A DockerScoutPackage is deployed in a GitLabContainerImage.

    ```
    (DockerScoutPackage)-[DEPLOYED]->(GitLabContainerImage)
    ```

- A DockerScoutPackage comes from a DockerScoutPublicImage.

    ```
    (DockerScoutPackage)-[FROM_BASE]->(DockerScoutPublicImage)
    ```

- A DockerScoutPackage is affected by a DockerScoutFinding.

    ```
    (DockerScoutPackage)<-[AFFECTS]-(DockerScoutFinding)
    ```

### DockerScoutFinding
Representation of a vulnerability finding in a container image, as detected by Docker Scout. Also labeled as `Risk` and `CVE`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the finding (format: `DSF\|CVE-ID`) |
| name | The vulnerability ID (e.g. `CVE-2024-13176`) |
| cve_id | The CVE identifier. Indexed. |
| source | Source of the vulnerability (e.g. `NVD`) |
| description | Description of the vulnerability |
| url | URL for vulnerability information |
| published_at | Date when the vulnerability was published |
| updated_at | Date when the vulnerability was last updated |
| severity | Severity level of the vulnerability. Indexed. |
| cvss_version | CVSS version used for scoring (e.g. `3.1`) |
| vulnerable_range | Version range affected by the vulnerability |
| cwe_ids | List of CWE identifiers |
| epss_score | EPSS (Exploit Prediction Scoring System) score |
| epss_percentile | EPSS percentile ranking |

#### Relationships

- A DockerScoutFinding affects an ECRImage.

    ```
    (DockerScoutFinding)-[AFFECTS]->(ECRImage)
    ```

- A DockerScoutFinding affects a GCPArtifactRegistryContainerImage.

    ```
    (DockerScoutFinding)-[AFFECTS]->(GCPArtifactRegistryContainerImage)
    ```

- A DockerScoutFinding affects a GCPArtifactRegistryPlatformImage.

    ```
    (DockerScoutFinding)-[AFFECTS]->(GCPArtifactRegistryPlatformImage)
    ```

- A DockerScoutFinding affects a GitLabContainerImage.

    ```
    (DockerScoutFinding)-[AFFECTS]->(GitLabContainerImage)
    ```

- A DockerScoutFinding affects a DockerScoutPackage.

    ```
    (DockerScoutFinding)-[AFFECTS]->(DockerScoutPackage)
    ```

### DockerScoutFix
Representation of a fix for a vulnerability, as detected by Docker Scout. Also labeled as `Fix`.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the fix (format: `fixed_version\|package_id`) |
| version | Version that fixes the vulnerability |

#### Relationships

- A DockerScoutPackage should update to a DockerScoutFix.

    ```
    (DockerScoutPackage)-[SHOULD_UPDATE_TO]->(DockerScoutFix)
    ```

- A DockerScoutFix applies to a DockerScoutFinding.

    ```
    (DockerScoutFix)-[APPLIES_TO]->(DockerScoutFinding)
    ```
