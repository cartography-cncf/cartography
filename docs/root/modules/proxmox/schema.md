## Proxmox Schema

### ProxmoxCluster

Representation of a Proxmox Virtual Environment cluster.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique cluster identifier (cluster name or derived from hostname) |
| name | Human-readable cluster name |
| version | Proxmox VE version string |
| quorate | Boolean indicating if the cluster has quorum |
| nodes_online | Number of nodes currently online in the cluster |
| migration | Migration mode setting (secure, insecure) |
| migration_network | CIDR network used for VM migrations |
| bwlimit | Bandwidth limit for migrations in KB/s |
| console | Default console viewer (html5, vv, xtermjs) |
| email_from | Default email sender address for notifications |
| http_proxy | HTTP proxy URL if configured |
| keyboard | Default keyboard layout |
| language | Default language setting |
| mac_prefix | MAC address prefix for VMs |
| max_workers | Maximum number of parallel migration workers |
| next_id_lower | Lower bound for auto-assigned VM IDs |
| next_id_upper | Upper bound for auto-assigned VM IDs |
| totem_interface | Corosync network interface |
| totem_cluster_name | Corosync cluster name |
| totem_config_version | Corosync configuration version |
| totem_ip_version | IP version used by Corosync (ipv4/ipv6) |
| totem_secauth | Corosync authentication mode |
| totem_version | Corosync protocol version |

#### Relationships

- ProxmoxCluster contains ProxmoxNodes.

    ```
    (ProxmoxNode)-[RESOURCE]->(ProxmoxCluster)
    ```

### ProxmoxNode

Representation of a physical or virtual node in a Proxmox cluster.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique node identifier (node name) |
| name | Node hostname |
| cluster_id | ID of the parent ProxmoxCluster |
| hostname | Node hostname |
| ip | Management IP address of the node |
| status | Current status (online, offline, unknown) |
| uptime | Node uptime in seconds |
| cpu_count | Total number of CPU cores |
| cpu_usage | CPU utilization as a float (0.0 to 1.0) |
| memory_total | Total RAM in bytes |
| memory_used | Used RAM in bytes |
| disk_total | Total disk space in bytes |
| disk_used | Used disk space in bytes |
| level | Node level in the cluster |

#### Relationships

- ProxmoxNode belongs to a ProxmoxCluster.

    ```
    (ProxmoxNode)-[RESOURCE]->(ProxmoxCluster)
    ```

- ProxmoxNode hosts ProxmoxVMs.

    ```
    (ProxmoxNode)-[HOSTS_VM]->(ProxmoxVM)
    ```

- ProxmoxStorage is available on ProxmoxNodes.

    ```
    (ProxmoxStorage)-[AVAILABLE_ON]->(ProxmoxNode)
    ```

- ProxmoxNode has ProxmoxNodeNetworkInterfaces.

    ```
    (ProxmoxNode)-[HAS_NETWORK_INTERFACE]->(ProxmoxNodeNetworkInterface)
    ```

### ProxmoxNodeNetworkInterface

Representation of a physical or virtual network interface on a Proxmox node.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the network interface |
| name | Interface name (e.g., vmbr0, eth0) |
| node_name | Name of the node this interface belongs to |
| type | Interface type (bridge, bond, eth, vlan, etc.) |
| address | IPv4 address |
| netmask | IPv4 subnet mask |
| gateway | IPv4 default gateway |
| address6 | IPv6 address |
| netmask6 | IPv6 subnet mask |
| gateway6 | IPv6 default gateway |
| bridge_ports | Bridge member ports |
| bond_slaves | Bond slave interfaces |
| active | Boolean indicating if interface is active |
| autostart | Boolean indicating if interface auto-starts on boot |
| mtu | MTU size |

#### Relationships

- ProxmoxNodeNetworkInterface belongs to a ProxmoxNode.

    ```
    (ProxmoxNode)-[HAS_NETWORK_INTERFACE]->(ProxmoxNodeNetworkInterface)
    ```

- ProxmoxNodeNetworkInterface belongs to a ProxmoxCluster.

    ```
    (ProxmoxNodeNetworkInterface)-[RESOURCE]->(ProxmoxCluster)
    ```

