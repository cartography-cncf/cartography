## BBOT Schema

BBOT events are represented by concrete labels rather than a shared event label. Duplicate occurrences within the selected scan are aggregated into one node. Their tags, modules, resolved hosts, occurrence UUIDs, parent UUIDs, and discovery contexts are unioned; the smallest scope distances and most recent observation properties are retained.

BBOT's `uuid` identifies an individual occurrence and is stored only in observation metadata. Node identity never uses occurrence UUIDs.

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

### Stable identities

[BBOT event IDs](https://www.blacklanternsecurity.com/bbot/Stable/scanning/events/#event-attributes) combine event type with a SHA-1 hash of BBOT's deduplication data. Cartography reuses that ID for event types whose deduplication semantics represent durable asset identity.

| Node label | Stable identity and notable properties |
|---|---|
| `BbotScan` | BBOT scan `id`; name, status, start/finish times, duration, and targets are mutable |
| `BbotDNSName:DNSRecord` | BBOT `id` for the normalized DNS name; `name` contains the normalized value |
| `BbotIPAddress` | BBOT `id` for the canonical address; `ip_address` and `is_global` describe the address |
| `BbotIPRange` | BBOT `id` for the canonical network; `network` contains the canonical CIDR |
| `BbotOpenTCPPort` | BBOT `id` for normalized host and TCP port; `endpoint` contains the BBOT display value |
| `BbotURL` | BBOT `id`, preserving BBOT's configured URL-deduplication behavior |
| `BbotASN` | BBOT `id`, based on ASN number; `asn`, `name`, `country`, `description`, and `subnet` may be present |
| `BbotTechnology` | BBOT `id`, based on host, effective port, and normalized technology |
| `BbotEmailAddress` | BBOT `id` for the normalized address; `email` contains the address |
| `BbotOrgStub` | BBOT `id` for the normalized organization stub; `organization` contains the normalized value |
| `BbotSocial` | SHA-256 fingerprint of platform and canonical profile URL, falling back to normalized profile name |
| `BbotStorageBucket` | Provider and normalized bucket name; `url` remains mutable |
| `BbotFinding` | SHA-256 fingerprint of detector module, affected target, and normalized finding name; legacy unnamed findings use normalized description |

Finding identity excludes severity, confidence, timestamps, CVEs, and explanatory text when a stable name is available. Changes to those fields update the existing node.

### Relationships

| Pattern | Meaning |
|---|---|
| `(:BbotDNSName)-[:RESOLVES_TO]->(:BbotDNSName|BbotIPAddress)` | DNS target present in the selected scan |
| `(:BbotDNSName|BbotIPAddress)-[:HAS_OPEN_PORT]->(:BbotOpenTCPPort)` | Open TCP port observed on a host |
| `(:BbotURL)-[:HOSTED_BY]->(:BbotOpenTCPPort|BbotDNSName|BbotIPAddress)` | Host or endpoint serving a URL |
| `(:BbotTechnology)-[:DETECTED_ON]->(:BbotURL|BbotOpenTCPPort|BbotDNSName|BbotIPAddress)` | Technology detected on an observed target |
| `(:BbotFinding)-[:AFFECTS]->(:BbotURL|BbotOpenTCPPort|BbotStorageBucket|BbotDNSName|BbotIPAddress)` | Asset affected by a finding |
| `(:BbotIPAddress)-[:ANNOUNCED_BY]->(:BbotASN)` | ASN associated with an observed address |
| `(:BbotDNSName)-[:MATCHES_DNS_RECORD]->(:DNSRecord)` | Case-insensitive match to a provider DNS record |
| `(:BbotIPAddress)-[:MATCHES_PUBLIC_IP]->(:PublicIP)` | Exact match to a provider-derived public IP |

Every non-scan node has an `OBSERVED_IN` relationship to the selected `BbotScan`. When the parent occurrence can be resolved to a supported concrete node, the child also has a `DISCOVERED_FROM` relationship to that parent. If BBOT's direct parent type is unsupported, Cartography walks the occurrence's parent chain to the nearest supported ancestor.

Relationships are merged by type and endpoints. They preserve `firstseen`, refresh `lastupdated`, and are removed when the association disappears from the selected scan.
