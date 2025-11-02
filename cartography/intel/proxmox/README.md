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

### Relationships

```
(:ProxmoxCluster)-[:CONTAINS_NODE]->(:ProxmoxNode)
(:ProxmoxNode)-[:HOSTS_VM]->(:ProxmoxVM)
(:ProxmoxVM)-[:HAS_DISK]->(:ProxmoxDisk)
(:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNetworkInterface)
(:ProxmoxDisk)-[:STORED_ON]->(:ProxmoxStorage)
(:ProxmoxStorage)-[:AVAILABLE_ON]->(:ProxmoxNode)
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

The Proxmox integration follows Cartography's standard **Get → Transform → Load** pattern:

1. **Get**: Retrieve data from Proxmox API using proxmoxer library
2. **Transform**: Convert API responses to standardized format
3. **Load**: Store data in Neo4j using MERGE operations
4. **Cleanup**: Remove stale data from previous syncs

Each module (`cluster.py`, `compute.py`, `storage.py`) follows this pattern independently.

## Development

### Running Tests

```bash
pytest tests/unit/cartography/intel/proxmox/
```

### Adding New Resources

To add new Proxmox resources:

1. Create a new module (e.g., `backup.py`)
2. Implement Get → Transform → Load functions
3. Add sync function to orchestrate the flow
4. Call from `__init__.py` main entry point
5. Update cleanup job JSON
6. Add unit tests

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