### ProxmoxVM

Representation of a QEMU virtual machine or LXC container.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier in format "node/type/vmid" (e.g., "node1/qemu/100") |
| vmid | Numeric VM/container ID |
| name | VM or container name |
| node | Name of the host node |
| cluster_id | ID of the parent ProxmoxCluster |
| type | Type of guest ("qemu" for VMs, "lxc" for containers) |
| status | Current status (running, stopped, paused) |
| template | Boolean indicating if this is a template |
| cpu_cores | Number of CPU cores allocated |
| cpu_sockets | Number of CPU sockets (QEMU only) |
| memory | Allocated RAM in bytes |
| disk_size | Total disk size in bytes |
| uptime | Uptime in seconds |
| tags | Array of tags assigned to the VM |

#### Relationships

- ProxmoxVM is hosted by a ProxmoxNode.

    ```
    (ProxmoxNode)-[HOSTS_VM]->(ProxmoxVM)
    ```

- ProxmoxVM has ProxmoxDisks.

    ```
    (ProxmoxVM)-[HAS_DISK]->(ProxmoxDisk)
    ```

- ProxmoxVM has ProxmoxNetworkInterfaces.

    ```
    (ProxmoxVM)-[HAS_NETWORK_INTERFACE]->(ProxmoxNetworkInterface)
    ```

### ProxmoxDisk

Representation of a virtual disk attached to a VM or container.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier in format "node/type/vmid:disk_id" (e.g., "node1/qemu/100:scsi0") |
| disk_id | Disk identifier (e.g., "scsi0", "virtio0", "sata0", "ide0", "efidisk0", "tpmstate0", "rootfs") |
| vmid | ID of the parent VM/container |
| storage | Storage backend ID where the disk is stored |
| size | Disk size in bytes |
| backup | Boolean indicating if disk is included in backups |
| cache | Cache mode (e.g., "writeback", "none") |

#### Relationships

- ProxmoxDisk belongs to a ProxmoxVM.

    ```
    (ProxmoxVM)-[HAS_DISK]->(ProxmoxDisk)
    ```

- ProxmoxDisk is stored on ProxmoxStorage.

    ```
    (ProxmoxDisk)-[STORED_ON]->(ProxmoxStorage)
    ```

### ProxmoxNetworkInterface

Representation of a network interface attached to a VM or container.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier in format "node/type/vmid:net_id" (e.g., "node1/qemu/100:net0") |
| net_id | Network interface identifier (e.g., "net0", "net1") |
| vmid | ID of the parent VM/container |
| bridge | Bridge name the interface is connected to |
| mac_address | MAC address of the interface |
| model | Network adapter model (e.g., "virtio", "e1000", "rtl8139", "vmxnet3", "veth") |
| firewall | Boolean indicating if Proxmox firewall is enabled |
| vlan_tag | VLAN tag if configured |
| ip | IPv4 address assigned to the interface |
| ip6 | IPv6 address assigned to the interface |
| gw | IPv4 gateway |
| gw6 | IPv6 gateway |
| mtu | MTU size |
| rate | Bandwidth rate limit (in MB/s) |
| link_up | Boolean indicating if the link is up |

#### Relationships

- ProxmoxNetworkInterface belongs to a ProxmoxVM.

    ```
    (ProxmoxVM)-[HAS_NETWORK_INTERFACE]->(ProxmoxNetworkInterface)
    ```

### ProxmoxStorage

Representation of a storage backend in Proxmox.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique storage identifier |
| name | Storage backend name |
| cluster_id | ID of the parent ProxmoxCluster |
| type | Storage type (dir, nfs, lvm, lvmthin, ceph, etc.) |
| content_types | Array of allowed content types (images, iso, backup, etc.) |
| shared | Boolean indicating if storage is shared across nodes |
| enabled | Boolean indicating if storage is enabled |
| total | Total storage capacity in bytes |
| used | Used storage space in bytes |
| available | Available storage space in bytes |

#### Relationships

- ProxmoxStorage is available on ProxmoxNodes.

    ```
    (ProxmoxStorage)-[AVAILABLE_ON]->(ProxmoxNode)
    ```

