"""
Integration tests for Proxmox compute module (VMs and containers).
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.compute
from cartography.intel.proxmox.compute import sync as compute_sync
from tests.data.proxmox.compute import MOCK_GUEST_AGENT_HOSTNAME
from tests.data.proxmox.compute import MOCK_GUEST_AGENT_NETWORK
from tests.data.proxmox.compute import MOCK_GUEST_AGENT_OSINFO
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
def test_sync_vms_and_containers(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that VMs and containers sync correctly.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Mock to return only qemu VMs for get_vms_for_node
    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    # Mock to return only lxc containers for get_containers_for_node
    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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
    assert (
        check_nodes(neo4j_session, "ProxmoxVM", ["id", "name", "type", "status"])
        == expected_vm_nodes
    )

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
def test_sync_vm_disks(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that VM disks are synced correctly.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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
        ("node1/qemu/100:scsi0", "scsi0", "local-lvm", 107374182400),  # 100G in bytes
        ("node1/qemu/101:scsi0", "scsi0", "local-lvm", 53687091200),  # 50G in bytes
        ("node1/qemu/101:efidisk0", "efidisk0", "local-lvm", 4194304),  # 4M in bytes
        ("node1/qemu/101:tpmstate0", "tpmstate0", "local-lvm", 4194304),  # 4M in bytes
        ("node2/lxc/200:rootfs", "rootfs", "local-lvm", 10737418240),  # 10G in bytes
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxDisk", ["id", "disk_id", "storage", "size"])
        == expected_disk_nodes
    )

    # Assert - Check disk->VM relationships
    expected_rels = {
        ("node1/qemu/100:scsi0", "node1/qemu/100"),
        ("node1/qemu/101:scsi0", "node1/qemu/101"),
        ("node1/qemu/101:efidisk0", "node1/qemu/101"),
        ("node1/qemu/101:tpmstate0", "node1/qemu/101"),
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
def test_sync_vm_network_interfaces(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that VM network interfaces are synced correctly.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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
        check_nodes(
            neo4j_session, "ProxmoxNetworkInterface", ["id", "net_id", "mac_address"]
        )
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
def test_vm_network_interface_ip_properties(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that network interface IP properties are correctly stored.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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
def test_vm_cpu_properties(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that VM CPU configuration is correctly stored.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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


@patch.object(cartography.intel.proxmox.compute, "get_guest_agent_info")
@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_sync_with_guest_agent_enabled(
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    mock_get_guest_agent_info,
    neo4j_session,
):
    """
    Test that guest agent data is synced when enabled.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    def get_guest_agent_info_side_effect(proxmox_client, node, vmid):
        result = {}
        osinfo = MOCK_GUEST_AGENT_OSINFO.get(vmid, {}).get("result", {})
        if osinfo:
            result["guest_os_name"] = osinfo.get("name") or osinfo.get("id")
            result["guest_os_version"] = osinfo.get("version") or osinfo.get(
                "version-id"
            )
            result["guest_kernel_release"] = osinfo.get("kernel-release")
            result["guest_kernel_version"] = osinfo.get("kernel-version")
            result["guest_machine"] = osinfo.get("machine")

        hostname = MOCK_GUEST_AGENT_HOSTNAME.get(vmid, {}).get("result", {})
        if hostname:
            result["guest_hostname"] = hostname.get("host-name")

        network = MOCK_GUEST_AGENT_NETWORK.get(vmid, {}).get("result", [])
        if network:
            result["guest_network_interfaces"] = network

        result["agent_enabled"] = bool(result)
        return result

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect
    mock_get_guest_agent_info.side_effect = get_guest_agent_info_side_effect

    # Act - Enable guest agent
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        enable_guest_agent=True,
    )

    # Assert - Check guest agent data on VM 100
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/100'})
        RETURN n.guest_hostname, n.guest_os_name, n.guest_os_version,
               n.guest_kernel_release, n.guest_kernel_version, n.guest_machine
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.guest_hostname"] == "test-vm-1.example.com"
    assert data["n.guest_os_name"] == "Ubuntu"
    assert data["n.guest_os_version"] == "22.04"
    assert data["n.guest_kernel_release"] == "5.15.0-89-generic"
    assert (
        data["n.guest_kernel_version"] == "#99-Ubuntu SMP Mon Oct 30 20:42:41 UTC 2023"
    )
    assert data["n.guest_machine"] == "x86_64"

    # Assert - Check that VM without guest agent has no data
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/101'})
        RETURN n.guest_hostname, n.guest_os_name
        """
    )
    data = result.single()
    assert data is not None
    # Should be None/null when agent not available
    assert data["n.guest_hostname"] is None
    assert data["n.guest_os_name"] is None

    # Assert - Check network interfaces have actual IPs from guest agent
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNetworkInterface {id: 'node1/qemu/100:net0'})
        RETURN n.actual_ipv4, n.actual_ipv6, n.guest_interface_name
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.actual_ipv4"] == "192.168.1.100/24,10.0.0.100/16"
    assert data["n.actual_ipv6"] == "fe80::be24:11ff:fe11:1111/64"
    assert data["n.guest_interface_name"] == "ens18"

    # Assert - Check second network interface has actual IPs
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNetworkInterface {id: 'node1/qemu/100:net1'})
        RETURN n.actual_ipv4, n.guest_interface_name
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.actual_ipv4"] == "192.168.2.100/24"
    assert data["n.guest_interface_name"] == "ens19"


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_sync_with_guest_agent_disabled(
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    neo4j_session,
):
    """
    Test that guest agent data is NOT synced when disabled (default).
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    # Act - Guest agent disabled by default
    compute_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        enable_guest_agent=False,
    )

    # Assert - Check that no guest agent data is present
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/100'})
        RETURN n.guest_hostname, n.guest_os_name
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.guest_hostname"] is None
    assert data["n.guest_os_name"] is None


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_vm_enhanced_properties(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that enhanced VM properties from config are synced.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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

    # Assert - Check enhanced VM properties on VM 100
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/100'})
        RETURN n.ostype, n.onboot, n.protection, n.description,
               n.machine, n.bios, n.cpu, n.cpulimit, n.cpuunits, n.hotplug
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ostype"] == "l26"
    assert data["n.onboot"] == 1
    assert data["n.protection"] == 0
    assert data["n.description"] == "Test VM 1"
    assert data["n.machine"] == "pc-i440fx-8.0"
    assert data["n.bios"] == "seabios"
    assert data["n.cpu"] == "host"
    assert data["n.cpulimit"] == 0
    assert data["n.cpuunits"] == 1024
    assert data["n.hotplug"] == "network,disk,usb"

    # Assert - Check enhanced VM properties on VM 101 (Windows VM)
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/101'})
        RETURN n.ostype, n.onboot, n.protection, n.machine, n.bios
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ostype"] == "win10"
    assert data["n.onboot"] == 0
    assert data["n.protection"] == 1
    assert data["n.machine"] == "pc-q35-8.0"
    assert data["n.bios"] == "ovmf"


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_disk_enhanced_properties(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that enhanced disk properties (backup, cache, etc.) are synced.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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

    # Assert - Check enhanced disk properties on VM 100 disk
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxDisk {id: 'node1/qemu/100:scsi0'})
        RETURN n.format, n.iothread, n.discard, n.ssd
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.format"] == "qcow2"
    assert data["n.iothread"] is True  # Boolean conversion from "1"
    assert data["n.discard"] == "on"
    assert data["n.ssd"] is True  # Boolean conversion from "1"

    # Assert - Check enhanced disk properties on VM 101 disk
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxDisk {id: 'node1/qemu/101:scsi0'})
        RETURN n.backup, n.cache
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.backup"] is False  # Boolean conversion from "0"
    assert data["n.cache"] == "writeback"


