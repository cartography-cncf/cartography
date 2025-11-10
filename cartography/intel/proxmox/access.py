"""
Sync Proxmox access control (users, groups, roles, ACLs).

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

from cartography.client.core.tx import load
from cartography.models.proxmox.access import ProxmoxACLSchema
from cartography.models.proxmox.access import ProxmoxGroupSchema
from cartography.models.proxmox.access import ProxmoxRoleSchema
from cartography.models.proxmox.access import ProxmoxUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_users(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all users in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of user dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.access.users.get()
    except Exception as e:
        logger.warning(f"Could not get users: {e}")
        return []


@timeit
def get_groups(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all groups in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of group dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.access.groups.get()
    except Exception as e:
        logger.warning(f"Could not get groups: {e}")
        return []


@timeit
def get_roles(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all roles in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of role dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.access.roles.get()
    except Exception as e:
        logger.warning(f"Could not get roles: {e}")
        return []


@timeit
def get_acls(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all ACL entries in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of ACL dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.access.acl.get()
    except Exception as e:
        logger.warning(f"Could not get ACLs: {e}")
        return []


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_user_data(
    users: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform user data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param users: Raw user data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed user dicts
    """
    transformed_users = []

    for user in users:
        # Required field - use direct access
        userid = user["userid"]

        # Parse groups if they exist
        groups = []
        if user.get("groups"):
            groups = [g.strip() for g in user.get("groups", "").split(",") if g.strip()]

        # Parse tokens if they exist (tokens field contains list)
        tokens = user.get("tokens", [])

        transformed_users.append(
            {
                "id": userid,
                "userid": userid,
                "cluster_id": cluster_id,
                "enable": bool(user.get("enable", True)),
                "expire": user.get("expire", 0),
                "firstname": user.get("firstname"),
                "lastname": user.get("lastname"),
                "email": user.get("email"),
                "comment": user.get("comment"),
                "groups": groups,
                "tokens": tokens,
            }
        )

    return transformed_users