- ProxmoxDisks are stored on ProxmoxStorage.

    ```
    (ProxmoxDisk)-[STORED_ON]->(ProxmoxStorage)
    ```

### ProxmoxPool

Representation of a resource pool for organizing VMs, containers, and storage.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique pool identifier |
| poolid | Pool name |
| cluster_id | ID of the parent ProxmoxCluster |
| comment | Description or notes about the pool |

#### Relationships

- ProxmoxPool contains ProxmoxVMs.

    ```
    (ProxmoxPool)-[CONTAINS_VM]->(ProxmoxVM)
    ```

- ProxmoxPool contains ProxmoxStorage.

    ```
    (ProxmoxPool)-[CONTAINS_STORAGE]->(ProxmoxStorage)
    ```

### ProxmoxBackupJob

Representation of a scheduled backup job configuration.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique job identifier |
| job_id | Backup job name/ID |
| cluster_id | ID of the parent ProxmoxCluster |
| schedule | Cron-style schedule string (e.g., "0 2 * * *") |
| storage | Target storage backend ID for backups |
| enabled | Boolean indicating if the job is enabled |
| mode | Backup mode (snapshot, suspend, stop) |
| compression | Compression algorithm (zstd, gzip, lzo, none) |
| mailnotification | Email notification setting (always, failure, never) |
| mailto | Email address for notifications |
| notes | Job description or notes |
| prune_keep_last | Number of most recent backups to keep |
| prune_keep_hourly | Number of hourly backups to keep |
| prune_keep_daily | Number of daily backups to keep |
| prune_keep_weekly | Number of weekly backups to keep |
| prune_keep_monthly | Number of monthly backups to keep |
| prune_keep_yearly | Number of yearly backups to keep |
| repeat_missed | Boolean indicating if missed backups should be repeated |

#### Relationships

- ProxmoxBackupJob backs up ProxmoxVMs.

    ```
    (ProxmoxBackupJob)-[BACKS_UP]->(ProxmoxVM)
    ```

- ProxmoxBackupJob targets ProxmoxStorage.

    ```
    (ProxmoxBackupJob)-[BACKS_UP_TO]->(ProxmoxStorage)
    ```

### ProxmoxHAGroup

Representation of a High Availability group defining node preferences.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique group identifier |
| group | HA group name |
| cluster_id | ID of the parent ProxmoxCluster |
| nodes | Comma-separated list of preferred nodes |
| restricted | Boolean indicating if VMs are restricted to listed nodes |
| nofailback | Boolean indicating if automatic failback is disabled |
| comment | Description or notes about the HA group |

#### Relationships

- ProxmoxHAResource is a member of ProxmoxHAGroup.

    ```
    (ProxmoxHAResource)-[MEMBER_OF_HA_GROUP]->(ProxmoxHAGroup)
    ```

### ProxmoxHAResource

Representation of a VM or container configured for High Availability.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique resource identifier (format: "vm:100" or "ct:200") |
| sid | Service ID (same as id) |
| cluster_id | ID of the parent ProxmoxCluster |
| state | Current HA state (started, stopped, disabled, etc.) |
| group | Associated HA group name |
| max_restart | Maximum number of restart attempts |
| max_relocate | Maximum number of relocation attempts |
| comment | Description or notes about the HA resource |

#### Relationships

- ProxmoxHAResource protects ProxmoxVMs.

    ```
    (ProxmoxHAResource)-[PROTECTS]->(ProxmoxVM)
    ```

- ProxmoxHAResource is a member of ProxmoxHAGroup.

    ```
    (ProxmoxHAResource)-[MEMBER_OF_HA_GROUP]->(ProxmoxHAGroup)
    ```

## Common Queries

### Find all running VMs

```cypher
MATCH (v:ProxmoxVM)
WHERE v.status = 'running' AND v.template = false
RETURN v.name, v.node, v.memory, v.cpu_cores
ORDER BY v.memory DESC
```

### Find VMs with internet-facing interfaces