@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
def test_vm_additional_hardware_properties(
    mock_get_vm_config, mock_get_containers, mock_get_vms, neo4j_session
):
    """
    Test that additional hardware properties (PCI, USB, serial) are synced.
    """
    # Arrange - Create cluster node first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "qemu"]

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get("type") == "lxc"]

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

    # Assert - Check additional hardware properties on VM 100
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/100'})
        RETURN n.balloon, n.numa, n.kvm, n.watchdog, n.rng0,
               n.hostpci_count, n.usb_count, n.serial_count
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.balloon"] == 2048
    assert data["n.numa"] == 0
    assert data["n.kvm"] == 1
    assert data["n.watchdog"] == "i6300esb,action=reset"
    assert data["n.rng0"] == "source=/dev/urandom"
    assert data["n.hostpci_count"] == 2
    assert data["n.usb_count"] == 1
    assert data["n.serial_count"] == 1

    # Assert - Check EFI and TPM on VM 101 (Windows 11 VM)
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxVM {id: 'node1/qemu/101'})
        RETURN n.efidisk0, n.tpmstate0
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.efidisk0"] == "local-lvm:vm-101-disk-1,size=4M"
    assert data["n.tpmstate0"] == "local-lvm:vm-101-disk-2,size=4M,version=v2.0"
