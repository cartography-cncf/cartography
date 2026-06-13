# Tenable Schema

## Overview

Cartography ingests assets and vulnerability findings from the [Tenable Export API](https://developer.tenable.com/reference/export-assets-v2). The integration uses the async bulk-export workflow (POST to initiate, poll for status, download chunks) to retrieve complete datasets efficiently.

## Configuration

| CLI flag | Default | Required | Description |
|---|---|---|---|
| `--tenable-access-key-env-var` | `TENABLE_ACCESS_KEY` | Yes | Environment variable holding the Tenable API access key |
| `--tenable-secret-key-env-var` | `TENABLE_SECRET_KEY` | Yes | Environment variable holding the Tenable API secret key |
| `--tenable-url` | `https://cloud.tenable.com` | No | Base URL of the Tenable API endpoint |
| `--tenable-tenant-id` | hostname of `--tenable-url` | No | Identifier used to scope all graph nodes for this Tenable instance. Set this to the **container UUID** shown in your Tenable account settings when running multiple tenants or using a custom URL. Defaults to the hostname portion of `--tenable-url` (e.g. `cloud.tenable.com`). |
| `--tenable-findings-lookback-days` | `180` | No | Number of days of vulnerability findings to retrieve on each sync. Tenable's export API filters on `last_found >= now - lookback_days`. Stale findings outside this window are removed from the graph by the cleanup job. |

## Nodes

### TenableTenant

Represents the Tenable instance being synced. All other Tenable nodes are scoped under this node via `RESOURCE` relationships.

| Field | Description |
|---|---|
| **id** | The tenant identifier: the container UUID from Tenable account settings when `--tenable-tenant-id` is set, otherwise the hostname of `--tenable-url` (default: `cloud.tenable.com`) |
| lastupdated | Timestamp of the last sync run |

### TenableAsset

An asset discovered and tracked by Tenable. Corresponds to a record returned by the [Assets Export v2 API](https://developer.tenable.com/reference/export-assets-v2).

Cloud-provider details live in the `TenableAssetAWS`, `TenableAssetAzure`, and `TenableAssetGCP` sub-nodes; only the cloud identifier keys are stored here for cross-module indexing.

| Field | Description |
|---|---|
| **id** | Asset UUID (Tenable's `id` field) |
| has_agent | Whether a Tenable agent is installed |
| has_plugin_results | Whether plugin scan results exist |
| is_licensed | Whether the asset counts against the license |
| is_public | Whether the asset has a public IP |
| types | Asset type list (e.g. `["host", "cloud"]`) |
| system_types | System type list (e.g. `["aws-ec2-instance"]`) |
| operating_systems | List of operating system strings |
| serial_number | Hardware serial number (indexed) |
| tenable_agent_days_since_active | Days since the Tenable agent last checked in |
| created_at_timestamps | Timestamp when the asset was first created in Tenable |
| updated_at_timestamps | Timestamp of the most recent asset update |
| first_seen_timestamps | Timestamp when the asset was first observed |
| last_seen_timestamps | Timestamp when the asset was last observed |
| first_scan_time | Timestamp of the first scan |
| last_scan_time | Timestamp of the most recent scan |
| last_authenticated_scan_date | Timestamp of the most recent authenticated scan |
| last_licensed_scan_date | Timestamp of the most recent licensed scan |
| last_scan_id | ID of the most recent scan |
| network_id | Tenable network container ID |
| **fqdn** | Primary FQDN (first entry of `fqdns`); indexed for cross-module relationship matching |
| fqdns | Full list of FQDNs |
| hostnames | List of hostnames |
| ipv4s | List of IPv4 addresses |
| ipv6s | List of IPv6 addresses |
| mac_addresses | List of MAC addresses |
| **aws_ec2_instance_id** | AWS EC2 instance ID (indexed) |
| **azure_vm_id** | Azure VM ID (indexed) |
| **gcp_instance_id** | GCP instance ID (indexed) |
| acr_score | Asset Criticality Rating (0–10) |
| aes_score | Asset Exposure Score |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAsset)
(:TenableAsset)-[:MEMBER_OF_NETWORK]->(:TenableNetwork)
(:TenableAsset)-[:HAS_AWS_INFO]->(:TenableAssetAWS)
(:TenableAsset)-[:HAS_AZURE_INFO]->(:TenableAssetAzure)
(:TenableAsset)-[:HAS_GCP_INFO]->(:TenableAssetGCP)
(:TenableAsset)-[:HAS_SOURCE]->(:TenableAssetSource)
(:TenableAsset)-[:HAS_TAG]->(:TenableAssetTag)
```

### TenableAssetAWS

AWS-specific cloud details for a Tenable asset. The `id` is the EC2 instance ID.

| Field | Description |
|---|---|
| **id** | EC2 instance ID (`ec2_instance_id` from `cloud.aws`) |
| ec2_instance_ami_id | AMI ID used to launch the instance |
| owner_id | AWS account ID |
| availability_zone | AWS availability zone |
| region | AWS region |
| vpc_id | VPC ID |
| subnet_id | Subnet ID |
| ec2_instance_type | Instance type (e.g. `t3.medium`) |
| ec2_instance_state_name | Instance state (e.g. `running`) |
| ec2_instance_group_name | Security group name |
| ec2_name | Value of the EC2 `Name` tag |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAssetAWS)
(:TenableAsset)-[:HAS_AWS_INFO]->(:TenableAssetAWS)
```

### TenableAssetAzure

Azure-specific cloud details for a Tenable asset. The `id` is the Azure VM ID (GUID).

| Field | Description |
|---|---|
| **id** | Azure VM ID (`vm_id` from `cloud.azure`) |
| **resource_id** | Azure Resource Manager resource ID (indexed) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAssetAzure)
(:TenableAsset)-[:HAS_AZURE_INFO]->(:TenableAssetAzure)
```

### TenableAssetGCP

GCP-specific cloud details for a Tenable asset. The `id` is the GCP instance ID.

| Field | Description |
|---|---|
| **id** | GCP instance ID (`instance_id` from `cloud.gcp`) |
| project_id | GCP project ID |
| zone | GCP zone |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAssetGCP)
(:TenableAsset)-[:HAS_GCP_INFO]->(:TenableAssetGCP)
```

### TenableNetwork

A Tenable logical network container. Multiple assets can belong to the same network.

| Field | Description |
|---|---|
| **id** | Network UUID (`network_id` from the asset export) |
| name | Network name (e.g. `Default`) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableNetwork)
(:TenableAsset)-[:MEMBER_OF_NETWORK]->(:TenableNetwork)
```

### TenableAssetSource

A data source that has observed a Tenable asset (e.g. `NESSUS_AGENT`, `NESSUS_SCAN`, `WAS`). The `id` is scoped to the asset: `{asset_uuid}::{source_name}`.

| Field | Description |
|---|---|
| **id** | Composite key: `asset_uuid::source_name` |
| name | Source name (e.g. `NESSUS_AGENT`) |
| source_first_seen | Timestamp when this source first observed the asset |
| source_last_seen | Timestamp when this source last observed the asset |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAssetSource)
(:TenableAsset)-[:HAS_SOURCE]->(:TenableAssetSource)
```

