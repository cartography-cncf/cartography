# Proxmox Metadata Coverage Analysis

This document provides a comprehensive analysis of the metadata available from the Proxmox API and what is currently captured by Cartography's Proxmox integration.

## VM/Container Metadata

### ✅ Currently Captured (Basic)
- `vmid` - Virtual machine ID
- `name` - VM/container name
- `node` - Node hosting the VM
- `type` - Resource type (qemu/lxc)
- `status` - Current status (running/stopped/etc.)
- `template` - Template flag
- `cpu_cores` - Number of CPU cores
- `cpu_sockets` - Number of CPU sockets
- `memory` - Maximum memory (bytes)
- `disk_size` - Maximum disk size (bytes)
- `uptime` - Uptime in seconds
- `tags` - VM tags (semicolon-separated)

### ✅ Currently Captured (Configuration - Added)
- `ostype` - Guest OS type (l24, l26, win10, win11, etc.)
- `onboot` - Auto-start on boot flag
- `protection` - Protection from deletion flag
- `description` - VM description/notes
- `vmgenid` - VM generation ID (UUID)
- `machine` - QEMU machine type
- `bios` - BIOS type (seabios/ovmf)
- `boot` - Boot order configuration
- `scsihw` - SCSI controller type
- `cpu` - CPU model and flags
- `cpulimit` - CPU usage limit (0-128)
- `cpuunits` - CPU weight/priority
- `hotplug` - Hotplug features enabled
- `lock` - VM lock status
- `balloon` - Memory ballooning value
- `shares` - Memory shares for auto-ballooning
- `numa` - NUMA enabled
- `kvm` - KVM hardware virtualization enabled
- `localtime` - Use local time for RTC
- `keyboard` - Keyboard layout
- `vga` - VGA configuration
- `agent_config` - QEMU guest agent configuration string
- `args` - Extra QEMU arguments

### ✅ Currently Captured (Guest Agent Data - Opt-in)
These require QEMU Guest Agent to be installed and running in the VM (enabled via `--proxmox-enable-guest-agent`):
- `guest_hostname` - Guest OS hostname (via `get-host-name`)
- `guest_os_name` - OS name (via `get-osinfo`)
- `guest_os_version` - OS version (via `get-osinfo`)
- `guest_kernel_release` - Kernel release (via `get-osinfo`)
- `guest_kernel_version` - Kernel version (via `get-osinfo`)
- `guest_machine` - Hardware architecture (via `get-osinfo`)
- `agent_enabled` - Whether guest agent is available

### ⚠️ Available but Not Captured (Advanced Guest Agent Data)
- `logged_in_users` - Users currently logged in (via `get-users`)
- `vcpu_info` - vCPU information (via `get-vcpus`)

### ⚠️ Available but Not Captured (Advanced Configuration)
- Individual device details from arrays (specific `hostpci[n]`, `usb[n]`, `serial[n]`, `parallel[n]` configurations)
  - Note: Device counts are captured, but not individual device configurations

## Disk Metadata

### ✅ Currently Captured (Basic)
- `disk_id` - Disk identifier (scsi0, virtio0, etc.)
- `vmid` - Parent VM ID
- `storage` - Storage backend name
- `size` - Disk size in bytes
- `backup` - Backup enabled flag
- `cache` - Cache mode

### ✅ Currently Captured (Configuration - Added)
- `format` - Disk format (qcow2, raw, vmdk, etc.)
- `iothread` - I/O thread enabled
- `discard` - Discard/trim support
- `ssd` - SSD emulation flag
- `replicate` - Replication enabled
- `serial` - Disk serial number
- `wwn` - World Wide Name
- `snapshot` - Snapshot mode enabled
- `iops` - IOPS limit
- `iops_rd` - Read IOPS limit
- `iops_wr` - Write IOPS limit
- `mbps` - Bandwidth limit (MB/s)
- `mbps_rd` - Read bandwidth limit (MB/s)
- `mbps_wr` - Write bandwidth limit (MB/s)
- `mbps_max` - Burst bandwidth limit (MB/s)
- `mbps_rd_max` - Burst read bandwidth limit (MB/s)
- `mbps_wr_max` - Burst write bandwidth limit (MB/s)
- `iops_max` - Burst IOPS limit
- `iops_rd_max` - Burst read IOPS limit
- `iops_wr_max` - Burst write IOPS limit
- `media` - Media type (cdrom/disk)
- `ro` - Read-only flag
- `detect_zeroes` - Detect and optimize zero writes

### ⚠️ Available but Not Captured (Advanced)
- `aio` - AIO type (native, threads, io_uring)
- `bps`, `bps_rd`, `bps_wr` - Bandwidth limits in bytes per second (duplicates mbps fields)
- `bps_max_length`, `iops_max_length` - Burst duration limits
- `rerror`, `werror` - Read/write error handling
- `product`, `vendor` - SCSI product/vendor strings (SCSI disks only)
- `queues` - Number of queues (SCSI disks only)
- `scsiblock` - SCSI block passthrough (SCSI disks only)
- `shared` - Shared disk flag

