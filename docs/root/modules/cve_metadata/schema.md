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
| effect\_tags | Controlled-vocabulary labels for the vulnerability's technical effect (see below) |
| effect\_tags\_source | Provenance of `effect_tags`: `cwe`, `cvss`, or `none` |
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

#### effect\_tags

`effect_tags` answers "what does this vulnerability let an attacker do?" using a small
controlled vocabulary, each value anchored to a MITRE ATT&CK tactic / CWE Common Consequence:

| Tag | Anchor |
|-----|--------|
| `execute-code` | ATT&CK Execution / "Execute Unauthorized Code or Commands" |
| `gain-privileges` | ATT&CK Privilege Escalation / "Gain Privileges or Assume Identity" |
| `access-credentials` | ATT&CK Credential Access / "Read Application Data (credentials)" |
| `bypass-control` | ATT&CK Defense Evasion / "Bypass Protection Mechanism" |
| `disclose-data` | "Read Files or Directories" / "Read Application Data" |
| `tamper-data` | ATT&CK Impact / "Modify Application Data" |
| `deny-service` | ATT&CK Impact / "DoS: Crash, Exit, or Restart / Resource Consumption" |

Derivation runs at ingest with strict precedence, so a node draws from exactly one source
(recorded in `effect_tags_source`):

1. **CWE (`cwe`)** — preferred. Union of effects mapped from the node's CWEs via the in-repo
   `CWE_EFFECT_TAGS` table (`cartography/intel/cve_metadata/effect_tags.py`). Uninformative
   CWEs (`NVD-CWE-noinfo`, `NVD-CWE-Other`, generic pillars like `CWE-707`/`CWE-20`) contribute nothing.
2. **CVSS (`cvss`)** — fallback only when stage 1 yields nothing, derived from the decomposed
   CVSS metrics. A "high" C/I/A impact means `HIGH` on v3/v4 or `COMPLETE` on v2:
   high `confidentiality_impact`→`disclose-data`, high `integrity_impact`→`tamper-data`,
   high `availability_impact`→`deny-service`, plus a coarse "straight-shot"
   (`attack_vector=NETWORK` + `privileges_required=NONE` + `user_interaction=NONE` + high `integrity_impact`)
   →`execute-code`. Degrades gracefully across CVSS versions (the straight-shot rule is skipped on v2,
   which lacks `privileges_required` / `user_interaction`).
3. **none (`none`)** — no usable CWE and no usable CVSS: `effect_tags=[]`.

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
