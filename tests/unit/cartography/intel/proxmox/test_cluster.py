"""
Tests for Proxmox cluster module.
"""

from cartography.intel.proxmox.cluster import transform_cluster_config
from cartography.intel.proxmox.cluster import transform_cluster_data
from cartography.intel.proxmox.cluster import transform_node_data


def test_transform_cluster_data_with_cluster_info():
    """Test cluster data transformation with cluster information present."""
    raw_status = [
        {
            "type": "cluster",
            "name": "test-cluster",
            "version": "8.1",
            "quorate": 1,
        },
        {
            "type": "node",
            "name": "node1",
            "online": 1,
        },
        {
            "type": "node",
            "name": "node2",
            "online": 1,
        },
    ]

    result = transform_cluster_data(raw_status, "proxmox.example.com")

    assert result["id"] == "test-cluster"
    assert result["name"] == "test-cluster"
    assert result["version"] == "8.1"
    assert result["quorate"] is True
    assert result["nodes_online"] == 2


def test_transform_cluster_data_without_cluster_info():
    """Test cluster data transformation without cluster information (synthetic cluster)."""
    raw_status = [
        {
            "type": "node",
            "name": "node1",
            "online": 1,
        },
    ]

    result = transform_cluster_data(raw_status, "proxmox.example.com")

    assert result["id"] == "proxmox-example-com"
    assert result["name"] == "proxmox-example-com"
    assert result["version"] == "unknown"
    assert result["quorate"] is True
    assert result["nodes_online"] == 1


def test_transform_node_data():
    """Test node data transformation."""
    raw_nodes = [
        {
            "node": "node1",
            "ip": "192.168.1.10",
            "status": "online",
            "uptime": 86400,
            "maxcpu": 8,
            "cpu": 0.25,
            "maxmem": 34359738368,
            "mem": 8589934592,
            "maxdisk": 1099511627776,
            "disk": 274877906944,
            "level": "",
        },
        {
            "node": "node2",
            "ip": "192.168.1.11",
            "status": "online",
        },
    ]

    cluster_id = "test-cluster"

    result = transform_node_data(raw_nodes, cluster_id)

    assert len(result) == 2
    assert result[0]["id"] == "node1"
    assert result[0]["cluster_id"] == "test-cluster"
    assert result[0]["cpu_count"] == 8
    assert result[0]["memory_total"] == 34359738368
    assert result[0]["ip"] == "192.168.1.10"

    # Test default values for second node
    assert result[1]["id"] == "node2"
    assert result[1]["cpu_count"] == 0
    assert result[1]["memory_total"] == 0
    assert result[1]["status"] == "online"


def test_transform_cluster_config_dict():
    """Test cluster config transformation when API returns a dict."""
    cluster_config = {
        "totem": {
            "cluster_name": "test-cluster",
            "config_version": 3,
            "interface": "vmbr0",
            "ip_version": "ipv4",
            "secauth": "on",
            "version": 2,
        },
    }

    result = transform_cluster_config(cluster_config)

    assert result["totem_cluster_name"] == "test-cluster"
    assert result["totem_config_version"] == 3
    assert result["totem_interface"] == "vmbr0"
    assert result["totem_ip_version"] == "ipv4"
    assert result["totem_secauth"] == "on"
    assert result["totem_version"] == 2


def test_transform_cluster_config_list():
    """Test cluster config transformation when API returns a list."""
    cluster_config = [
        {
            "section": "totem",
            "cluster_name": "test-cluster",
            "config_version": 3,
            "interface": "vmbr0",
            "ip_version": "ipv4",
            "secauth": "on",
            "version": 2,
        },
    ]

    result = transform_cluster_config(cluster_config)

    assert result["totem_cluster_name"] == "test-cluster"
    assert result["totem_config_version"] == 3
    assert result["totem_interface"] == "vmbr0"
    assert result["totem_ip_version"] == "ipv4"
    assert result["totem_secauth"] == "on"
    assert result["totem_version"] == 2


def test_transform_cluster_config_empty():
    """Test cluster config transformation with empty/None input."""
    assert transform_cluster_config({}) == {}
    assert transform_cluster_config([]) == {}
    assert transform_cluster_config(None) == {}