### TenableAssetTag

A key/value tag applied to a Tenable asset. The `id` is the Tenable tag UUID.

| Field | Description |
|---|---|
| **id** | Tag UUID |
| tag_key | Tag category/key (e.g. `Environment`) |
| tag_value | Tag value (e.g. `Production`) |
| added_by | User who applied the tag |
| added_at | Timestamp when the tag was applied |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableAssetTag)
(:TenableAsset)-[:HAS_TAG]->(:TenableAssetTag)
```

### TenableFinding

A vulnerability instance detected by Tenable on a specific asset. Corresponds to a record returned by the [Vulnerability Export API](https://developer.tenable.com/reference/exports-vulns-request-export).

The `id` is the Tenable finding UUID (`finding_id`). Plugin details live in `TenablePlugin`; scan metadata lives in `TenableScan`.

> **Ontology note:** when `has_cve` is `"true"` the node is also labelled `CVE`, allowing `CVEMetadata` nodes to enrich it automatically via `(:CVEMetadata)-[:ENRICHES]->(:CVE)` (matched on `cve_id`).

| Field | Description |
|---|---|
| **id** | Finding UUID (`finding_id` from the export) |
| **asset_uuid** | UUID of the asset this finding was detected on (indexed) |
| severity | Severity string (`info`, `low`, `medium`, `high`, `critical`) |
| severity_id | Numeric severity (0=info, 1=low, 2=medium, 3=high, 4=critical) |
| severity_default_id | Default numeric severity before any overrides |
| severity_modification_type | Whether severity was manually adjusted (e.g. `NONE`) |
| state | Finding state (`OPEN`, `REOPENED`, `FIXED`) |
| first_found | Timestamp when the finding was first detected |
| last_found | Timestamp when the finding was most recently detected |
| indexed | Timestamp when the finding was indexed in Tenable |
| source | Scanner source (e.g. `NESSUS`) |
| output | Raw scanner output text |
| resurfaced_date | Timestamp when a previously-fixed finding re-appeared |
| time_taken_to_fix | Seconds between first_found and fix (as a string) |
| port | Port number the finding was detected on |
| protocol | Protocol (e.g. `TCP`, `UDP`) |
| service | Service name (e.g. `www`, `cifs`) |
| **cve_id** | First CVE ID from the plugin's CVE list; used for CVEMetadata ontology matching (indexed) |
| cve_list | Full list of CVE IDs associated with this finding |
| has_cve | `"true"` if the plugin has at least one CVE ID, `"false"` otherwise |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableFinding)
(:TenableFinding)-[:AFFECTS]->(:TenableAsset)
(:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)
(:TenableFinding)-[:PART_OF_SCAN]->(:TenableScan)
```

