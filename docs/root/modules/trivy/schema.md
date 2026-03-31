## Trivy Schema

### TrivyImageFinding
Representation of a vulnerability finding in a container image.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the finding (format: TIF|CVE-ID) |
| name | The vulnerability ID (e.g. CVE-2024-1234) |
| cve_id | The CVE identifier |
| description | Description of the vulnerability |
| last_modified_date | Date when the vulnerability was last modified |
| primary_url | Primary URL for vulnerability information |
| published_date | Date when the vulnerability was published |
| severity | Severity level of the vulnerability |
| severity_source | Source of the severity rating |
| title | Title of the vulnerability |
| cvss_nvd_v2_score | CVSS v2 score from NVD |
| cvss_nvd_v2_vector | CVSS v2 vector from NVD |
| cvss_nvd_v3_score | CVSS v3 score from NVD |
| cvss_nvd_v3_vector | CVSS v3 vector from NVD |
| cvss_redhat_v3_score | CVSS v3 score from RedHat |
| cvss_redhat_v3_vector | CVSS v3 vector from RedHat |
| cvss_ubuntu_v3_score | CVSS v3 score from Ubuntu |
| cvss_ubuntu_v3_vector | CVSS v3 vector from Ubuntu |
| class_name | Class of the vulnerability (e.g. os, library) |
| type | Type of the vulnerability |

#### Relationships

- A TrivyImageFinding affects an ECRImage.

    ```
    (TrivyImageFinding)-[AFFECTS]->(ECRImage)
    ```

- A TrivyImageFinding affects a GCPArtifactRegistryContainerImage.

    ```
    (TrivyImageFinding)-[AFFECTS]->(GCPArtifactRegistryContainerImage)
    ```

- A TrivyImageFinding affects a GCPArtifactRegistryPlatformImage.

    ```
    (TrivyImageFinding)-[AFFECTS]->(GCPArtifactRegistryPlatformImage)
    ```

- A TrivyImageFinding affects a GitLabContainerImage.

    ```
    (TrivyImageFinding)-[AFFECTS]->(GitLabContainerImage)
    ```

### TrivyPackage
Representation of a package installed in a container image, as detected by Trivy.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the package (format: version|name) |
| installed_version | Version of the installed package |
| name | Name of the package |
| version | Version of the package (same as installed_version) |
| class_name | Class of the package (e.g. os, library) |
| type | Type of the package |
| purl | Package URL (e.g., `pkg:npm/express@4.18.2`) |
| pkg_id | Package identifier from Trivy |
| **normalized_id** | Normalized ID for cross-tool matching (format: `{type}\|{namespace/}{name}\|{version}`). Indexed. |

#### Relationships

- A TrivyPackage is deployed in an ECRImage.

    ```
    (TrivyPackage)-[DEPLOYED]->(ECRImage)
    ```

- A TrivyPackage is deployed in a GCPArtifactRegistryContainerImage.

    ```
    (TrivyPackage)-[DEPLOYED]->(GCPArtifactRegistryContainerImage)
    ```

- A TrivyPackage is deployed in a GCPArtifactRegistryPlatformImage.

    ```
    (TrivyPackage)-[DEPLOYED]->(GCPArtifactRegistryPlatformImage)
    ```

- A TrivyPackage is deployed in a GitLabContainerImage.

    ```
    (TrivyPackage)-[DEPLOYED]->(GitLabContainerImage)
    ```

- A TrivyPackage is affected by a TrivyImageFinding.

    ```
    (TrivyPackage)<-[AFFECTS]-(TrivyImageFinding)
    ```

- A canonical Package (ontology) is detected as a TrivyPackage.

    ```
    (Package)-[DETECTED_AS]->(TrivyPackage)
    ```

### TrivyFix
Representation of a fix for a vulnerability.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the fix (format: version|name) |
| version | Version that fixes the vulnerability |
| class_name | Class of the fix (e.g. os, library) |
| type | Type of the fix |

#### Relationships

- A TrivyPackage should update to a TrivyFix.

    ```
    (TrivyPackage)-[SHOULD_UPDATE_TO]->(TrivyFix)
    ```

- A TrivyFix applies to a TrivyImageFinding.

    ```
    (TrivyFix)-[APPLIES_TO]->(TrivyImageFinding)
    ```
