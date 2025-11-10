"""
Sync Proxmox clusters and nodes.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.cluster import ProxmoxClusterSchema
from cartography.models.proxmox.cluster import ProxmoxNodeNetworkInterfaceSchema
from cartography.models.proxmox.cluster import ProxmoxNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# Per docs: "should be 'dumb'... raise an exception if not able to complete"
# ============================================================================


@timeit
def get_cluster_status(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get cluster status information.

    :param proxmox_client: Proxmox API client
    :return: Cluster status list
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.status.get()


@timeit
def get_nodes(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get all nodes in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of node dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes.get()


@timeit
def get_node_status(proxmox_client, node_name: str) -> Dict[str, Any]:
    """
    Get detailed status for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Name of the node
    :return: Node status dict
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).status.get()


@timeit
def get_node_network(proxmox_client, node_name: str) -> List[Dict[str, Any]]:
    """
    Get network interface configuration for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Name of the node
    :return: List of network interface dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.nodes(node_name).network.get()
    except Exception as e:
        logger.warning(f"Could not get network config for node {node_name}: {e}")
        return []


@timeit
def get_cluster_options(proxmox_client) -> Dict[str, Any]:
    """
    Get cluster-wide configuration options.

    :param proxmox_client: Proxmox API client
    :return: Cluster options dict
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.cluster.options.get()
    except Exception as e:
        logger.warning(f"Could not get cluster options: {e}")
        return {}


