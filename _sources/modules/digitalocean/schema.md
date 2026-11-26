<!-- Generated from the data model. Do not edit manually. -->

## Digitalocean Schema

```mermaid
graph LR
    DOAccount -- RESOURCE --> DOFirewall
    DOAccount -- RESOURCE --> DOFirewallRule
    DOAccount -- RESOURCE --> DOIpRange
    DOAccount -- RESOURCE --> DOProject
    DODroplet -- RESOURCE --> DOProject
    DOFirewall -- PROTECTS --> DODroplet
    DOFirewallRule -- HAS_DESTINATION --> DODroplet
    DOFirewallRule -- HAS_DESTINATION --> DOIpRange
    DOFirewallRule -- HAS_SOURCE --> DODroplet
    DOFirewallRule -- HAS_SOURCE --> DOIpRange
    DOFirewallRule -- MEMBER_OF_DO_FIREWALL --> DOFirewall
    DOProject -- RESOURCE --> DOAccount
    DOProject -- RESOURCE --> DODroplet
```

### DOAccount

A DigitalOcean account.

> **Ontology Mapping**: This node uses the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | DigitalOcean account UUID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| droplet_limit |  | Maximum number of Droplets allowed. |
| floating_ip_limit |  | Maximum number of floating IPs allowed. |
| status |  | Account status. |
| uuid |  | DigitalOcean account UUID. |
| *_ont_name* | Yes | Normalized field sourced from `uuid`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |

#### Relationships

- `(:DOAccount)-[:RESOURCE]->(:DOFirewall)`: A DigitalOcean account contains the firewall as a resource.

- `(:DOAccount)-[:RESOURCE]->(:DOFirewallRule)`: A DigitalOcean account contains the firewall rule as a resource.

- `(:DOAccount)-[:RESOURCE]->(:DOIpRange)`: A DigitalOcean account contains the IP range selector as a resource.

- `(:DOProject)-[:RESOURCE]->(:DOAccount)`: Deprecated compatibility edge linking a project to its account.

- `(:DOAccount)-[:RESOURCE]->(:DOProject)`: The account contains the project.

### DODroplet

A compute instance in a DigitalOcean project.