```cypher
MATCH (v:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(i:ProxmoxNetworkInterface)
WHERE i.bridge = 'vmbr0' AND v.status = 'running'
RETURN v.name, v.node, i.mac_address, i.bridge
```

### Find nodes with high resource usage

```cypher
MATCH (n:ProxmoxNode)
WHERE n.cpu_usage > 0.8 OR (n.memory_used * 1.0 / n.memory_total) > 0.9
RETURN n.name, n.cpu_usage,
       (n.memory_used * 100.0 / n.memory_total) as memory_percent,
       n.status
ORDER BY n.cpu_usage DESC
```

### Find VMs by tag

```cypher
MATCH (v:ProxmoxVM)
WHERE 'production' IN v.tags
RETURN v.name, v.node, v.status, v.tags
```

### Find storage backends and their usage

```cypher
MATCH (s:ProxmoxStorage)
WHERE s.total > 0
RETURN s.name, s.type,
       (s.used * 100.0 / s.total) as usage_percent,
       s.shared
ORDER BY usage_percent DESC
```

### Map VM disk locations

```cypher
MATCH (v:ProxmoxVM)-[:HAS_DISK]->(d:ProxmoxDisk)-[:STORED_ON]->(s:ProxmoxStorage)
RETURN v.name, d.disk_id, d.size, s.name as storage, s.type
ORDER BY v.name, d.disk_id
```

### Find VMs without backup protection

```cypher
MATCH (v:ProxmoxVM)
WHERE v.template = false
  AND NOT EXISTS {
    MATCH (v)-[:HAS_DISK]->(d:ProxmoxDisk)
    WHERE d.backup = true
  }
RETURN v.name, v.node, v.cluster_id
```

### Cluster topology overview

```cypher
MATCH (n:ProxmoxNode)-[:RESOURCE]->(c:ProxmoxCluster)
OPTIONAL MATCH (n)-[:HOSTS_VM]->(v:ProxmoxVM)
WHERE v.template = false
RETURN c.name as cluster,
       n.name as node,
       count(v) as vm_count,
       n.status
ORDER BY c.name, n.name
```

### Find VMs in a specific pool

```cypher
MATCH (pool:ProxmoxPool {poolid: 'production'})-[:CONTAINS_VM]->(vm:ProxmoxVM)
RETURN vm.name, vm.status, vm.node, vm.memory
ORDER BY vm.memory DESC
```

### Find all backup jobs for a VM

```cypher
MATCH (vm:ProxmoxVM {name: 'my-critical-vm'})<-[:BACKS_UP]-(job:ProxmoxBackupJob)
WHERE job.enabled = true
RETURN job.id, job.schedule, job.mode, job.storage
ORDER BY job.schedule
```

### Find VMs not covered by any backup job

```cypher
MATCH (vm:ProxmoxVM)
WHERE vm.template = false
  AND vm.status = 'running'
  AND NOT EXISTS {
    MATCH (vm)<-[:BACKS_UP]-(:ProxmoxBackupJob {enabled: true})
  }
RETURN vm.name, vm.node, vm.memory, vm.tags
ORDER BY vm.memory DESC
```

### Find VMs protected by HA

```cypher
MATCH (vm:ProxmoxVM)<-[:PROTECTS]-(ha:ProxmoxHAResource)-[:MEMBER_OF_HA_GROUP]->(group:ProxmoxHAGroup)
RETURN vm.name, vm.status, ha.state, group.group, group.nodes
ORDER BY vm.name
```

### Find production VMs without HA protection

```cypher
MATCH (vm:ProxmoxVM)
WHERE vm.template = false
  AND vm.status = 'running'
  AND 'production' IN vm.tags
  AND NOT EXISTS {
    MATCH (vm)<-[:PROTECTS]-(:ProxmoxHAResource)
  }
RETURN vm.name, vm.node, vm.memory, vm.cpu_cores
ORDER BY vm.memory DESC
```

### Backup coverage report by pool

```cypher
MATCH (pool:ProxmoxPool)-[:CONTAINS_VM]->(vm:ProxmoxVM)
WHERE vm.template = false
OPTIONAL MATCH (vm)<-[:BACKS_UP]-(job:ProxmoxBackupJob)
WHERE job.enabled = true
RETURN pool.poolid,
       count(vm) as total_vms,
       count(job) as backed_up_vms,
       collect(DISTINCT vm.name) as vms_without_backup
ORDER BY pool.poolid
```

