"""
Sync Proxmox firewall configurations.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.firewall import ProxmoxFirewallIPSetSchema
from cartography.models.proxmox.firewall import ProxmoxFirewallRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_cluster_firewall_rules(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get cluster-level firewall rules.

    :param proxmox_client: Proxmox API client
    :return: List of firewall rule dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.rules.get()


@timeit
def get_node_firewall_rules(
    proxmox_client: Any, node_name: str
) -> list[dict[str, Any]]:
    """
    Get node-level firewall rules.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of firewall rule dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).firewall.rules.get()


@timeit
def get_vm_firewall_rules(
    proxmox_client: Any, node_name: str, vmid: int
) -> list[dict[str, Any]]:
    """
    Get VM-level firewall rules.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :param vmid: VM ID
    :return: List of firewall rule dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).qemu(vmid).firewall.rules.get()


@timeit
def get_cluster_ipsets(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get cluster-level IP sets.

    :param proxmox_client: Proxmox API client
    :return: List of IP set dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.ipset.get()


@timeit
def get_ipset_cidrs(proxmox_client: Any, ipset_name: str) -> list[dict[str, Any]]:
    """
    Get CIDR entries for a specific IP set.

    :param proxmox_client: Proxmox API client
    :param ipset_name: IP set name
    :return: List of CIDR entry dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.ipset(ipset_name).get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_firewall_rule_data(
    rules: list[dict[str, Any]],
    cluster_id: str,
    scope: str,
    scope_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform firewall rule data into standard format.

    :param rules: Raw firewall rule data from API
    :param cluster_id: Parent cluster ID
    :param scope: Rule scope (cluster, node, vm)
    :param scope_id: Scope identifier (node name or vmid)
    :return: List of transformed firewall rule dicts
    """
    transformed_rules = []

    for rule in rules:
        # Create unique ID based on scope and position
        if scope_id:
            rule_id = f"{scope}:{scope_id}:{rule.get('pos', 0)}"
        else:
            rule_id = f"{scope}:{rule.get('pos', 0)}"

        transformed_rules.append(
            {
                "id": rule_id,
                "cluster_id": cluster_id,
                "scope": scope,
                "scope_id": scope_id,
                "pos": rule.get("pos", 0),
                "type": rule.get("type"),
                "action": rule.get("action"),
                "enable": bool(rule.get("enable", True)),  # Convert to bool
                "iface": rule.get("iface"),
                "source": rule.get("source"),
                "dest": rule.get("dest"),
                "proto": rule.get("proto"),
                "sport": rule.get("sport"),
                "dport": rule.get("dport"),
                "comment": rule.get("comment"),
                "macro": rule.get("macro"),
                "log": rule.get("log"),
            }
        )

    return transformed_rules


def transform_ipset_data(
    ipsets: list[dict[str, Any]],
    ipset_cidrs: dict[str, list[dict[str, Any]]],
    cluster_id: str,
    scope: str,
    scope_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform IP set data into standard format.

    :param ipsets: Raw IP set data from API
    :param ipset_cidrs: Map of ipset name -> CIDR entries
    :param cluster_id: Parent cluster ID
    :param scope: IP set scope (cluster, node, vm)
    :param scope_id: Scope identifier
    :return: List of transformed IP set dicts
    """
    transformed_ipsets = []

    for ipset in ipsets:
        # Required field
        name = ipset["name"]

        # Create unique ID based on scope
        if scope_id:
            ipset_id = f"{scope}:{scope_id}:{name}"
        else:
            ipset_id = f"{scope}:{name}"

        # Get CIDR entries for this IP set
        cidrs = []
        for cidr_entry in ipset_cidrs.get(name, []):
            if "cidr" in cidr_entry:
                cidrs.append(cidr_entry["cidr"])

        transformed_ipsets.append(
            {
                "id": ipset_id,
                "name": name,
                "cluster_id": cluster_id,
                "scope": scope,
                "scope_id": scope_id,
                "comment": ipset.get("comment"),
                "cidrs": cidrs,
            }
        )

    return transformed_ipsets


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_firewall_rules(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load firewall rule data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param rules: List of transformed firewall rule dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not rules:
        return

    load(
        neo4j_session,
        ProxmoxFirewallRuleSchema(),
        rules,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_ipsets(
    neo4j_session: neo4j.Session,
    ipsets: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load IP set data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param ipsets: List of transformed IP set dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not ipsets:
        return

    load(
        neo4j_session,
        ProxmoxFirewallIPSetSchema(),
        ipsets,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_firewall_scope_relationships(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between firewall rules and their scope (node or VM).

    :param neo4j_session: Neo4j session
    :param rules: List of firewall rule dicts
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query

    # Separate rules by scope
    node_rules = [r for r in rules if r["scope"] == "node" and r["scope_id"]]
    vm_rules = [r for r in rules if r["scope"] == "vm" and r["scope_id"]]

    # Create relationships to nodes
    if node_rules:
        query = """
        UNWIND $Rules as rule
        MATCH (fr:ProxmoxFirewallRule{id: rule.id})
        MATCH (n:ProxmoxNode{id: rule.scope_id})
        MERGE (fr)-[r:APPLIES_TO_NODE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            Rules=node_rules,
            UpdateTag=update_tag,
        )

    # Create relationships to VMs
    if vm_rules:
        # Convert scope_id to int for VM matching
        for rule in vm_rules:
            if rule["scope_id"]:
                try:
                    rule["vmid_int"] = int(rule["scope_id"])
                except ValueError:
                    pass

        query = """
        UNWIND $Rules as rule
        MATCH (fr:ProxmoxFirewallRule{id: rule.id})
        MATCH (v:ProxmoxVM{vmid: rule.vmid_int})
        MERGE (fr)-[r:APPLIES_TO_VM]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            Rules=vm_rules,
            UpdateTag=update_tag,
        )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync firewall configuration.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox firewall configuration")

    all_rules = []
    all_ipsets = []

    # GET - Cluster-level firewall rules
    cluster_rules = get_cluster_firewall_rules(proxmox_client)
    transformed_cluster_rules = transform_firewall_rule_data(
        cluster_rules, cluster_id, "cluster"
    )
    all_rules.extend(transformed_cluster_rules)

    # GET - Cluster-level IP sets
    cluster_ipsets = get_cluster_ipsets(proxmox_client)
    ipset_cidrs = {}
    for ipset in cluster_ipsets:
        ipset_name = ipset["name"]
        cidrs = get_ipset_cidrs(proxmox_client, ipset_name)
        ipset_cidrs[ipset_name] = cidrs

    transformed_ipsets = transform_ipset_data(
        cluster_ipsets, ipset_cidrs, cluster_id, "cluster"
    )
    all_ipsets.extend(transformed_ipsets)

    # GET - Node-level firewall rules
    nodes = proxmox_client.nodes.get()
    for node in nodes:
        node_name = node["node"]
        node_rules = get_node_firewall_rules(proxmox_client, node_name)
        transformed_node_rules = transform_firewall_rule_data(
            node_rules, cluster_id, "node", node_name
        )
        all_rules.extend(transformed_node_rules)

    # GET - VM-level firewall rules (sample only to avoid excessive API calls)
    # In production, you might want to limit this or make it configurable
    logger.debug("Skipping VM-level firewall rules to avoid excessive API calls")

    # LOAD - ingest to Neo4j
    load_firewall_rules(neo4j_session, all_rules, cluster_id, update_tag)
    load_ipsets(neo4j_session, all_ipsets, cluster_id, update_tag)

    if all_rules:
        load_firewall_scope_relationships(neo4j_session, all_rules, update_tag)

    logger.info(f"Synced {len(all_rules)} firewall rules and {len(all_ipsets)} IP sets")