## Network Interface Metadata

### ✅ Currently Captured
- `net_id` - Network interface ID (net0, net1, etc.)
- `vmid` - Parent VM ID
- `bridge` - Bridge name
- `mac_address` - MAC address
- `model` - Network adapter model (virtio, e1000, etc.)
- `firewall` - Firewall enabled flag
- `vlan_tag` - VLAN tag
- `ip` - IPv4 address (from config)
- `ip6` - IPv6 address (from config)
- `gw` - IPv4 gateway (from config)
- `gw6` - IPv6 gateway (from config)
- `mtu` - MTU size
- `rate` - Bandwidth rate limit (Mbps)
- `link_up` - Link status (inverted from link_down)
- `queues` - Multi-queue setting (VirtIO)
- `trunks` - VLAN trunk configuration
- `tag` - Native VLAN for trunk (same as vlan_tag)

### ✅ Currently Captured (Guest Agent Runtime Data - Opt-in)
When guest agent is enabled (via `--proxmox-enable-guest-agent`):
- `actual_ipv4` - Actual IPv4 addresses assigned in guest OS (CSV for multiple IPs)
- `actual_ipv6` - Actual IPv6 addresses assigned in guest OS (CSV for multiple IPs)
- `guest_interface_name` - Interface name as seen by guest OS (e.g., eth0, ens18)

## Node Metadata

### ✅ Currently Captured
- `name` - Node name
- `hostname` - Node hostname
- `ip` - Node IP address
- `status` - Node status (online/offline)
- `uptime` - Node uptime (seconds)
- `cpu_count` - Number of CPUs
- `cpu_usage` - Current CPU usage
- `memory_total` - Total memory (bytes)
- `memory_used` - Used memory (bytes)
- `disk_total` - Total disk space (bytes)
- `disk_used` - Used disk space (bytes)
- `level` - Node level/type

### ✅ Currently Captured (System Info - Added)
- `kversion` - Kernel version
- `loadavg` - Load average (CSV: 1m, 5m, 15m)
- `wait` - I/O wait percentage
- `swap_total` - Total swap space (bytes)
- `swap_used` - Used swap space (bytes)
- `swap_free` - Free swap space (bytes)
- `pveversion` - Proxmox VE version string
- `cpuinfo` - CPU model information
- `idle` - Idle CPU percentage

### ⚠️ Available but Not Captured
- `rootfs` - Root filesystem information

## Node Network Interface Metadata

### ✅ Currently Captured
- `name` - Interface name (vmbr0, eth0, etc.)
- `type` - Interface type (bridge, bond, eth, vlan, etc.)
- `address` - IPv4 address
- `netmask` - Subnet mask
- `gateway` - IPv4 gateway
- `address6` - IPv6 address
- `netmask6` - IPv6 netmask
- `gateway6` - IPv6 gateway
- `bridge_ports` - Bridge member ports
- `bond_slaves` - Bond slave interfaces
- `active` - Interface active status
- `autostart` - Auto-start on boot
- `mtu` - MTU size
- `bond_mode` - Bonding mode (balance-rr, active-backup, etc.)
- `bond_xmit_hash_policy` - Bond hashing policy
- `cidr` - CIDR notation for IPv4
- `cidr6` - CIDR notation for IPv6
- `method` - Configuration method (static, dhcp, manual)
- `method6` - IPv6 configuration method
- `comments` - Interface comments

### ⚠️ Available but Not Captured
- `ovs_*` - Open vSwitch configuration

## Cluster Metadata

### ✅ Currently Captured
- `name` - Cluster name
- `version` - Cluster version
- `quorate` - Quorum status
- `nodes_online` - Number of online nodes
- `nodes_total` - Total number of nodes in cluster
- `cluster_id` - Internal cluster ID from API
- **Migration settings** (from `/cluster/options`):
  - `migration_type` - Migration mode (secure, insecure)
  - `migration_network` - CIDR network for migrations
  - `migration_bandwidth_limit` - Bandwidth limit in KB/s
- **Console and UI settings** (from `/cluster/options`):
  - `console` - Default console viewer (html5, vv, xtermjs)
  - `keyboard` - Default keyboard layout
  - `language` - Default language
- **Email and proxy** (from `/cluster/options`):
  - `email_from` - Default sender email
  - `http_proxy` - HTTP proxy URL
- **Resource management** (from `/cluster/options`):
  - `mac_prefix` - MAC address prefix for VMs
  - `max_workers` - Maximum parallel migration workers
  - `next_id_lower`, `next_id_upper` - Auto-assigned VMID bounds
