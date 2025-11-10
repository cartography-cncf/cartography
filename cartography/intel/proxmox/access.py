"""
Sync Proxmox access control (users, groups, roles, ACLs).

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

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
    return proxmox_client.access.users.get()


@timeit
def get_groups(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all groups in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of group dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.access.groups.get()


@timeit
def get_group_members(
    proxmox_client: Any, groups: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """
    Get group membership information for all groups.
    Returns a mapping of group_id -> list of user_ids.

    This is especially important for SSO users whose group memberships
    might not be returned in the user API endpoint.

    :param proxmox_client: Proxmox API client
    :param groups: List of group dicts from get_groups()
    :return: Dict mapping group IDs to lists of member user IDs
    :raises: Exception if API call fails
    """
    group_members: dict[str, list[str]] = {}

    for group in groups:
        groupid = group.get("groupid")
        if not groupid:
            continue

        # Get detailed group info including members
        group_detail = proxmox_client.access.groups(groupid).get()
        members = group_detail.get("members", [])
        if members:
            # Members is a list of user IDs
            group_members[groupid] = members
            logger.debug(f"Group {groupid} has {len(members)} members")

    return group_members


@timeit
def get_roles(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all roles in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of role dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.access.roles.get()


@timeit
def get_acls(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all ACL entries in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of ACL dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.access.acl.get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_user_data(
    users: list[dict[str, Any]],
    cluster_id: str,
    group_members: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform user data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param users: Raw user data from API
    :param cluster_id: Parent cluster ID
    :param group_members: Optional dict mapping group IDs to member user IDs
                         (important for SSO users)
    :return: List of transformed user dicts
    """
    transformed_users = []

    for user in users:
        # Required field - use direct access
        userid = user["userid"]

        # Parse groups if they exist (Proxmox returns comma-separated string)
        groups = []
        groups_str = user.get("groups", "")
        if groups_str:
            groups = [g.strip() for g in groups_str.split(",") if g.strip()]

        # Enrich with group memberships from group_members data (important for SSO users)
        # SSO users often don't have groups in their user record, but groups have member lists
        if group_members:
            for groupid, members in group_members.items():
                if userid in members and groupid not in groups:
                    groups.append(groupid)
                    logger.debug(
                        f"Enriched user {userid} with group {groupid} from group membership data"
                    )

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

        # Parse privileges (Proxmox returns comma-separated string)
        privs = []
        privs_str = role.get("privs", "")
        if privs_str:
            privs = [p.strip() for p in privs_str.split(",") if p.strip()]

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

        # Determine principal type and extract base user ID for tokens
        # Proxmox format: groups don't have @, users are user@realm, tokens are user@realm!tokenname
        if "@" in ugid:
            principal_type = "user"
            # For API tokens (user@realm!token), extract base user (user@realm)
            base_userid = ugid.split("!")[0] if "!" in ugid else ugid
        else:
            principal_type = "group"
            base_userid = ugid

        # Parse path to extract resource type and ID
        resource_type, resource_id = _parse_acl_path(path)

        transformed_acls.append(
            {
                "id": acl_id,
                "path": path,
                "cluster_id": cluster_id,
                "roleid": roleid,
                "ugid": ugid,
                "base_userid": base_userid,  # Base user ID without token suffix
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
    neo4j_session: neo4j.Session,
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
    neo4j_session: neo4j.Session,
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
    neo4j_session: neo4j.Session,
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
    neo4j_session: neo4j.Session,
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
    neo4j_session: neo4j.Session,
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
    # Use base_userid to match users correctly (handles API tokens like user@realm!token)
    if user_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (u:ProxmoxUser{userid: acl.base_userid})
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
    neo4j_session: neo4j.Session,
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
    vm_acls = [
        acl for acl in acls if acl["resource_type"] == "vm" and acl["resource_id"]
    ]
    storage_acls = [
        acl for acl in acls if acl["resource_type"] == "storage" and acl["resource_id"]
    ]
    pool_acls = [
        acl for acl in acls if acl["resource_type"] == "pool" and acl["resource_id"]
    ]
    node_acls = [
        acl for acl in acls if acl["resource_type"] == "node" and acl["resource_id"]
    ]
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
    neo4j_session: neo4j.Session,
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
    neo4j_session: neo4j.Session,
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

    # Get group membership information (important for SSO users)
    group_members = get_group_members(proxmox_client, groups)

    # TRANSFORM - manipulate data for ingestion
    transformed_users = transform_user_data(users, cluster_id, group_members)
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