> **Ontology Mapping**: This node uses the ontology label [`ComputeInstance`](#ontology-computeinstance).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | DigitalOcean Droplet ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| account_id |  | ID of the owning account. |
| created_at |  | Droplet creation timestamp. |
| image |  | Base image slug. |
| ip_address |  | Public IPv4 address. |
| ip_v6_address |  | Public IPv6 address. |
| kernel |  | Current kernel information. |
| locked |  | Whether user actions are blocked. |
| name |  | Droplet name. |
| private_ip_address |  | Private IPv4 address. |
| project_id |  | ID of the containing project. |
| region |  | DigitalOcean region slug. |
| size |  | Droplet size slug. |
| status |  | Droplet lifecycle status. |
| tags |  | Tags assigned to the Droplet. |
| volumes |  | Attached block-storage volume IDs. |
| vpc_uuid |  | UUID of the Droplet's VPC. |
| *_ont_created_at* | Yes | Normalized field sourced from `created_at`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_private_ip_address* | Yes | Normalized field sourced from `private_ip_address`. |
| *_ont_public_ip_address* | Yes | Normalized field sourced from `ip_address`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized field sourced from `status`. |
| *_ont_type* | Yes | Normalized field sourced from `size`. |

#### Relationships

- `(:DOFirewallRule)-[:HAS_DESTINATION]->(:DODroplet)`: An outbound rule selects one or more Droplets as traffic destinations.

- `(:DOFirewallRule)-[:HAS_SOURCE]->(:DODroplet)`: An inbound rule selects one or more Droplets as traffic sources.

- `(:PublicIP)-[:POINTS_TO]->(:DODroplet)`

- `(:DOFirewall)-[:PROTECTS]->(:DODroplet)`: A DigitalOcean firewall protects one or more Droplets.

- `(:DOProject)-[:RESOURCE]->(:DODroplet)`: The project contains the Droplet.

- `(:DODroplet)-[:RESOURCE]->(:DOProject)`: Deprecated compatibility edge linking a Droplet to its project.

### DOFirewall

A DigitalOcean Cloud Firewall that controls Droplet network access.

> **Ontology Mapping**: This node uses the ontology label [`NetworkAccessControl`](#ontology-networkaccesscontrol).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | DigitalOcean firewall UUID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| created_at |  | ISO 8601 timestamp when the firewall was created. |
| droplet_ids |  | IDs of Droplets protected by this firewall. |
| name |  | Firewall name. |
| status |  | Firewall operation status. |
| tags |  | Tags assigned to the firewall. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:DOFirewallRule)-[:MEMBER_OF_DO_FIREWALL]->(:DOFirewall)`: A firewall rule belongs to a DigitalOcean firewall.

- `(:DOFirewall)-[:PROTECTS]->(:DODroplet)`: A DigitalOcean firewall protects one or more Droplets.

- `(:DOAccount)-[:RESOURCE]->(:DOFirewall)`: A DigitalOcean account contains the firewall as a resource.

### DOFirewallRule

A directional traffic rule configured on a DigitalOcean Cloud Firewall.

> **Additional Labels**: This node also uses `IpRule`.

> **Additional Label Definitions**:
>
> - `IpRule`: A node participating in the shared IpRule graph interface.

> **Conditional Labels**:
>
> - `IpPermissionEgress` when `action` equals `allow` and `direction` equals `outbound`. A node participating in the shared IpPermissionEgress graph interface.
> - `IpPermissionInbound` when `action` equals `allow` and `direction` equals `inbound`. A node participating in the shared IpPermissionInbound graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable, deterministic identifier for the firewall rule. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| action |  | Firewall action applied when the rule matches. |
| canonical_name |  | Canonical name for the firewall rule, derived from its properties. |
| destination_kubernetes_ids |  | Kubernetes-cluster IDs selected by an outbound rule. |
| destination_load_balancer_uids |  | Load-balancer UUIDs selected by an outbound rule. |
| destination_tags |  | DigitalOcean tags selected by an outbound rule. |
| direction |  | Traffic direction: inbound or outbound. |
| firewall_id | Yes | UUID of the firewall containing this rule. |
| fromport |  | Lowest transport-layer port matched by the rule. |
| ports |  | Port or inclusive port range matched by the rule. |
| protocol |  | Network protocol matched by the rule. |
| source_kubernetes_ids |  | Kubernetes-cluster IDs selected by an inbound rule. |
| source_load_balancer_uids |  | Load-balancer UUIDs selected by an inbound rule. |
| source_tags |  | DigitalOcean tags selected by an inbound rule. |
| toport |  | Highest transport-layer port matched by the rule. |

#### Relationships

- `(:DOFirewallRule)-[:HAS_DESTINATION]->(:DODroplet)`: An outbound rule selects one or more Droplets as traffic destinations.

- `(:DOFirewallRule)-[:HAS_DESTINATION]->(:DOIpRange)`: An outbound rule selects one or more IP ranges as traffic destinations.

- `(:DOFirewallRule)-[:HAS_SOURCE]->(:DODroplet)`: An inbound rule selects one or more Droplets as traffic sources.

- `(:DOFirewallRule)-[:HAS_SOURCE]->(:DOIpRange)`: An inbound rule selects one or more IP ranges as traffic sources.

- `(:DOFirewallRule)-[:MEMBER_OF_DO_FIREWALL]->(:DOFirewall)`: A firewall rule belongs to a DigitalOcean firewall.

- `(:DOAccount)-[:RESOURCE]->(:DOFirewallRule)`: A DigitalOcean account contains the firewall rule as a resource.

### DOIpRange

An IP address or CIDR selector used by a DigitalOcean firewall rule.

> **Additional Labels**: This node also uses `IpRange`.

> **Additional Label Definitions**:
>
> - `IpRange`: A node participating in the shared IpRange graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | IP address or CIDR used as the identifier for this selector. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| range | Yes | IP address or CIDR selected by a DigitalOcean firewall rule. |

#### Relationships

- `(:DOFirewallRule)-[:HAS_DESTINATION]->(:DOIpRange)`: An outbound rule selects one or more IP ranges as traffic destinations.

- `(:DOFirewallRule)-[:HAS_SOURCE]->(:DOIpRange)`: An inbound rule selects one or more IP ranges as traffic sources.

- `(:DOAccount)-[:RESOURCE]->(:DOIpRange)`: A DigitalOcean account contains the IP range selector as a resource.

### DOProject

A project in a DigitalOcean account.

> **Ontology Mapping**: This node uses the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | DigitalOcean project UUID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| account_id |  | ID of the account that owns the project. |
| created_at |  | Project creation timestamp. |
| description |  | Project description. |
| environment |  | Environment classification of project resources. |
| is_default |  | Whether unspecified resources default to this project. |
| name |  | Project name. |
| owner_uuid |  | UUID of the project owner. |
| updated_at |  | Project update timestamp. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:DOAccount)-[:RESOURCE]->(:DOProject)`: The account contains the project.

- `(:DOProject)-[:RESOURCE]->(:DOAccount)`: Deprecated compatibility edge linking a project to its account.

- `(:DODroplet)-[:RESOURCE]->(:DOProject)`: Deprecated compatibility edge linking a Droplet to its project.

- `(:DOProject)-[:RESOURCE]->(:DODroplet)`: The project contains the Droplet.