### TenablePlugin

A Tenable plugin that detected one or more findings. Plugins are deduplicated across findings — a single `TenablePlugin` node can be linked to many `TenableFinding` nodes.

| Field | Description |
|---|---|
| **id** | Integer plugin ID (e.g. `156641`) |
| name | Human-readable plugin name |
| family | Plugin family (e.g. `Windows : Microsoft Bulletins`, `CGI abuses`) |
| family_id | Numeric family ID |
| description | Detailed plugin description |
| synopsis | Short summary of what the plugin checks |
| solution | Recommended remediation |
| risk_factor | Qualitative risk (`none`, `low`, `medium`, `high`, `critical`) |
| has_patch | Whether a vendor patch is available |
| has_workaround | Whether a workaround exists |
| vendor_unpatched | Whether the vendor has declined to patch |
| vendor_severity | Vendor-assigned severity label (e.g. `Important`) |
| exploit_available | Whether a known exploit exists |
| exploitability_ease | Ease of exploitation description |
| exploit_framework_metasploit | Whether a Metasploit module exists |
| patch_publication_date | Date the patch was published |
| publication_date | Date the plugin was published |
| modification_date | Date the plugin was last modified |
| vuln_publication_date | Date the vulnerability was disclosed |
| cvss_base_score | CVSS v2 base score |
| cvss_temporal_score | CVSS v2 temporal score |
| cvss3_base_score | CVSS v3 base score |
| cvss3_temporal_score | CVSS v3 temporal score |
| cvss4_base_score | CVSS v4 base score |
| vpr_score | Tenable Vulnerability Priority Rating score |
| epss_score | EPSS probability score |
| cve_list | Full list of CVE IDs associated with this plugin |
| type | Scan type (`local`, `remote`, `combined`) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenablePlugin)
(:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)
```

### TenableScan

A Tenable scan run that produced one or more findings. Scans are deduplicated — multiple findings from the same scan share one `TenableScan` node.

| Field | Description |
|---|---|
| **id** | Scan UUID (`scan.uuid` from the findings export) |
| schedule_uuid | UUID of the scan schedule template |
| started_at | Timestamp when the scan started |
| last_scan_target | IP address or hostname that was most recently scanned |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:TenableTenant)-[:RESOURCE]->(:TenableScan)
(:TenableFinding)-[:PART_OF_SCAN]->(:TenableScan)
```
