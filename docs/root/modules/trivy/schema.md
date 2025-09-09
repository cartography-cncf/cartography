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

### ImageLayer
Representation of a container image layer derived from Trivy's uncompressed rootfs diff IDs.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the layer (the `diff_id`) |
| diff_id | Uncompressed rootfs diff ID (e.g., `sha256:...`) |

#### Relationships

- Layer adjacency in build order (head to tail):

    ```
    (ImageLayer)-[NEXT]->(ImageLayer)
    ```

- Image head/tail attachment:

    ```
    (ECRImage)-[HEAD]->(ImageLayer)
    (ECRImage)-[TAIL]->(ImageLayer)
    ```

- Package attribution (when Trivy provides `.Layer.DiffID`):

    ```
    (Package)-[INTRODUCED_IN]->(ImageLayer)
    ```

Notes:
- ECRImages also have a derived property `length` indicating the number of layers (diff_ids).
- Layers are shared across images; cleanup does not remove layers by default unless they become orphaned (see lineage docs).

### Package
Representation of a package installed in a container image.

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

#### Relationships

- A Package is deployed in an ECRImage.

    ```
    (Package)-[DEPLOYED]->(ECRImage)
    ```

- A Package is affected by a TrivyImageFinding.

    ```
    (Package)<-[AFFECTS]-(TrivyImageFinding)
    ```

- A Package is attributed to the layer that introduced it when available.

    ```
    (Package)-[INTRODUCED_IN]->(ImageLayer)
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

- A TrivyFix should update a Package.

    ```
    (TrivyFix)-[SHOULD_UPDATE_TO]->(Package)
    ```

- A TrivyFix applies to a TrivyImageFinding.

    ```
    (TrivyFix)-[APPLIES_TO]->(TrivyImageFinding)
    ```

### Image lineage
Derived from the ImageLayer chain using longest-prefix base matching. See the lineage page for details.

```
(child:ECRImage)-[BUILT_FROM]->(base:ECRImage)
```
