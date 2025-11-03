# Proxmox Virtual Environment Integration

This module syncs Proxmox Virtual Environment (PVE) infrastructure into Cartography, enabling infrastructure asset tracking across Proxmox clusters.

## Features

The Proxmox integration syncs the following resources:

- **Clusters and Nodes**: Physical/virtual nodes in your Proxmox cluster
- **Virtual Machines**: QEMU/KVM virtual machines with detailed configuration
- **Containers**: LXC containers with resource allocation
- **Disks**: Virtual disk configurations and storage relationships
- **Network Interfaces**: VM network interfaces with VLAN and bridge information
- **Storage**: Storage backends (local, NFS, Ceph, LVM, etc.)
- **Resource Pools**: Pool-based organization of VMs, containers, and storage
- **Backup Jobs**: Scheduled backup configurations with retention policies

## Configuration

### Prerequisites

1. **Proxmox VE 7.0+** (tested with 8.x)
2. **API Token or User Credentials**
3. **Permissions**: Read-only access is sufficient (`PVEAuditor` role recommended)

### Setup

#### Option 1: API Token Authentication (Recommended)

1. Create an API token in Proxmox:
   - Navigate to Datacenter → Permissions → API Tokens
   - Create a new token for user `root@pam` with name `cartography`
   - Grant the `PVEAuditor` role on `/`
   - Save the token value securely

2. Set environment variables:
   ```bash
   export PROXMOX_TOKEN_NAME="cartography"
   export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   ```

3. Run Cartography:
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-token-name-env-var PROXMOX_TOKEN_NAME \
       --proxmox-token-value-env-var PROXMOX_TOKEN_VALUE
   ```

#### Option 2: Password Authentication

1. Set environment variable:
   ```bash
   export PROXMOX_PASSWORD="your-password"
   ```

2. Run Cartography:
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-password-env-var PROXMOX_PASSWORD
   ```

## Schema

### Node Types

#### ProxmoxCluster
- `id`: Cluster identifier
- `name`: Cluster name
- `version`: Proxmox VE version
- `quorate`: Cluster quorum status
- `nodes_online`: Number of online nodes

#### ProxmoxNode
- `id`: Node name (unique)
- `name`: Node display name
- `ip`: Management IP address
- `status`: online/offline/unknown
- `cpu_count`, `cpu_usage`: CPU information
- `memory_total`, `memory_used`: RAM information
- `disk_total`, `disk_used`: Disk information

#### ProxmoxVM
- `id`: Format `node:vmid`
- `vmid`: VM ID number
- `name`: VM name
- `type`: qemu or lxc
- `status`: running/stopped/paused
- `cpu_cores`, `cpu_sockets`: CPU configuration
- `memory`: RAM in bytes
- `tags`: Array of VM tags

#### ProxmoxDisk
- `id`: Format `vmid:disk_id`
- `disk_id`: Disk identifier (e.g., scsi0, virtio0)
- `storage`: Storage backend ID
- `size`: Size in bytes
- `backup`: Backup enabled flag

#### ProxmoxNetworkInterface
- `id`: Format `vmid:net_id`
- `net_id`: Network interface identifier
- `bridge`: Bridge name
- `mac_address`: MAC address
- `model`: Network adapter model
- `vlan_tag`: VLAN tag (optional)

#### ProxmoxStorage
- `id`: Storage ID
- `type`: Storage type (dir, nfs, lvm, ceph, etc.)
- `content_types`: Array of content types
- `shared`: Shared storage flag
- `total`, `used`, `available`: Space information

#### ProxmoxPool
- `id`: Pool identifier
- `poolid`: Pool name
- `comment`: Description/notes

#### ProxmoxBackupJob
- `id`: Job identifier
- `schedule`: Cron-style schedule
- `storage`: Target storage backend
- `enabled`: Job enabled/disabled
- `mode`: Backup mode (snapshot, suspend, stop)
- `compression`: Compression type (zstd, gzip, lzo)
- `prune_backups`: Retention policy settings

### Relationships

```
(:ProxmoxCluster)-[:CONTAINS_NODE]->(:ProxmoxNode)
(:ProxmoxNode)-[:HOSTS_VM]->(:ProxmoxVM)
(:ProxmoxVM)-[:HAS_DISK]->(:ProxmoxDisk)
(:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNetworkInterface)
(:ProxmoxDisk)-[:STORED_ON]->(:ProxmoxStorage)
(:ProxmoxStorage)-[:AVAILABLE_ON]->(:ProxmoxNode)
(:ProxmoxPool)-[:CONTAINS_VM]->(:ProxmoxVM)
(:ProxmoxPool)-[:CONTAINS_STORAGE]->(:ProxmoxStorage)
(:ProxmoxBackupJob)-[:BACKS_UP]->(:ProxmoxVM)
(:ProxmoxBackupJob)-[:BACKS_UP_TO]->(:ProxmoxStorage)
```

## Example Queries

### Find all running VMs
```cypher
MATCH (v:ProxmoxVM)
WHERE v.status = 'running'
RETURN v.name, v.node, v.memory, v.cpu_cores
```

