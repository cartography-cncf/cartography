"""
Tests for Proxmox compute module.
"""
import pytest

from cartography.intel.proxmox.compute import extract_disk_data
from cartography.intel.proxmox.compute import extract_network_data
from cartography.intel.proxmox.compute import transform_vm_data


def test_transform_vm_data():
    """Test VM and container data transformation."""
    raw_vms = [
        {
            'vmid': 100,
            'name': 'test-vm-1',
            'node': 'node1',
            'type': 'qemu',
            'status': 'running',
            'maxmem': 4294967296,
            'cpus': 2,
            'sockets': 1,
            'maxdisk': 107374182400,
            'uptime': 3600,
            'tags': 'production;web',
            'template': False,
        },
        {
            'vmid': 101,
            'name': 'test-ct-1',
            'node': 'node1',
            'type': 'lxc',
            'status': 'stopped',
            'maxmem': 2147483648,
            'cores': 1,
            'template': False,
        },
    ]

    cluster_id = 'test-cluster'

    result = transform_vm_data(raw_vms, cluster_id)

    assert len(result) == 2

    # Test QEMU VM
    assert result[0]['id'] == 'node1:100'
    assert result[0]['vmid'] == 100
    assert result[0]['name'] == 'test-vm-1'
    assert result[0]['type'] == 'qemu'
    assert result[0]['cpu_cores'] == 2
    assert result[0]['memory'] == 4294967296
    assert result[0]['tags'] == ['production', 'web']

    # Test LXC container
    assert result[1]['id'] == 'node1:101'
    assert result[1]['vmid'] == 101
    assert result[1]['type'] == 'lxc'
    assert result[1]['cpu_cores'] == 1
    assert result[1]['status'] == 'stopped'


def test_extract_disk_data():
    """Test disk extraction from VM config."""
    vm_config = {
        'scsi0': 'local-lvm:vm-100-disk-0,size=32G,backup=1',
        'virtio0': 'local-lvm:vm-100-disk-1,size=64G,cache=writeback',
        'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',  # Should be ignored
    }

    result = extract_disk_data(vm_config, 100)

    assert len(result) == 2

    # Test scsi0
    scsi_disk = next(d for d in result if d['disk_id'] == 'scsi0')
    assert scsi_disk['id'] == '100:scsi0'
    assert scsi_disk['vmid'] == 100
    assert scsi_disk['storage'] == 'local-lvm'
    assert scsi_disk['size'] == 32 * 1024**3  # 32GB in bytes
    assert scsi_disk.get('backup') is True

    # Test virtio0
    virtio_disk = next(d for d in result if d['disk_id'] == 'virtio0')
    assert virtio_disk['id'] == '100:virtio0'
    assert virtio_disk['storage'] == 'local-lvm'
    assert virtio_disk['size'] == 64 * 1024**3  # 64GB in bytes
    assert virtio_disk.get('cache') == 'writeback'


def test_extract_network_data():
    """Test network interface extraction from VM config."""
    vm_config = {
        'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1,tag=100',
        'net1': 'e1000=11:22:33:44:55:66,bridge=vmbr1',
        'scsi0': 'local-lvm:vm-100-disk-0,size=32G',  # Should be ignored
    }

    result = extract_network_data(vm_config, 100)

    assert len(result) == 2

    # Test net0
    net0 = next(i for i in result if i['net_id'] == 'net0')
    assert net0['id'] == '100:net0'
    assert net0['vmid'] == 100
    assert net0['model'] == 'virtio'
    assert net0['mac_address'] == 'AA:BB:CC:DD:EE:FF'
    assert net0['bridge'] == 'vmbr0'
    assert net0.get('firewall') is True
    assert net0.get('vlan_tag') == 100

    # Test net1
    net1 = next(i for i in result if i['net_id'] == 'net1')
    assert net1['id'] == '100:net1'
    assert net1['model'] == 'e1000'
    assert net1['mac_address'] == '11:22:33:44:55:66'
    assert net1['bridge'] == 'vmbr1'
