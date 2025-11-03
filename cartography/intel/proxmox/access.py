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
def get_users(proxmox_client) -> list[dict[str, Any]]:
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
def get_groups(proxmox_client) -> list[dict[str, Any]]:
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
def get_roles(proxmox_client) -> list[dict[str, Any]]:
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
def get_acls(proxmox_client) -> list[dict[str, Any]]:
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
        userid = user['userid']

        # Parse groups if they exist
        groups = []
        if user.get('groups'):
            groups = [g.strip() for g in user.get('groups', '').split(',') if g.strip()]

        # Parse tokens if they exist (tokens field contains list)
        tokens = user.get('tokens', [])

        transformed_users.append({
            'id': userid,
            'userid': userid,
            'cluster_id': cluster_id,
            'enable': user.get('enable', True),
            'expire': user.get('expire', 0),
            'firstname': user.get('firstname'),
            'lastname': user.get('lastname'),
            'email': user.get('email'),
            'comment': user.get('comment'),
            'groups': groups,
            'tokens': tokens,
        })

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
        groupid = group['groupid']

        transformed_groups.append({
            'id': groupid,
            'groupid': groupid,
            'cluster_id': cluster_id,
            'comment': group.get('comment'),
        })

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
        roleid = role['roleid']

        # Parse privileges
        privs = []
        if role.get('privs'):
            privs = [p.strip() for p in role.get('privs', '').split(',') if p.strip()]

        transformed_roles.append({
            'id': roleid,
            'roleid': roleid,
            'cluster_id': cluster_id,
            'privs': privs,
            'special': role.get('special', False),
        })

    return transformed_roles


def transform_acl_data(
    acls: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform ACL data into standard format.

    :param acls: Raw ACL data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed ACL dicts
    """
    transformed_acls = []

    for acl in acls:
        # Required fields
        path = acl['path']
        roleid = acl['roleid']
        ugid = acl['ugid']  # User or group ID

        # Create unique ID from path + ugid + roleid
        acl_id = f"{path}:{ugid}:{roleid}"

        transformed_acls.append({
            'id': acl_id,
            'path': path,
            'cluster_id': cluster_id,
            'roleid': roleid,
            'ugid': ugid,
            'propagate': acl.get('propagate', True),
        })

    return transformed_acls


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================

def load_users(
    neo4j_session,
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
    neo4j_session,
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
    neo4j_session,
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
    neo4j_session,
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


def load_user_group_relationships(
    neo4j_session,
    users: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between users and their groups.

    :param neo4j_session: Neo4j session
    :param users: List of user dicts with group memberships
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query
    
    # Flatten user -> groups into individual relationships
    user_groups = []
    for user in users:
        for group in user.get('groups', []):
            user_groups.append({
                'userid': user['userid'],
                'groupid': group,
            })

    if not user_groups:
        return

    query = """
    UNWIND $UserGroups as ug
    MATCH (u:ProxmoxUser{userid: ug.userid})
    MATCH (g:ProxmoxGroup{groupid: ug.groupid})
    MERGE (u)-[r:MEMBER_OF_GROUP]->(g)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        UserGroups=user_groups,
        UpdateTag=update_tag,
    )


def load_acl_principal_relationships(
    neo4j_session,
    acls: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between ACLs and users/groups they apply to.

    :param neo4j_session: Neo4j session
    :param acls: List of ACL dicts
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import run_write_query
    
    if not acls:
        return

    # Separate user ACLs from group ACLs based on ugid format
    # Users have @ in their ID, groups don't
    user_acls = [acl for acl in acls if '@' in acl['ugid']]
    group_acls = [acl for acl in acls if '@' not in acl['ugid']]

    # Create relationships to users
    if user_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (u:ProxmoxUser{userid: acl.ugid})
        MERGE (a)-[r:APPLIES_TO_USER]->(u)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=user_acls,
            UpdateTag=update_tag,
        )

    # Create relationships to groups
    if group_acls:
        query = """
        UNWIND $ACLs as acl
        MATCH (a:ProxmoxACL{id: acl.id})
        MATCH (g:ProxmoxGroup{groupid: acl.ugid})
        MERGE (a)-[r:APPLIES_TO_GROUP]->(g)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        """
        run_write_query(
            neo4j_session,
            query,
            ACLs=group_acls,
            UpdateTag=update_tag,
        )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================

@timeit
def sync(
    neo4j_session,
    proxmox_client,
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
        load_users(neo4j_session, transformed_users, cluster_id, update_tag)
        load_user_group_relationships(neo4j_session, transformed_users, update_tag)

    if transformed_roles:
        load_roles(neo4j_session, transformed_roles, cluster_id, update_tag)

    if transformed_acls:
        load_acls(neo4j_session, transformed_acls, cluster_id, update_tag)
        load_acl_principal_relationships(neo4j_session, transformed_acls, update_tag)

    logger.info(
        f"Synced {len(transformed_users)} users, {len(transformed_groups)} groups, "
        f"{len(transformed_roles)} roles, and {len(transformed_acls)} ACLs"
    )