### Find VMs with internet-facing interfaces
```cypher
MATCH (v:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(i:ProxmoxNetworkInterface)
WHERE i.bridge = 'vmbr0' AND v.status = 'running'
RETURN v.name, i.mac_address, i.bridge
```

### Find nodes with high CPU usage
```cypher
MATCH (n:ProxmoxNode)
WHERE n.cpu_usage > 0.8
RETURN n.name, n.cpu_usage, n.status
ORDER BY n.cpu_usage DESC
```

### Find VMs by tag
```cypher
MATCH (v:ProxmoxVM)
WHERE 'production' IN v.tags
RETURN v.name, v.node, v.tags
```

### Find all storage backends and their capacity
```cypher
MATCH (s:ProxmoxStorage)
RETURN s.name, s.type, s.total, s.used, s.available
ORDER BY s.used DESC
```

### Find VMs in a specific pool
```cypher
MATCH (pool:ProxmoxPool {poolid: 'production'})-[:CONTAINS_VM]->(vm:ProxmoxVM)
RETURN vm.name, vm.status, vm.node
ORDER BY vm.name
```

### Find all backup jobs for a VM
```cypher
MATCH (vm:ProxmoxVM {name: 'my-vm'})<-[:BACKS_UP]-(job:ProxmoxBackupJob)
RETURN job.id, job.schedule, job.enabled, job.storage
ORDER BY job.schedule
```

### Find VMs not covered by any backup job
```cypher
MATCH (vm:ProxmoxVM)
WHERE NOT (vm)<-[:BACKS_UP]-(:ProxmoxBackupJob)
AND vm.template = false
RETURN vm.name, vm.node, vm.status
ORDER BY vm.name
```

### Find disabled backup jobs
```cypher
MATCH (job:ProxmoxBackupJob)
WHERE job.enabled = false
RETURN job.id, job.schedule, job.notes
```

## Permissions Required

The Proxmox user or API token needs the following permissions:

- **VM.Audit**: Read VM configurations
- **Datastore.Audit**: Read storage information
- **Sys.Audit**: Read system information

The built-in `PVEAuditor` role provides all necessary permissions.

## SSL Verification

By default, SSL certificates are verified. To disable verification (not recommended for production):

```bash
cartography --proxmox-host proxmox.example.com \
    --proxmox-verify-ssl false
```

## Architecture

The Proxmox integration follows Cartography's **modern data model approach** with the standard **Get → Transform → Load → Cleanup** pattern:

1. **Get**: Retrieve data from Proxmox API using proxmoxer library
2. **Transform**: Convert API responses to standardized format
3. **Load**: Store data in Neo4j using modern `load()` function with schema definitions
4. **Cleanup**: Remove stale data using `GraphJob.from_node_schema()`

### Modern Data Model Benefits

The Proxmox module uses Cartography's **declarative data model schemas** instead of handwritten Cypher queries:

- **Type Safety**: Python dataclasses provide compile-time validation
- **Maintainability**: Schema definitions are centralized in `cartography/models/proxmox/`
- **Automatic Cleanup**: GraphJob handles stale data removal automatically
- **Relationship Management**: Declarative relationship schemas simplify connections
- **Indexing**: Extra indexes created automatically on frequently queried fields

Each module (`cluster.py`, `compute.py`, `storage.py`) follows this pattern independently.

## Development

### Running Tests

```bash
pytest tests/unit/cartography/intel/proxmox/
pytest tests/integration/cartography/intel/proxmox/
```

### Adding New Resources

To add new Proxmox resources following modern patterns:

1. **Define Data Model** in `cartography/models/proxmox/`:
   - Create node properties class extending `CartographyNodeProperties`
   - Define relationship schemas extending `CartographyRelSchema`
   - Create node schema extending `CartographyNodeSchema`

2. **Implement Intel Module** in `cartography/intel/proxmox/`:
   - Create `get()` functions for API calls
   - Create `transform()` functions for data shaping
   - Create `load()` functions using modern `load()` with schemas
   - Create `sync()` orchestration function

3. **Update Main Entry Point** in `__init__.py`:
   - Call your sync function
   - Add cleanup using `GraphJob.from_node_schema()`

4. **Add Tests**:
   - Unit tests for transform functions
   - Integration tests using `check_nodes()` and `check_rels()`

See `AGENTS.md` in the repository root for comprehensive development guidance.

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Verify Proxmox host is reachable
2. Check firewall rules allow port 8006
3. Verify API token/credentials are correct
4. Try disabling SSL verification temporarily

### Permission Errors

If you see 403 errors:

1. Verify token/user has appropriate roles
2. Check ACL permissions on `/` path
3. Ensure token is not expired

### Import Errors

If proxmoxer is not found:

```bash
pip install proxmoxer>=2.0.1
```

## References

- [Proxmox VE API Documentation](https://pve.proxmox.com/pve-docs/api-viewer/)
- [proxmoxer Library](https://pypi.org/project/proxmoxer/)
- [Cartography Developer Guide](https://cartography-cncf.github.io/cartography/dev/developer-guide.html)
