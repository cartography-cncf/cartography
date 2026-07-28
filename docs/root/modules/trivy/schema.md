## Trivy Schema

### TrivyImageFinding::Risk / ::CVE
Representation of a vulnerability finding in a container image.

A Trivy finding can carry identifiers from several schemes: CVEs, but also GitHub advisories
(`GHSA-*`), Debian advisories (`DLA-*`, `DSA-*`, `TEMP-*`), `RUSTSEC-*`, and others. These schemes
are not mutually exclusive, so each identifier field below reflects **which identifiers are present
in the report** (the primary `VulnerabilityID` plus any `VendorIDs`), not which scheme the primary
identifier happens to use.

`:Risk` is applied to every finding. `:CVE` is conditional: it is only set when a CVE identifier is
present (`has_cve = "true"`, i.e. `cve_id` is populated).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the finding, built from the primary `VulnerabilityID` (format: TIF|VULNERABILITY-ID, e.g. `TIF|CVE-2024-1234` or `TIF|GHSA-xxxx-xxxx-xxxx`) |
| name | The primary vulnerability ID, whatever its scheme (e.g. CVE-2024-1234, GHSA-xxxx-xxxx-xxxx) |
| vulnerability_ids | Every identifier the report carries for this finding, primary first: the `VulnerabilityID` plus any `VendorIDs` (e.g. `["CVE-2025-31115", "DSA-5895-1"]`). Identifier authorities without a dedicated field below remain available here |
| cve_id | The CVE identifier, if the finding carries one. Null when no reported identifier is a CVE |
| ghsa_id | The GitHub advisory identifier, if the finding carries one. Null when no reported identifier is a GHSA |
| has_cve | `"true"` when a CVE identifier is present, `"false"` otherwise. Drives the conditional `:CVE` label |
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

- A TrivyImageFinding affects an ontology Image (matched via `_ont_digest`).

    ```
    (TrivyImageFinding)-[AFFECTS]->(Image)
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

- A TrivyPackage is deployed on an ontology Image (matched via `_ont_digest`).

    ```
    (TrivyPackage)-[DEPLOYED]->(Image)
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