### HA failover risk assessment

```cypher
MATCH (group:ProxmoxHAGroup)
MATCH (ha:ProxmoxHAResource)-[:MEMBER_OF_HA_GROUP]->(group)
MATCH (ha)-[:PROTECTS]->(vm:ProxmoxVM)
RETURN group.group,
       group.nodes,
       group.restricted,
       count(vm) as protected_vms,
       collect(vm.name) as vm_names
ORDER BY protected_vms DESC
```

### ProxmoxUser

Representation of a user account in Proxmox VE.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | User identifier (format: user@realm) |
| userid | Full user ID |
| cluster_id | ID of the parent ProxmoxCluster |
| enable | Boolean indicating if account is enabled |
| expire | Account expiration timestamp (0 = never expires) |
| firstname | User's first name |
| lastname | User's last name |
| email | User's email address |
| comment | User description or notes |
| groups | Array of group memberships |
| tokens | Array of API tokens |

#### Relationships

- ProxmoxUser is a member of ProxmoxGroups.

    ```
    (ProxmoxUser)-[MEMBER_OF_GROUP]->(ProxmoxGroup)
    ```

- ProxmoxACL grants permissions to ProxmoxUsers.

    ```
    (ProxmoxACL)-[APPLIES_TO_USER]->(ProxmoxUser)
    ```

### ProxmoxGroup

Representation of a user group in Proxmox VE.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Group identifier |
| groupid | Group name |
| cluster_id | ID of the parent ProxmoxCluster |
| comment | Group description or notes |

#### Relationships

- ProxmoxACL grants permissions to ProxmoxGroups.

    ```
    (ProxmoxACL)-[APPLIES_TO_GROUP]->(ProxmoxGroup)
    ```

### ProxmoxRole

Representation of a permission role in Proxmox VE.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Role identifier |
| roleid | Role name |
| cluster_id | ID of the parent ProxmoxCluster |
| privs | Array of privileges (e.g., VM.Audit, Sys.Modify) |
| special | Boolean indicating if this is a built-in role |

#### Relationships

- ProxmoxACL grants ProxmoxRoles.

    ```
    (ProxmoxACL)-[GRANTS_ROLE]->(ProxmoxRole)
    ```

### ProxmoxACL

Representation of an Access Control List entry in Proxmox VE.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | ACL entry identifier |
| path | Resource path (e.g., /, /vms/100, /storage/local) |
| cluster_id | ID of the parent ProxmoxCluster |
| roleid | Role granted by this ACL |
| ugid | User or group ID this ACL applies to |
| propagate | Boolean indicating if permissions propagate to children |
| principal_type | Type of principal (user or group) |
| resource_type | Type of resource (cluster, vm, storage, pool, node, access) |
| resource_id | ID of specific resource if applicable |

#### Relationships

- ProxmoxACL grants ProxmoxRoles.

    ```
    (ProxmoxACL)-[GRANTS_ROLE {propagate, path}]->(ProxmoxRole)
    ```

- ProxmoxACL applies to ProxmoxUsers.

    ```
    (ProxmoxACL)-[APPLIES_TO_USER {path, propagate, resource_type}]->(ProxmoxUser)
    ```

- ProxmoxACL applies to ProxmoxGroups.

    ```
    (ProxmoxACL)-[APPLIES_TO_GROUP {path, propagate, resource_type}]->(ProxmoxGroup)
    ```

- ProxmoxACL grants access to resources.

    ```
    (ProxmoxACL)-[GRANTS_ACCESS_TO {propagate, path}]->(ProxmoxVM|ProxmoxStorage|ProxmoxPool|ProxmoxNode|ProxmoxCluster)
    ```

- Effective permissions (derived relationships for easy querying).

    ```
    (ProxmoxUser|ProxmoxGroup)-[HAS_PERMISSION {via_acl, role, privileges, path, propagate, via_group?}]->(Resource)
    ```

