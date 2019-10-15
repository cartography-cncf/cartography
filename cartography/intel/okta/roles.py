# Okta intel module - Roles
import json
import logging

from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import get_okta_groups_id_from_graph
from cartography.intel.okta.utils import get_user_id_from_graph

logger = logging.getLogger(__name__)


def _get_user_roles(api_client, user_id, okta_org_id):
    """
    Get user roles from Okta
    :param api_client: api client
    :param user_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: user roles data
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles
    response = api_client.get_path(f'/{user_id}/roles')

    return response.text


def _get_group_roles(api_client, group_id, okta_org_id):
    """
    Get user roles from Okta
    :param api_client: api client
    :param group_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: group roles data
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles-assigned-to-group
    response = api_client.get_path(f'/{group_id}/roles')

    return response.text


def transform_user_roles_data(data, okta_org_id):
    """
    Transform user role data
    :param data: data returned by Okta server
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """
    role_data = json.loads(data)

    user_roles = []

    for role in role_data:
        role_props = {}
        role_props["label"] = role["label"]
        role_props["type"] = role["type"]
        role_props["id"] = "{}-{}".format(okta_org_id, role["type"])

        user_roles.append(role_props)

    return user_roles


def transform_group_roles_data(data, okta_org_id):
    """
    Transform user role data
    :param data: data returned by Okta server
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """
    role_data = json.loads(data)

    user_roles = []

    for role in role_data:
        role_props = {}
        role_props["label"] = role["label"]
        role_props["type"] = role["type"]
        role_props["id"] = "{}-{}".format(okta_org_id, role["type"])

        user_roles.append(role_props)

    return user_roles


def _load_user_role(neo4j_session, user_id, roles_data, okta_update_tag):
    ingest = """
    MATCH (user:OktaUser{id: {USER_ID}})<-[:RESOURCE]-(org:OktaOrganization)
    WITH user,org
    UNWIND {ROLES_DATA} as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = {okta_update_tag}
    WITH user, role_node, org
    MERGE (user)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        USER_ID=user_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


def _load_group_role(neo4j_session, group_id, roles_data, okta_update_tag):
    ingest = """
    MATCH (group:OktaGroup{id: {GROUP_ID}})<-[:RESOURCE]-(org:OktaOrganization)
    WITH group,org
    UNWIND {ROLES_DATA} as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = {okta_update_tag}
    WITH group, role_node, org
    MERGE (group)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        GROUP_ID=group_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


def sync_roles(neo4j_session, okta_org_id, okta_update_tag, okta_api_key):
    """
    Sync okta roles
    :param neo4j_session: Neo4j Session
    :param okta_org_id: Okta organization id
    :param okta_update_tag: Update tag
    :param okta_api_key: Okta API key
    :return: None
    """
    logger.debug("Syncing Okta Roles")

    # get API client
    api_client = create_api_client(okta_org_id, "/api/v1/users", okta_api_key)

    # users
    users = get_user_id_from_graph(neo4j_session, okta_org_id)

    for user_id in users:
        user_roles_data = _get_user_roles(api_client, user_id, okta_org_id)
        user_roles = transform_user_roles_data(user_roles_data, okta_org_id)
        if len(user_roles) > 0:
            _load_user_role(neo4j_session, user_id, user_roles, okta_update_tag)

    # groups
    groups = get_okta_groups_id_from_graph(neo4j_session, okta_org_id)

    for group_id in groups:
        group_roles_data = _get_group_roles(api_client, group_id, okta_org_id)
        group_roles = transform_group_roles_data(group_roles_data, okta_org_id)
        if len(group_roles) > 0:
            _load_group_role(neo4j_session, group_id, group_roles, okta_update_tag)
