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

#### Relationships

- ProxmoxACL grants ProxmoxRoles.

    ```
    (ProxmoxACL)-[GRANTS_ROLE]->(ProxmoxRole)
    ```

- ProxmoxACL applies to ProxmoxUsers.

    ```
    (ProxmoxACL)-[APPLIES_TO_USER]->(ProxmoxUser)
    ```

- ProxmoxACL applies to ProxmoxGroups.

    ```
    (ProxmoxACL)-[APPLIES_TO_GROUP]->(ProxmoxGroup)
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