### ProxmoxFirewallRule

Representation of a firewall rule at cluster, node, or VM level.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Firewall rule identifier |
| cluster_id | ID of the parent ProxmoxCluster |
| scope | Rule scope (cluster, node, vm) |
| scope_id | Scope identifier (node name or vmid) |
| pos | Position in the rule list |
| type | Rule type (in, out, group) |
| action | Action to take (ACCEPT, DROP, REJECT) |
| enable | Boolean indicating if rule is enabled |
| iface | Network interface the rule applies to |
| source | Source address or network (CIDR) |
| dest | Destination address or network (CIDR) |
| proto | Protocol (tcp, udp, icmp, etc.) |
| sport | Source port(s) |
| dport | Destination port(s) |
| comment | Rule description or notes |
| macro | Predefined macro name |
| log | Log level for matched traffic |

#### Relationships

- ProxmoxFirewallRule applies to ProxmoxNodes.

    ```
    (ProxmoxFirewallRule)-[APPLIES_TO_NODE]->(ProxmoxNode)
    ```

- ProxmoxFirewallRule applies to ProxmoxVMs.

    ```
    (ProxmoxFirewallRule)-[APPLIES_TO_VM]->(ProxmoxVM)
    ```

### ProxmoxFirewallIPSet

Representation of an IP set (address group) for firewall rules.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | IP set identifier |
| name | IP set name |
| cluster_id | ID of the parent ProxmoxCluster |
| scope | IP set scope (cluster, node, vm) |
| scope_id | Scope identifier (node name or vmid) |
| comment | IP set description or notes |
| cidrs | Array of CIDR entries in this IP set |

### ProxmoxCertificate

Representation of an SSL/TLS certificate used by a Proxmox node.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Certificate identifier |
| cluster_id | ID of the parent ProxmoxCluster |
| node_name | Node using this certificate |
| filename | Certificate filename |
| fingerprint | Certificate fingerprint (hash) |
| issuer | Certificate issuer DN |
| subject | Certificate subject DN |
| san | Array of Subject Alternative Names |
| notbefore | Certificate valid from timestamp |
| notafter | Certificate valid until timestamp |
| public_key_type | Public key algorithm (RSA, EC, etc.) |
| public_key_bits | Public key size in bits |
| pem | PEM-encoded certificate |

#### Relationships

- ProxmoxNode uses ProxmoxCertificates.

    ```
    (ProxmoxNode)-[HAS_CERTIFICATE]->(ProxmoxCertificate)
    ```

## Security and Compliance Queries

### Find users with root-level access

```cypher
MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
MATCH (acl)-[:GRANTS_ROLE]->(r:ProxmoxRole)
WHERE acl.path = '/' AND r.roleid = 'Administrator'
RETURN u.userid, u.email, u.enable, r.roleid
ORDER BY u.userid
```

### Find disabled users with active permissions

```cypher
MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
WHERE u.enable = false
RETURN u.userid, u.email, count(acl) as permission_count
ORDER BY permission_count DESC
```

### Find firewall rules with unrestricted access

```cypher
MATCH (rule:ProxmoxFirewallRule)
WHERE rule.action = 'ACCEPT'
AND rule.enable = true
AND (rule.source IS NULL OR rule.source = '0.0.0.0/0')
RETURN rule.scope, rule.scope_id, rule.pos, rule.proto, rule.dport, rule.comment
ORDER BY rule.scope, rule.pos
```

### Certificate expiration audit

```cypher
MATCH (n:ProxmoxNode)-[:HAS_CERTIFICATE]->(cert:ProxmoxCertificate)
WITH n, cert,
     (cert.notafter - timestamp()) / (24 * 60 * 60 * 1000) as days_until_expiry
RETURN n.name, cert.subject,
       CASE
         WHEN days_until_expiry < 0 THEN 'EXPIRED'
         WHEN days_until_expiry < 30 THEN 'CRITICAL'
         WHEN days_until_expiry < 90 THEN 'WARNING'
         ELSE 'OK'
       END as status,
       days_until_expiry
ORDER BY days_until_expiry
```

### Privilege escalation risk: Users with VM modification rights

