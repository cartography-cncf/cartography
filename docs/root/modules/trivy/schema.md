## Trivy Schema

### TrivyImageFinding
Container image vulnerability finding.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier (format: `TIF\|<CVE-ID>`) |
| cve_id | CVE identifier |
| severity | Severity level (CRITICAL, HIGH, MEDIUM, LOW) |
| description | Vulnerability description |
| published_date | Publication date |
| nvd_v3_score | CVSS v3 score from NVD |
| nvd_v3_vector | CVSS v3 vector from NVD |

**Relationships:**
```
(TrivyImageFinding)-[AFFECTS]->(ECRImage)
(TrivyImageFinding)-[AFFECTS]->(Package)
```

### Package
Software package in a container image.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier (format: `<version>\|<name>`) |
| name | Package name |
| installed_version | Installed version |
| type | Package type (e.g., debian, alpine, npm) |

**Relationships:**
```
(Package)-[DEPLOYED]->(ECRImage)
(Package)<-[AFFECTS]-(TrivyImageFinding)
```

### TrivyFix
Available fix for a vulnerability.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier (format: `<fixed_version>\|<package_name>`) |
| version | Fixed version |

**Relationships:**
```
(TrivyFix)-[SHOULD_UPDATE_TO]->(Package)
(TrivyFix)-[APPLIES_TO]->(TrivyImageFinding)
```

### ImageLayer
Container image layer (populated by lineage module).

| Field | Description |
|-------|-------------|
| **id** | Layer diff ID (sha256 hash) |
| diff_id | Uncompressed rootfs diff ID |

**Relationships:**
```
(ImageLayer)-[NEXT]->(ImageLayer)  # Layer chain
(ECRImage)-[HEAD]->(ImageLayer)    # First layer
(ECRImage)-[TAIL]->(ImageLayer)    # Last layer
```

### Image Lineage
Parent-child relationships between container images.

```
(child:ECRImage)-[BUILT_FROM]->(parent:ECRImage)
```

**ECRImage properties added by Trivy module:**
- `length`: Number of layers in the image
- `platforms`: List of supported platforms (e.g., `["linux/amd64", "linux/arm64"]`)

These relationships are automatically created by analyzing shared layer prefixes between images.
