# BBOT

[BBOT](https://www.blacklanternsecurity.com/bbot/) discovers internet-facing
assets and security findings. Cartography ingests the most recently completed
scan from a local report or supported object store.

```{toctree}
config
schema
```

## Supported event types

Cartography ingests `SCAN`, `DNS_NAME`, `IP_ADDRESS`, `IP_RANGE`,
`OPEN_TCP_PORT`, `URL`, `ASN`, `TECHNOLOGY`, `EMAIL_ADDRESS`, `ORG_STUB`,
`SOCIAL`, `STORAGE_BUCKET`, and `FINDING` events. Other event types are logged
and skipped.

Each supported event type uses its own concrete node label. Duplicate
occurrences within the selected scan are aggregated into one node, unioning
tags, modules, resolved hosts, occurrence UUIDs, parent UUIDs, and discovery
contexts while retaining the smallest scope distances and the latest
observation metadata.

BBOT occurrence `uuid` values are observation metadata, not node identities.
Cartography uses BBOT's stable event `id` when its deduplication semantics
represent durable asset identity, and stable fingerprints for the event types
that need Cartography-defined identities.

## Snapshot lifecycle

The selected completed scan is the current BBOT snapshot. Stable assets and
relationships are merged in place, preserving `firstseen` and advancing
`lastupdated`. Nodes or associations absent from the selected scan are deleted.
If an asset later reappears, it is recreated with a new `firstseen`; historical
absence tracking is not retained.

Every non-scan node has an `OBSERVED_IN` relationship to the selected
`BbotScan`. When a parent occurrence can be resolved to a supported node, the
child has a `DISCOVERED_FROM` relationship to that parent. If BBOT's direct
parent type is unsupported, Cartography walks the parent chain to the nearest
supported ancestor. The generated schema documents the other typed asset
relationships.

`BbotDNSName` nodes use the ontology `DNSRecord` label, and `BbotFinding` nodes
use the `SecurityIssue` label. Running the `ontology` stage after `bbot`
attaches what BBOT observed to the cloud resources already in the graph:

- `(:BbotDNSName)-[:MATCHES_DNS_RECORD]->(:DNSRecord)` when a provider DNS record
  has the same name.
- `(:BbotIPAddress)-[:MATCHES_PUBLIC_IP]->(:PublicIP)` for globally routable
  addresses.
- `(:BbotDNSName)-[:DNS_POINTS_TO]->(resource)` when the name is a hostname that
  a provider assigned to the resource, such as an EC2 instance's public DNS name
  or a load balancer's DNS name. Every DNS record target that Cartography links
  provider records to is covered, so a new target gets BBOT coverage too.
- `(:BbotOpenTCPPort)-[:EXPOSE]->(resource)` and `(:BbotURL)-[:EXPOSE]->(resource)`
  for the resource that serves the endpoint.
- `(:BbotFinding)-[:AFFECTS]->(resource)` and
  `(:BbotTechnology)-[:DETECTED_ON]->(resource)` for the resource that a finding
  or a detected technology belongs to.
- `(:BbotStorageBucket)-[:MATCHES_OBJECT_STORAGE]->(bucket)` for the
  `AWSS3Bucket` or `GCPBucket` with the same name. Azure buckets are not matched,
  because BBOT reports a guessed account and container name pair and container
  names repeat across accounts.

A BBOT host reaches a resource through its globally routable address, which a
`PublicIP` points to a compute instance or load balancer, or through its DNS
name. A DNS name also reaches the address or CNAME target it resolves to, and
the provider DNS record with the same name, in one hop. An endpoint's egress
address, the `PublicIP` to `Device` link, is not followed.