```cypher
MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
MATCH (acl)-[:GRANTS_ROLE]->(r:ProxmoxRole)
WHERE 'VM.Config' IN r.privs OR 'VM.Allocate' IN r.privs
RETURN u.userid, u.email, r.roleid, acl.path, r.privs
ORDER BY u.userid
```

## RBAC and Permission Queries

The Proxmox module includes comprehensive RBAC (Role-Based Access Control) support with rich relationship metadata. These queries help you understand and audit user permissions.

### Understanding Permission Propagation

Proxmox ACLs can propagate to child resources. For example, a permission on `/pool/production` can propagate to all VMs in that pool.

```cypher
// Find ACLs with propagation enabled
MATCH (acl:ProxmoxACL)-[r:GRANTS_ACCESS_TO]->(resource)
WHERE acl.propagate = true
RETURN acl.path, acl.ugid, resource, r.propagate
```

### What can a specific user access?

```cypher
// Direct permissions via ACLs
MATCH (u:ProxmoxUser {userid: 'admin@pam'})-[p:HAS_PERMISSION]->(resource)
RETURN resource, p.role, p.privileges, p.path, p.via_group
ORDER BY labels(resource)[0], resource.name
```

### Who can access a specific VM?

```cypher
// Find all users and groups with permissions to a VM
MATCH (vm:ProxmoxVM {vmid: 100})
MATCH (principal)-[p:HAS_PERMISSION]->(vm)
WHERE principal:ProxmoxUser OR principal:ProxmoxGroup
RETURN principal.userid, principal.groupid, p.role, p.privileges, p.path
ORDER BY principal.userid, principal.groupid
```

### Find users with administrative privileges

```cypher
// Users with Administrator role
MATCH (u:ProxmoxUser)-[:HAS_PERMISSION {role: 'Administrator'}]->(resource)
RETURN DISTINCT u.userid, u.email, u.enable,
       collect(DISTINCT labels(resource)[0]) as resource_types
ORDER BY u.userid
```

### Audit group membership and inherited permissions

```cypher
// Find users, their groups, and what the groups can access
MATCH (u:ProxmoxUser)-[:MEMBER_OF_GROUP]->(g:ProxmoxGroup)
OPTIONAL MATCH (g)-[p:HAS_PERMISSION]->(resource)
RETURN u.userid, g.groupid,
       collect(DISTINCT {
         resource: coalesce(resource.name, resource.id),
         role: p.role,
         path: p.path
       }) as group_permissions
ORDER BY u.userid
```

### Find over-privileged accounts

```cypher
// Users with cluster-wide admin rights
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(c:ProxmoxCluster)
MATCH (u)<-[:APPLIES_TO_USER]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(r:ProxmoxRole)
WHERE acl.path = '/' AND r.roleid IN ['Administrator', 'PVEAdmin']
RETURN u.userid, u.email, u.enable, u.expire,
       CASE WHEN u.expire > 0 THEN datetime({epochSeconds: u.expire}) ELSE 'Never' END as expires_at,
       collect(DISTINCT r.roleid) as roles
ORDER BY u.expire DESC
```

### Find resources without specific ACL protection

```cypher
// VMs that don't have specific ACL entries (rely on parent path permissions)
MATCH (vm:ProxmoxVM)
WHERE NOT EXISTS {
  MATCH (:ProxmoxACL {resource_type: 'vm', resource_id: toString(vm.vmid)})
}
RETURN vm.name, vm.vmid, vm.node, vm.tags
ORDER BY vm.name
```

### Permission coverage by resource type

```cypher
// Show ACL coverage across different resource types
MATCH (acl:ProxmoxACL)
RETURN acl.resource_type,
       count(*) as acl_count,
       count(DISTINCT acl.ugid) as unique_principals,
       collect(DISTINCT acl.roleid) as roles_granted
ORDER BY acl_count DESC
```

### Find accounts with specific privileges

```cypher
// Users who can create/modify VMs
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(resource)
WHERE ANY(priv IN p.privileges WHERE priv IN ['VM.Allocate', 'VM.Config.Disk', 'VM.Config.CPU'])
RETURN DISTINCT u.userid, u.email,
       collect(DISTINCT {resource: coalesce(resource.name, resource.id), privileges: p.privileges}) as access
ORDER BY u.userid
```