@timeit
def get_cluster_resources(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get cluster resource summary.

    :param proxmox_client: Proxmox API client
    :return: List of resource dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.cluster.resources.get()
    except Exception as e:
        logger.warning(f"Could not get cluster resources: {e}")
        return []


@timeit
def get_cluster_config(proxmox_client) -> Any:
    """
    Get cluster configuration including corosync info.

    :param proxmox_client: Proxmox API client
    :return: Cluster config (can be dict or list depending on API response)
    :raises: Exception if API call fails
    """
    try:
        # Get corosync configuration
        return proxmox_client.cluster.config.get()
    except Exception as e:
        logger.warning(f"Could not get cluster config: {e}")
        return {}


@timeit
def get_replication_jobs(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get cluster replication jobs.

    :param proxmox_client: Proxmox API client
    :return: List of replication job dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.cluster.replication.get()
    except Exception as e:
        logger.warning(f"Could not get replication jobs: {e}")
        return []


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# Per docs: Use data['field'] for required, data.get('field') for optional
# ============================================================================


def transform_cluster_data(
    cluster_status: List[Dict[str, Any]],
    proxmox_host: str,
) -> Dict[str, Any]:
    """
    Transform cluster status data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param cluster_status: Raw cluster status from API
    :param proxmox_host: Proxmox hostname for synthetic ID
    :return: Transformed cluster data
    """
    cluster_info = None
    for item in cluster_status:
        # Required field - use direct access
        if item["type"] == "cluster":
            cluster_info = item
            break

    if not cluster_info:
        # Create synthetic cluster ID from hostname
        cluster_id = proxmox_host.replace(".", "-")
        nodes_total = len([i for i in cluster_status if i["type"] == "node"])
        nodes_online = len(
            [i for i in cluster_status if i["type"] == "node" and i.get("online")]
        )
        return {
            "id": cluster_id,
            "name": cluster_id,
            "version": "unknown",
            "quorate": True,
            "nodes_online": nodes_online,
            "nodes_total": nodes_total,
            "cluster_id": None,
        }

    # Per docs: "ID should uniquely identify the node... use API-provided fields for IDs"
    nodes_total = cluster_info.get(
        "nodes", len([i for i in cluster_status if i["type"] == "node"])
    )
    nodes_online = len(
        [i for i in cluster_status if i["type"] == "node" and i.get("online")]
    )

    return {
        "id": cluster_info["name"],  # Required field - direct access
        "name": cluster_info["name"],  # Required
        "version": cluster_info.get("version", "unknown"),  # Optional with default
        "quorate": bool(
            cluster_info.get("quorate", True)
        ),  # Optional with default, convert to bool
        "nodes_online": nodes_online,
        "nodes_total": nodes_total,
        "cluster_id": cluster_info.get("id"),  # Internal cluster ID from API
    }


def transform_cluster_options(cluster_options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform cluster options into additional metadata fields.

    :param cluster_options: Raw cluster options from API
    :return: Dict of transformed cluster option fields
    """
    if not cluster_options:
        return {}

    return {
        # Migration settings
        "migration_type": cluster_options.get("migration"),
        "migration_network": cluster_options.get("migration_network"),
        "migration_bandwidth_limit": cluster_options.get("bwlimit"),
        # Console settings
        "console": cluster_options.get("console"),
        # Email/notification settings
        "email_from": cluster_options.get("email_from"),
        "http_proxy": cluster_options.get("http_proxy"),
        # Keyboard layout
        "keyboard": cluster_options.get("keyboard"),
        # Language
        "language": cluster_options.get("language"),
        # MAC address prefix
        "mac_prefix": cluster_options.get("mac_prefix"),
        # Maximum workers
        "max_workers": cluster_options.get("max_workers"),
        # Next VMID settings
        "next_id_lower": (
            cluster_options.get("next-id", {}).get("lower")
            if isinstance(cluster_options.get("next-id"), dict)
            else None
        ),
        "next_id_upper": (
            cluster_options.get("next-id", {}).get("upper")
            if isinstance(cluster_options.get("next-id"), dict)
            else None
        ),
    }


def transform_cluster_config(cluster_config: Any) -> Dict[str, Any]:
    """
    Transform cluster configuration (corosync) into metadata fields.

    :param cluster_config: Raw cluster config from API (can be list or dict)
    :return: Dict of transformed cluster config fields
    """
    if not cluster_config:
        return {}

    # Proxmox API may return a list - if so, convert to dict
    # The list typically contains configuration section dictionaries
    config_dict = {}
    if isinstance(cluster_config, list):
        # Convert list of config sections to a dict
        for item in cluster_config:
            if isinstance(item, dict) and "section" in item:
                section_name = item.get("section")
                config_dict[section_name] = item
        # If we have a totem section, use it directly
        cluster_config = config_dict

    totem = cluster_config.get("totem", {})

    return {
        # Corosync/Totem configuration
        "totem_interface": totem.get("interface"),
        "totem_cluster_name": totem.get("cluster_name"),
        "totem_config_version": totem.get("config_version"),
        "totem_ip_version": totem.get("ip_version"),
        "totem_secauth": totem.get("secauth"),
        "totem_version": totem.get("version"),
    }


def transform_node_data(
    nodes: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform node data into standard format.

    :param nodes: Raw node data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed node dicts
    """
    transformed_nodes = []

    for node in nodes:
        # Use direct access for required fields, .get() for optional
        transformed_nodes.append(
            {
                "id": node["node"],  # Required - API-provided ID
                "name": node["node"],  # Required
                "cluster_id": cluster_id,  # Required
                "hostname": node["node"],  # Use node name as hostname
                "ip": node.get("ip"),  # Optional
                "status": node.get("status", "unknown"),  # Optional with default
                "uptime": node.get("uptime", 0),  # Optional with default
                "cpu_count": node.get("maxcpu", 0),  # Optional
                "cpu_usage": node.get("cpu", 0.0),  # Optional
                "memory_total": node.get("maxmem", 0),  # Optional
                "memory_used": node.get("mem", 0),  # Optional
                "disk_total": node.get("maxdisk", 0),  # Optional
                "disk_used": node.get("disk", 0),  # Optional
                "level": node.get("level"),  # Optional
                # Additional system info
                "kversion": node.get("kversion"),  # Kernel version
                # Convert loadavg array to comma-separated string
                "loadavg": (
                    ",".join(str(x) for x in node.get("loadavg", []))
                    if node.get("loadavg")
                    else None
                ),
                "wait": node.get("wait"),  # I/O wait time
                # Swap information
                "swap_total": node.get("maxswap"),  # Total swap
                "swap_used": node.get("swap"),  # Used swap
                "swap_free": (
                    node.get("maxswap", 0) - node.get("swap", 0)
                    if node.get("maxswap") and node.get("swap")
                    else None
                ),
                # Additional system info
                "pveversion": node.get("pveversion"),  # PVE version string
                "cpuinfo": node.get("cpuinfo"),  # CPU model
                "idle": node.get("idle"),  # Idle percentage
            }
        )

    return transformed_nodes


def transform_node_network_data(
    network_interfaces: List[Dict[str, Any]],
    node_name: str,
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform node network interface data into standard format.

    :param network_interfaces: Raw network interface data from API
    :param node_name: Node name
    :param cluster_id: Parent cluster ID
    :return: List of transformed network interface dicts
    """
    transformed_interfaces = []

    for iface in network_interfaces:
        # Required field
        iface_name = iface["iface"]
        iface_id = f"{node_name}:{iface_name}"

        transformed_interfaces.append(
            {
                "id": iface_id,
                "name": iface_name,
                "node_name": node_name,
                "type": iface.get("type"),  # bridge, bond, eth, vlan, etc.
                "address": iface.get("address"),
                "netmask": iface.get("netmask"),
                "gateway": iface.get("gateway"),
                "address6": iface.get("address6"),
                "netmask6": iface.get("netmask6"),
                "gateway6": iface.get("gateway6"),
                "bridge_ports": iface.get("bridge_ports"),
                "bond_slaves": iface.get("slaves"),  # API uses 'slaves' key
                "active": iface.get("active", False),
                "autostart": iface.get("autostart", False),
                "mtu": iface.get("mtu"),
                # Additional bond configuration
                "bond_mode": iface.get("bond_mode"),
                "bond_xmit_hash_policy": iface.get("bond_xmit_hash_policy"),
                # Additional network configuration
                "cidr": iface.get("cidr"),
                "cidr6": iface.get("cidr6"),
                "method": iface.get("method"),
                "method6": iface.get("method6"),
                "comments": iface.get("comments"),
            }
        )

    return transformed_interfaces


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# Per AGENTS.md: Use load() function with data model schemas
# ============================================================================


def load_cluster(neo4j_session, cluster_data: Dict[str, Any], update_tag: int) -> None:
    """
    Load cluster data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param cluster_data: Transformed cluster data
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxClusterSchema(),
        [cluster_data],
        lastupdated=update_tag,
    )


def load_nodes(
    neo4j_session, nodes: List[Dict[str, Any]], cluster_id: str, update_tag: int
) -> None:
    """
    Load node data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param nodes: List of transformed node dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxNodeSchema(),
        nodes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_node_networks(
    neo4j_session,
    network_interfaces: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load node network interface data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param network_interfaces: List of transformed network interface dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not network_interfaces:
        return

    from cartography.models.proxmox.cluster import ProxmoxNodeNetworkInterfaceSchema

    load(
        neo4j_session,
        ProxmoxNodeNetworkInterfaceSchema(),
        network_interfaces,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# Per docs: "sync should call get, then load, and finally cleanup"
# ============================================================================


@timeit
def sync(
    neo4j_session,
    proxmox_client,
    proxmox_host: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Sync cluster and node data.

    Follows Cartography's Get → Transform → Load pattern.
    Cleanup is handled in separate cleanup job.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param proxmox_host: Proxmox hostname
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    :return: Cluster data dict with cluster_id
    """
    logger.info("Syncing Proxmox cluster and nodes")

    # GET - retrieve data from API
    cluster_status = get_cluster_status(proxmox_client)
    nodes = get_nodes(proxmox_client)
    cluster_options = get_cluster_options(proxmox_client)
    cluster_config = get_cluster_config(proxmox_client)

    # TRANSFORM - manipulate data for ingestion
    cluster_data = transform_cluster_data(cluster_status, proxmox_host)

    # Merge additional cluster metadata
    cluster_data.update(transform_cluster_options(cluster_options))
    cluster_data.update(transform_cluster_config(cluster_config))

    transformed_nodes = transform_node_data(nodes, cluster_data["id"])

    # LOAD - ingest to Neo4j
    load_cluster(neo4j_session, cluster_data, update_tag)
    load_nodes(neo4j_session, transformed_nodes, cluster_data["id"], update_tag)

    # Sync node network interfaces
    all_node_networks = []
    for node in nodes:
        node_name = node["node"]
        # GET network config for this node
        network_interfaces = get_node_network(proxmox_client, node_name)
        # TRANSFORM network data
        transformed_networks = transform_node_network_data(
            network_interfaces,
            node_name,
            cluster_data["id"],
        )
        all_node_networks.extend(transformed_networks)

    # LOAD node network interfaces
    if all_node_networks:
        load_node_networks(
            neo4j_session, all_node_networks, cluster_data["id"], update_tag
        )
        logger.info(
            f"Synced {len(all_node_networks)} network interfaces across {len(nodes)} nodes"
        )

    # CLEANUP - remove stale data
    # Add CLUSTER_ID to parameters for cleanup jobs
    cleanup_params = {**common_job_parameters, "CLUSTER_ID": cluster_data["id"]}
    cleanup(neo4j_session, cleanup_params)

    logger.info(
        f"Synced cluster {cluster_data['id']} with {len(transformed_nodes)} nodes"
    )

    return {"cluster_id": cluster_data["id"]}


def cleanup(neo4j_session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale cluster, node, and network interface data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters including UPDATE_TAG and CLUSTER_ID
    """
    # Cleanup nodes
    GraphJob.from_node_schema(ProxmoxNodeSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Cleanup node network interfaces
    GraphJob.from_node_schema(
        ProxmoxNodeNetworkInterfaceSchema(), common_job_parameters
    ).run(neo4j_session)
