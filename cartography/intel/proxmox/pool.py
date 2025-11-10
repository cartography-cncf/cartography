"""
Sync Proxmox resource pools.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.pool import ProxmoxPoolSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_pools(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all resource pools in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of pool dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.pools.get()


@timeit
def get_pool_details(proxmox_client: Any, poolid: str) -> dict[str, Any]:
    """
    Get detailed information about a specific pool.

    :param proxmox_client: Proxmox API client
    :param poolid: Pool ID
    :return: Pool details dict
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.pools(poolid).get()
    except Exception as e:
        logger.warning(f"Could not get details for pool {poolid}: {e}")
        return {}


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_pool_data(
    pools: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform pool data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param pools: Raw pool data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed pool dicts
    """
    transformed_pools = []

    for pool in pools:
        # Required field - use direct access
        poolid = pool["poolid"]

        transformed_pools.append(
            {
                "id": poolid,
                "poolid": poolid,
                "comment": pool.get("comment"),
                "cluster_id": cluster_id,
            }
        )

    return transformed_pools


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_pools(
    neo4j_session: "neo4j.Session",
    pools: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load pool data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param pools: List of transformed pool dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxPoolSchema(),
        pools,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_pool_member_relationships(
    neo4j_session: "neo4j.Session",
    pool_members: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between pools and their member resources (VMs, storage).

    Pool members can include VMs/containers and storage resources.

    :param neo4j_session: Neo4j session
    :param pool_members: List of pool-member mappings
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query

    if not pool_members:
        return

    # Separate VM/container members from storage members
    vm_members = [m for m in pool_members if m["type"] in ("qemu", "lxc")]
    storage_members = [m for m in pool_members if m["type"] == "storage"]

    # Create relationships to VMs/containers
    if vm_members:
        query = """
        UNWIND $Members as member
        MATCH (p:ProxmoxPool{id: member.pool_id})
        MATCH (v:ProxmoxVM{vmid: member.vmid})
        MERGE (p)-[r:CONTAINS_VM]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            Members=vm_members,
            UpdateTag=update_tag,
        )

    # Create relationships to storage
    if storage_members:
        query = """
        UNWIND $Members as member
        MATCH (p:ProxmoxPool{id: member.pool_id})
        MATCH (s:ProxmoxStorage{id: member.storage_id})
        MERGE (p)-[r:CONTAINS_STORAGE]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            Members=storage_members,
            UpdateTag=update_tag,
        )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: "neo4j.Session",
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync pool data.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox resource pools")

    # GET - retrieve data from API
    pools = get_pools(proxmox_client)

    # Collect pool member information
    pool_members = []
    for pool in pools:
        poolid = pool["poolid"]
        details = get_pool_details(proxmox_client, poolid)

        # Extract members from pool details
        if "members" in details:
            for member in details["members"]:
                member_data = {
                    "pool_id": poolid,
                    "type": member.get("type"),
                }

                if member.get("type") in ("qemu", "lxc"):
                    member_data["vmid"] = member.get("vmid")
                elif member.get("type") == "storage":
                    member_data["storage_id"] = member.get("storage")

                pool_members.append(member_data)

    # TRANSFORM - manipulate data for ingestion
    transformed_pools = transform_pool_data(pools, cluster_id)

    # LOAD - ingest to Neo4j
    load_pools(neo4j_session, transformed_pools, cluster_id, update_tag)
    load_pool_member_relationships(neo4j_session, pool_members, update_tag)

    logger.info(
        f"Synced {len(transformed_pools)} resource pools with {len(pool_members)} members"
    )
