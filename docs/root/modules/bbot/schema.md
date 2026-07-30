## BBOT Schema

BBOT events are represented by concrete labels rather than a shared event label. Duplicate occurrences within the selected scan are aggregated into one node. Their tags, modules, resolved hosts, occurrence UUIDs, parent UUIDs, and discovery contexts are unioned; the smallest scope distances and most recent observation properties are retained.

BBOT's `uuid` identifies an individual occurrence and is stored only in observation metadata. Node identity never uses occurrence UUIDs.

## Nodes

### Common properties

The following properties may appear on each concrete BBOT node:

| Field | Description |
|---|---|
| firstseen | Timestamp when Cartography first created the stable node |
| lastupdated | Update tag from the most recent selected scan containing the node |
| **id** | Stable node identity described below |
| bbot_ids | BBOT deduplication IDs represented by the aggregated node |
| event_type | Original BBOT event type |
| data | Original event data, serialized for structured values |
| host | Normalized hostname or IP address, when present |
| port | Effective port, when present |
| url | Canonical URL, when present |
| scan_id | BBOT scan ID associated with the observation |
| occurrence_uuids | UUIDs of the occurrences aggregated in the selected scan |
| occurrence_count | Number of occurrences aggregated in the selected scan |
| parent_uuids | Parent occurrence UUIDs observed in the selected scan |
| tags | Union of BBOT tags for the selected scan |
| modules | Union of BBOT detector modules for the selected scan |
| resolved_hosts | Union of resolved DNS/IP targets for the selected scan |
| discovery_contexts | Union of BBOT discovery context strings |
| scope_distance | Minimum BBOT scope distance among occurrences |
| web_spider_distance | Minimum BBOT web spider distance among occurrences |
| observed_at | Timestamp of the latest aggregated occurrence |
| source_uri | Report URI from which the selected scan was loaded |

The node-specific tables below supplement these common properties.

### BbotScan

Represents the selected completed BBOT scan.

| Field | Description |
|---|---|
| **id** | BBOT scan `id` |
| name | Scan name |
| status | Scan status |
| started_at | Scan start time |
| finished_at | Scan completion time |
| duration_seconds | Scan duration in seconds |
| targets | Scan seed targets |

#### Relationships

- Every non-scan BBOT node points to the selected scan:

    ```
    (Bbot*)-[OBSERVED_IN]->(BbotScan)
    ```

### BbotDNSName

Represents a normalized DNS name. This node also has the semantic `DNSRecord` label.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the normalized DNS name |
| name | Normalized DNS name |

#### Relationships

```
(BbotDNSName)-[RESOLVES_TO]->(BbotDNSName|BbotIPAddress)
(BbotDNSName)-[HAS_OPEN_PORT]->(BbotOpenTCPPort)
(BbotDNSName)-[MATCHES_DNS_RECORD]->(DNSRecord)
```

### BbotIPAddress

Represents a canonical IPv4 or IPv6 address.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the canonical address |
| ip_address | Canonical IP address |
| public_ip_address | Canonical address when globally routable, otherwise null |
| is_global | Whether the address is globally routable |

#### Relationships

```
(BbotIPAddress)-[HAS_OPEN_PORT]->(BbotOpenTCPPort)
(BbotIPAddress)-[ANNOUNCED_BY]->(BbotASN)
(BbotIPAddress)-[MATCHES_PUBLIC_IP]->(PublicIP)
```

Globally routable nodes contribute to canonical `PublicIP` reconciliation. A `PublicIP` remains while any BBOT or provider source observes it.

### BbotIPRange

Represents a canonical IP network.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the canonical network |
| network | Canonical CIDR |

#### Relationships

This node uses the common `OBSERVED_IN` and `DISCOVERED_FROM` relationships.

### BbotOpenTCPPort

Represents an open TCP endpoint.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the normalized host and TCP port |
| host | Normalized hostname or IP address |
| port | TCP port |
| endpoint | BBOT endpoint display value |

#### Relationships

```
(BbotDNSName|BbotIPAddress)-[HAS_OPEN_PORT]->(BbotOpenTCPPort)
```

URLs, technologies, and findings can also point to this node through `HOSTED_BY`, `DETECTED_ON`, and `AFFECTS`.

