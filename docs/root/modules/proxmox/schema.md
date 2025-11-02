## Proxmox Schema

### ProxmoxCluster

Representation of a Proxmox Virtual Environment cluster.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique cluster identifier (cluster name or derived from hostname) |
| name | Human-readable cluster name |
| version | Proxmox VE version string |
| quorate | Boolean indicating if the cluster has quorum |
| nodes_online | Number of nodes currently online in the cluster |

#### Relationships

- ProxmoxCluster contains ProxmoxNodes.

    ```
    (ProxmoxCluster)-[CONTAINS_NODE]->(ProxmoxNode)
    ```

### ProxmoxNode

Representation of a physical or virtual node in a Proxmox cluster.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique node identifier (node name) |
| name | Node hostname |
| cluster_id | ID of the parent ProxmoxCluster |
| ip | Management IP address of the node |
| status | Current status (online, offline, unknown) |
| uptime | Node uptime in seconds |
| cpu_count | Total number of CPU cores |
| cpu_usage | CPU utilization as a float (0.0 to 1.0) |
| memory_total | Total RAM in bytes |
| memory_used | Used RAM in bytes |
| disk_total | Total disk space in bytes |
| disk_used | Used disk space in bytes |

#### Relationships

- ProxmoxNode is contained by a ProxmoxCluster.

    ```
    (ProxmoxCluster)-[CONTAINS_NODE]->(ProxmoxNode)
    ```

- ProxmoxNode hosts ProxmoxVMs.

    ```
    (ProxmoxNode)-[HOSTS_VM]->(ProxmoxVM)
    ```

- ProxmoxStorage is available on ProxmoxNodes.

    ```
    (ProxmoxStorage)-[AVAILABLE_ON]->(ProxmoxNode)
    ```

### ProxmoxVM

Representation of a QEMU virtual machine or LXC container.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique identifier in format "node:vmid" |
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
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique identifier in format "vmid:disk_id" |
| disk_id | Disk identifier (e.g., "scsi0", "virtio0", "rootfs") |
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
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique identifier in format "vmid:net_id" |
| net_id | Network interface identifier (e.g., "net0", "eth0") |
| vmid | ID of the parent VM/container |
| bridge | Bridge name the interface is connected to |
| mac_address | MAC address of the interface |
| model | Network adapter model (e.g., "virtio", "e1000") |
| firewall | Boolean indicating if Proxmox firewall is enabled |
| vlan_tag | VLAN tag if configured |

#### Relationships

- ProxmoxNetworkInterface belongs to a ProxmoxVM.

    ```
    (ProxmoxVM)-[HAS_NETWORK_INTERFACE]->(ProxmoxNetworkInterface)
    ```

### ProxmoxStorage

Representation of a storage backend in Proxmox.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Unique storage identifier |
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
MATCH (c:ProxmoxCluster)-[:CONTAINS_NODE]->(n:ProxmoxNode)
OPTIONAL MATCH (n)-[:HOSTS_VM]->(v:ProxmoxVM)
WHERE v.template = false
RETURN c.name as cluster,
       n.name as node,
       count(v) as vm_count,
       n.status
ORDER BY c.name, n.name
```
