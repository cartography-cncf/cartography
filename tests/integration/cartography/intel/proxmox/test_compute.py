"""
Integration tests for Proxmox compute module (VMs and containers).
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.compute
from cartography.intel.proxmox.compute import sync as compute_sync
from tests.data.proxmox.compute import MOCK_STORAGE_DATA
from tests.data.proxmox.compute import MOCK_VM_CONFIG
from tests.data.proxmox.compute import MOCK_VM_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"

# Mock node list for compute sync
MOCK_NODES = [
    {"node": "node1"},
    {"node": "node2"},
]


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_sync_vms_and_containers(mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session):
    """
    Test that VMs and containers sync correctly.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Mock to return only qemu VMs for get_vms_for_node
    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']
    
    # Mock to return only lxc containers for get_containers_for_node
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']
    
    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check VM nodes
    expected_vm_nodes = {
        ("node1/qemu/100", "test-vm-1", "qemu", "running"),
        ("node1/qemu/101", "test-vm-2", "qemu", "stopped"),
        ("node2/lxc/200", "test-container-1", "lxc", "running"),
    }
    assert check_nodes(neo4j_session, "ProxmoxVM", ["id", "name", "type", "status"]) == expected_vm_nodes

    # Assert - Check VM->Cluster relationships
    expected_rels = {
        ("node1/qemu/100", TEST_CLUSTER_ID),
        ("node1/qemu/101", TEST_CLUSTER_ID),
        ("node2/lxc/200", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxVM",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_sync_vm_disks(mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session):
    """
    Test that VM disks are synced correctly.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']
    
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']
    
    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check disk nodes
    expected_disk_nodes = {
        ("node1/qemu/100:scsi0", "scsi0", "local-lvm", "100G"),
        ("node1/qemu/101:scsi0", "scsi0", "local-lvm", "50G"),
        ("node2/lxc/200:rootfs", "rootfs", "local-lvm", "10G"),
    }
    assert check_nodes(neo4j_session, "ProxmoxDisk", ["id", "device", "storage", "size"]) == expected_disk_nodes

    # Assert - Check disk->VM relationships
    expected_rels = {
        ("node1/qemu/100:scsi0", "node1/qemu/100"),
        ("node1/qemu/101:scsi0", "node1/qemu/101"),
        ("node2/lxc/200:rootfs", "node2/lxc/200"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxDisk",
            "id",
            "ProxmoxVM",
            "id",
            "HAS_DISK",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_sync_vm_network_interfaces(mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session):
    """
    Test that VM network interfaces are synced correctly with IP addresses.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']
    
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']
    
    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check network interface nodes
    expected_interface_nodes = {
        ("node1/qemu/100:net0", "net0", "BC:24:11:11:11:11"),
        ("node1/qemu/100:net1", "net1", "BC:24:11:11:11:12"),
        ("node1/qemu/101:net0", "net0", "BC:24:11:22:22:22"),
        ("node2/lxc/200:net0", "net0", "BC:24:11:33:33:33"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxNetworkInterface", ["id", "device", "hwaddr"])
        == expected_interface_nodes
    )

    # Assert - Check interface->VM relationships
    expected_rels = {
        ("node1/qemu/100:net0", "node1/qemu/100"),
        ("node1/qemu/100:net1", "node1/qemu/100"),
        ("node1/qemu/101:net0", "node1/qemu/101"),
        ("node2/lxc/200:net0", "node2/lxc/200"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxNetworkInterface",
            "id",
            "ProxmoxVM",
            "id",
            "HAS_NETWORK_INTERFACE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_vm_network_interface_ip_properties(mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session):
    """
    Test that network interface IP properties are correctly stored.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']
    
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']
    
    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check IPv4 properties on VM interface
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNetworkInterface {id: 'node1/qemu/100:net0'})
        RETURN n.ip, n.gw, n.bridge
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ip"] == "192.168.1.100/24"
    assert data["n.gw"] == "192.168.1.1"
    assert data["n.bridge"] == "vmbr0"

    # Assert - Check IPv6 properties on container interface
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNetworkInterface {id: 'node2/lxc/200:net0'})
        RETURN n.ip, n.gw, n.ip6, n.gw6
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ip"] == "192.168.1.200/24"
    assert data["n.gw"] == "192.168.1.1"
    assert data["n.ip6"] == "2001:db8::200/64"
    assert data["n.gw6"] == "2001:db8::1"


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_vm_cpu_properties(mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session):
    """
    Test that VM CPU configuration is correctly stored.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']
    
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']
    
    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check CPU configuration
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/100'})
        RETURN n.cores, n.sockets, n.vcpus
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.cores"] == 2
    assert data["n.sockets"] == 1
    assert data["n.vcpus"] == 2  # cores * sockets

    # Assert - Check second VM with different CPU config
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/101'})
        RETURN n.cores, n.sockets, n.vcpus
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.cores"] == 1
    assert data["n.sockets"] == 2
    assert data["n.vcpus"] == 2  # cores * sockets