### BbotURL

Represents a canonical URL using BBOT's configured URL-deduplication behavior.

| Field | Description |
|---|---|
| **id** | BBOT URL `id` |
| name | Canonical URL |
| url | Canonical URL |

#### Relationships

```
(BbotURL)-[HOSTED_BY]->(BbotOpenTCPPort|BbotDNSName|BbotIPAddress)
```

Technologies and findings can point to this node through `DETECTED_ON` and `AFFECTS`.

### BbotASN

Represents an autonomous system.

| Field | Description |
|---|---|
| **id** | BBOT `id`, based on ASN number |
| asn | Autonomous system number |
| name | Autonomous system name |
| country | Country code |
| description | Autonomous system description |
| subnet | Associated network |

#### Relationships

```
(BbotIPAddress)-[ANNOUNCED_BY]->(BbotASN)
```

### BbotTechnology

Represents a technology detected on a host, effective port, or URL.

| Field | Description |
|---|---|
| **id** | BBOT `id` for host, effective port, and normalized technology |
| technology | Normalized technology name |
| host | Normalized hostname or IP address |
| port | Effective port |
| url | Canonical URL when present |

#### Relationships

```
(BbotTechnology)-[DETECTED_ON]->(BbotURL|BbotOpenTCPPort|BbotDNSName|BbotIPAddress)
```

### BbotEmailAddress

Represents a normalized email address.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the normalized address |
| email | Email address |

#### Relationships

This node uses the common `OBSERVED_IN` and `DISCOVERED_FROM` relationships.

### BbotOrgStub

Represents a normalized organization stub.

| Field | Description |
|---|---|
| **id** | BBOT `id` for the normalized organization stub |
| organization | Normalized organization value |

#### Relationships

This node uses the common `OBSERVED_IN` and `DISCOVERED_FROM` relationships.

### BbotSocial

Represents a social profile.

| Field | Description |
|---|---|
| **id** | SHA-256 fingerprint of platform and canonical profile URL, falling back to normalized profile name |
| platform | Social platform |
| profile_name | Profile name |
| url | Canonical profile URL |

#### Relationships

This node uses the common `OBSERVED_IN` and `DISCOVERED_FROM` relationships.

### BbotStorageBucket

Represents an object storage bucket.

| Field | Description |
|---|---|
| **id** | Provider and normalized bucket name |
| bucket_provider | Normalized provider |
| bucket_name | Normalized bucket name |
| url | Mutable endpoint URL |

#### Relationships

Findings can point to this node:

```
(BbotFinding)-[AFFECTS]->(BbotStorageBucket)
```

### BbotFinding / SecurityIssue

Represents a security finding. This node also has the semantic `SecurityIssue` label and normalized title and severity fields for cross-scanner queries.

| Field | Description |
|---|---|
| **id** | SHA-256 fingerprint of detector module, affected target, and normalized finding name; legacy unnamed findings use normalized description |
| finding_name | Stable finding name when present |
| severity | Reported severity |
| confidence | Reported confidence |
| description | Explanatory text |
| cves | Associated CVE identifiers |

Finding identity excludes severity, confidence, timestamps, CVEs, and explanatory text when a stable name exists. Changes to those fields update the existing node.

#### Relationships

```
(BbotFinding)-[AFFECTS]->(BbotURL|BbotOpenTCPPort|BbotStorageBucket|BbotDNSName|BbotIPAddress)
```

## Relationship lifecycle

Every non-scan node has an `OBSERVED_IN` relationship to the selected `BbotScan`. When the parent occurrence can be resolved to a supported concrete node, the child has a `DISCOVERED_FROM` relationship to that parent. If BBOT's direct parent type is unsupported, Cartography walks the occurrence's parent chain to the nearest supported ancestor.

Relationships are merged by type and endpoints. They preserve `firstseen`, refresh `lastupdated`, and are removed when the association disappears from the selected scan.

[BBOT event IDs](https://www.blacklanternsecurity.com/bbot/Stable/scanning/events/#event-attributes) combine event type with a SHA-1 hash of BBOT's deduplication data. Cartography reuses that ID when its deduplication semantics represent durable asset identity.