- **Corosync configuration** (from `/cluster/config`):
  - `totem_cluster_name` - Cluster name from corosync
  - `totem_config_version` - Config version
  - `totem_interface` - Network interface
  - `totem_ip_version` - IP version (ipv4/ipv6)
  - `totem_secauth` - Security authentication
  - `totem_version` - Totem protocol version

### ⚠️ Available but Not Captured
- QDevice status and configuration
- Replication jobs and status
- Cluster-wide firewall rules
- Additional corosync parameters (crypto_cipher, crypto_hash, fail_recv_const)

## Storage Metadata

### ✅ Currently Captured
Detailed storage metadata is captured in the storage module.

## Access Control Metadata

### ✅ Currently Captured
Users, groups, roles, and ACLs are captured in the access module.

## High Availability Metadata

### ✅ Currently Captured
HA groups and resources are captured in the ha module.

## Backup Metadata

### ✅ Currently Captured
Backup jobs are captured in the backup module.

## Firewall Metadata

### ✅ Currently Captured
Firewall rules and IP sets are captured in the firewall module.

## Certificate Metadata

### ✅ Currently Captured
SSL/TLS certificates are captured in the certificate module.

## Resource Pool Metadata

### ✅ Currently Captured
Resource pools are captured in the pool module.

## Future Enhancement Considerations

### High Priority (Should Add)
1. **Guest Agent Integration** (opt-in):
   - Actual OS hostname and version
   - Real network interface IPs (not just config)
   - Running processes and logged-in users
   - Filesystem information

2. **Additional Disk Metadata**:
   - AIO type
   - Error handling policies
   - Burst limits

3. **Additional Network Metadata**:
   - Multi-queue settings
   - VLAN trunk configuration

### Medium Priority (Nice to Have)
1. **Advanced VM Configuration**:
   - PCI/USB passthrough devices
   - Serial/parallel ports
   - Audio devices
   - EFI/TPM configuration

2. **Node System Information**:
   - Kernel version
   - Load average
   - Detailed filesystem info

3. **Cluster Details**:
   - Corosync configuration
   - Replication job status

### Low Priority (Optional)
1. **NUMA Configuration**
2. **Hugepages Settings**
3. **Watchdog Configuration**
4. **Random Number Generator Settings**

## Implementation Notes

### Guest Agent Data
Implement as an optional feature with configuration flag:
```python
# In cartography/config.py
proxmox_enable_guest_agent: bool = False

# Only fetch guest agent data if enabled and agent is detected
if config.proxmox_enable_guest_agent and vm_has_guest_agent(vm_config):
    guest_data = get_guest_agent_data(proxmox_client, node_name, vmid)
    vm.update(guest_data)
```

### Performance Considerations
- Guest agent calls add significant overhead (one API call per VM)
- Consider batching or caching strategies
- Document performance impact clearly

### Error Handling
- Many VMs won't have guest agent installed
- Handle gracefully with try/except and logging
- Don't fail the entire sync if guest agent calls fail

## API Endpoints Reference

### VM/Container Endpoints
- `GET /nodes/{node}/qemu` - List QEMU VMs
- `GET /nodes/{node}/lxc` - List LXC containers
- `GET /nodes/{node}/qemu/{vmid}/config` - Get VM config
- `GET /nodes/{node}/lxc/{vmid}/config` - Get container config
- `POST /nodes/{node}/qemu/{vmid}/agent/{command}` - Execute guest agent command

### Node Endpoints
- `GET /nodes/{node}/status` - Get node status
- `GET /nodes/{node}/network` - Get network configuration

### Cluster Endpoints
- `GET /cluster/status` - Get cluster status
- `GET /cluster/resources` - Get cluster resources

### Storage Endpoints
- `GET /storage` - List storage
- `GET /storage/{storage}` - Get storage details

### Access Control Endpoints
- `GET /access/users` - List users
- `GET /access/groups` - List groups
- `GET /access/roles` - List roles
- `GET /access/acl` - List ACLs

## Proxmoxer Library Coverage

The `proxmoxer` library provides thin wrapper access to all Proxmox API endpoints:
- Follows REST API structure exactly
- No additional metadata beyond what API provides
- All Proxmox API v2 endpoints are accessible

## Conclusion

The current implementation captures the most important operational and configuration metadata for:
- ✅ VM/container identification and status
- ✅ Resource allocation (CPU, memory, disk, network)
- ✅ Configuration settings (boot, OS type, protection)
- ✅ Storage and network interfaces
- ✅ Cluster and node information
- ✅ Access control and security
- ✅ High availability and backups

The main gaps are:
1. Guest agent data (requires opt-in feature)
2. Advanced hardware configuration (PCI passthrough, etc.)
3. Performance monitoring data (beyond basic metrics)

For most use cases, the current metadata coverage is comprehensive and provides excellent visibility into Proxmox infrastructure.