def transform_group_data(
    groups: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform group data into standard format.

    :param groups: Raw group data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed group dicts
    """
    transformed_groups = []

    for group in groups:
        # Required field
        groupid = group["groupid"]

        transformed_groups.append(
            {
                "id": groupid,
                "groupid": groupid,
                "cluster_id": cluster_id,
                "comment": group.get("comment"),
            }
        )

    return transformed_groups


def transform_role_data(
    roles: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform role data into standard format.

    :param roles: Raw role data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed role dicts
    """
    transformed_roles = []

    for role in roles:
        # Required field
        roleid = role["roleid"]

        # Parse privileges
        privs = []
        if role.get("privs"):
            privs = [p.strip() for p in role.get("privs", "").split(",") if p.strip()]

        transformed_roles.append(
            {
                "id": roleid,
                "roleid": roleid,
                "cluster_id": cluster_id,
                "privs": privs,
                "special": bool(role.get("special", False)),
            }
        )

    return transformed_roles


def _parse_acl_path(path: str) -> tuple[str, str | None]:
    """
    Parse Proxmox ACL path to determine resource type and ID.

    Proxmox ACL paths follow patterns:
    - "/" = entire cluster
    - "/vms/<vmid>" = specific VM
    - "/storage/<storage_id>" = specific storage
    - "/pool/<pool_id>" = specific pool
    - "/nodes/<node_name>" = specific node
    - "/access" = access control itself

    :param path: ACL path
    :return: Tuple of (resource_type, resource_id)
    """
    if path == "/":
        return "cluster", None
    elif path.startswith("/vms/"):
        return "vm", path.split("/")[-1]
    elif path.startswith("/storage/"):
        return "storage", path.split("/")[-1]
    elif path.startswith("/pool/"):
        return "pool", path.split("/")[-1]
    elif path.startswith("/nodes/"):
        return "node", path.split("/")[-1]
    elif path.startswith("/access"):
        return "access", None
    else:
        # Unknown path format
        return "unknown", None


def transform_acl_data(
    acls: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform ACL data into standard format.

    Parses ACL paths to determine resource types and IDs for better relationship mapping.

    :param acls: Raw ACL data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed ACL dicts
    """
    transformed_acls = []

    for acl in acls:
        # Required fields
        path = acl["path"]
        roleid = acl["roleid"]
        ugid = acl["ugid"]  # User or group ID

        # Create unique ID from path + ugid + roleid
        acl_id = f"{path}:{ugid}:{roleid}"

        # Determine principal type (user has @, group doesn't)
        principal_type = "user" if "@" in ugid else "group"

        # Parse path to extract resource type and ID
        resource_type, resource_id = _parse_acl_path(path)

        transformed_acls.append(
            {
                "id": acl_id,
                "path": path,
                "cluster_id": cluster_id,
                "roleid": roleid,
                "ugid": ugid,
                "propagate": bool(acl.get("propagate", True)),
                "principal_type": principal_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

    return transformed_acls


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_users(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    users: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load user data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param users: List of transformed user dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxUserSchema(),
        users,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_groups(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    groups: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load group data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param groups: List of transformed group dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxGroupSchema(),
        groups,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_roles(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    roles: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load role data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param roles: List of transformed role dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxRoleSchema(),
        roles,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_acls(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    acls: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load ACL data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param acls: List of transformed ACL dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxACLSchema(),
        acls,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )





def load_acl_principal_relationships(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    acls: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between ACLs and users/groups they apply to.

    Includes rich metadata about the permission scope and propagation.

    :param neo4j_session: Neo4j session
    :param acls: List of ACL dicts
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query

    if not acls:
        return

    # Separate user ACLs from group ACLs based on principal_type
    user_acls = [acl for acl in acls if acl["principal_type"] == "user"]
    group_acls = [acl for acl in acls if acl["principal_type"] == "group"]

    # Create relationships to users with rich metadata
    if user_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (u:ProxmoxUser{userid: acl.ugid})
        MERGE (a)-[r:APPLIES_TO_USER]->(u)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.path = acl.path,
            r.propagate = acl.propagate,
            r.resource_type = acl.resource_type
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=user_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to groups with rich metadata
    if group_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (g:ProxmoxGroup{groupid: acl.ugid})
        MERGE (a)-[r:APPLIES_TO_GROUP]->(g)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.path = acl.path,
            r.propagate = acl.propagate,
            r.resource_type = acl.resource_type
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=group_acls,
            UpdateTag=update_tag,
        )


def load_acl_resource_relationships(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    acls: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between ACLs and the resources they grant permissions to.

    Maps ACL paths to actual resource nodes (VMs, storage, pools, nodes).

    :param neo4j_session: Neo4j session
    :param acls: List of ACL dicts
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query

    if not acls:
        return

    # Group ACLs by resource type
    vm_acls = [acl for acl in acls if acl["resource_type"] == "vm" and acl["resource_id"]]
    storage_acls = [acl for acl in acls if acl["resource_type"] == "storage" and acl["resource_id"]]
    pool_acls = [acl for acl in acls if acl["resource_type"] == "pool" and acl["resource_id"]]
    node_acls = [acl for acl in acls if acl["resource_type"] == "node" and acl["resource_id"]]
    cluster_acls = [acl for acl in acls if acl["resource_type"] == "cluster"]

    # Create relationships to VMs
    if vm_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (v:ProxmoxVM{vmid: toInteger(acl.resource_id)})
        MERGE (a)-[r:GRANTS_ACCESS_TO]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.propagate = acl.propagate,
            r.path = acl.path
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=vm_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to storage
    if storage_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (s:ProxmoxStorage{id: acl.resource_id})
        MERGE (a)-[r:GRANTS_ACCESS_TO]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.propagate = acl.propagate,
            r.path = acl.path
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=storage_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to pools
    if pool_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (p:ProxmoxPool{poolid: acl.resource_id})
        MERGE (a)-[r:GRANTS_ACCESS_TO]->(p)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.propagate = acl.propagate,
            r.path = acl.path
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=pool_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to nodes
    if node_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (n:ProxmoxNode{id: acl.resource_id})
        MERGE (a)-[r:GRANTS_ACCESS_TO]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.propagate = acl.propagate,
            r.path = acl.path
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=node_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to cluster (root level permissions)
    if cluster_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (c:ProxmoxCluster{id: acl.cluster_id})
        MERGE (a)-[r:GRANTS_ACCESS_TO]->(c)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.propagate = acl.propagate,
            r.path = acl.path
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=cluster_acls,
            UpdateTag=update_tag,
        )


def load_effective_permissions(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    update_tag: int,
) -> None:
    """
    Create derived relationships showing effective permissions.

    This creates direct HAS_PERMISSION relationships from users/groups to resources,
    making it easier to query "what can this user access?" or "who can access this VM?"

    :param neo4j_session: Neo4j session
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query

    # Create direct user -> resource permissions (through ACLs)
    query = """
    MATCH (u:ProxmoxUser)<-[:APPLIES_TO_USER]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(role:ProxmoxRole)
    MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR 
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH u, resource, role, acl
    MERGE (u)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = acl.id,
        r.role = role.roleid,
        r.privileges = role.privs,
        r.path = acl.path,
        r.propagate = acl.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)

    # Create group -> resource permissions
    query = """
    MATCH (g:ProxmoxGroup)<-[:APPLIES_TO_GROUP]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(role:ProxmoxRole)
    MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR 
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH g, resource, role, acl
    MERGE (g)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = acl.id,
        r.role = role.roleid,
        r.privileges = role.privs,
        r.path = acl.path,
        r.propagate = acl.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)

    # Create inherited permissions: user -> group -> resource
    query = """
    MATCH (u:ProxmoxUser)-[:MEMBER_OF_GROUP]->(g:ProxmoxGroup)-[gp:HAS_PERMISSION]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR 
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH u, resource, gp
    MERGE (u)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = gp.via_acl,
        r.via_group = true,
        r.role = gp.role,
        r.privileges = gp.privileges,
        r.path = gp.path,
        r.propagate = gp.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: "neo4j.Session",  # type: ignore[name-defined]
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync access control configuration.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox access control (users, groups, roles, ACLs)")

    # GET - retrieve data from API
    users = get_users(proxmox_client)
    groups = get_groups(proxmox_client)
    roles = get_roles(proxmox_client)
    acls = get_acls(proxmox_client)

    # TRANSFORM - manipulate data for ingestion
    transformed_users = transform_user_data(users, cluster_id)
    transformed_groups = transform_group_data(groups, cluster_id)
    transformed_roles = transform_role_data(roles, cluster_id)
    transformed_acls = transform_acl_data(acls, cluster_id)

    # LOAD - ingest to Neo4j
    if transformed_groups:
        load_groups(neo4j_session, transformed_groups, cluster_id, update_tag)

    if transformed_users:
        # User-to-Group relationships are now handled by the schema via one_to_many
        load_users(neo4j_session, transformed_users, cluster_id, update_tag)

    if transformed_roles:
        load_roles(neo4j_session, transformed_roles, cluster_id, update_tag)

    if transformed_acls:
        load_acls(neo4j_session, transformed_acls, cluster_id, update_tag)
        # Create relationships between ACLs and principals (users/groups)
        load_acl_principal_relationships(neo4j_session, transformed_acls, update_tag)
        # Create relationships between ACLs and resources they grant access to
        load_acl_resource_relationships(neo4j_session, transformed_acls, update_tag)

    # Create derived effective permission relationships
    # This makes it easy to query "what can this user access?"
    load_effective_permissions(neo4j_session, update_tag)

    logger.info(
        f"Synced {len(transformed_users)} users, {len(transformed_groups)} groups, "
        f"{len(transformed_roles)} roles, and {len(transformed_acls)} ACLs with full permission graph"
    )