### Audit trail: Map ACL to effective permissions

```cypher
// Full permission chain from ACL to user to resource
MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
MATCH (acl)-[:GRANTS_ROLE]->(r:ProxmoxRole)
MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
RETURN u.userid,
       acl.path,
       r.roleid,
       r.privs,
       labels(resource)[0] as resource_type,
       coalesce(resource.name, resource.id) as resource_name,
       acl.propagate
ORDER BY u.userid, acl.path
```

### Group-based permission analysis

```cypher
// Analyze what each group can access
MATCH (g:ProxmoxGroup)
OPTIONAL MATCH (g)<-[:MEMBER_OF_GROUP]-(u:ProxmoxUser)
OPTIONAL MATCH (g)-[p:HAS_PERMISSION]->(resource)
RETURN g.groupid,
       count(DISTINCT u) as member_count,
       collect(DISTINCT u.userid) as members,
       count(DISTINCT resource) as resource_count,
       collect(DISTINCT {
         resource_type: labels(resource)[0],
         resource_name: coalesce(resource.name, resource.id),
         role: p.role
       })[0..5] as sample_permissions
ORDER BY member_count DESC
```

### Find permissions on specific storage

```cypher
// Who can access a specific storage backend
MATCH (storage:ProxmoxStorage {name: 'local-lvm'})
MATCH (principal)-[p:HAS_PERMISSION]->(storage)
WHERE principal:ProxmoxUser OR principal:ProxmoxGroup
RETURN principal.userid, principal.groupid, p.role, p.privileges, p.via_group
ORDER BY principal.userid, principal.groupid
```

### Permission inheritance through pools

```cypher
// Find permissions on pools and what VMs are affected
MATCH (pool:ProxmoxPool)-[:CONTAINS_VM]->(vm:ProxmoxVM)
MATCH (principal)-[p:HAS_PERMISSION]->(pool)
WHERE principal:ProxmoxUser OR principal:ProxmoxGroup
RETURN pool.poolid,
       count(DISTINCT vm) as vm_count,
       principal.userid, principal.groupid,
       p.role, p.privileges,
       collect(DISTINCT vm.name)[0..3] as sample_vms
ORDER BY pool.poolid, principal.userid
```

### Security audit: Accounts with backup restore capability

```cypher
// Users who can restore backups (potential data access risk)
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(resource)
WHERE ANY(priv IN p.privileges WHERE priv IN ['VM.Backup', 'Datastore.Allocate'])
RETURN u.userid, u.email, u.enable,
       collect(DISTINCT {
         resource: coalesce(resource.name, resource.id),
         role: p.role,
         privileges: p.privileges
       }) as access_details
ORDER BY u.userid
```

### Find dormant accounts with active permissions

```cypher
// Users who are disabled but still have ACL entries
MATCH (u:ProxmoxUser)
WHERE u.enable = false
OPTIONAL MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u)
OPTIONAL MATCH (acl)-[:GRANTS_ROLE]->(r:ProxmoxRole)
OPTIONAL MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
WITH u, collect(DISTINCT {acl: acl.id, role: r.roleid, resource: resource}) as permissions
WHERE size(permissions) > 0 AND permissions[0].acl IS NOT NULL
RETURN u.userid, u.email,
       CASE WHEN u.expire > 0 THEN datetime({epochSeconds: u.expire}) ELSE 'Never' END as expired_at,
       size(permissions) as permission_count,
       permissions
ORDER BY permission_count DESC
```

### Compare permissions between users

```cypher
// Compare what two users can access
MATCH (u1:ProxmoxUser {userid: 'user1@pam'})-[:HAS_PERMISSION]->(r1)
MATCH (u2:ProxmoxUser {userid: 'user2@pam'})-[:HAS_PERMISSION]->(r2)
WHERE id(r1) = id(r2)  // Same resource
RETURN r1, labels(r1)[0] as resource_type, coalesce(r1.name, r1.id) as resource_name
ORDER BY resource_type, resource_name
```
