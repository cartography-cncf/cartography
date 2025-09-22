# Okta intel module - Roles
import json
import logging
from typing import Dict
from typing import List

import neo4j
from okta.framework.ApiClient import ApiClient

from cartography.client.core.tx import run_write_query
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_user_roles(api_client: ApiClient, user_id: str, okta_org_id: str) -> str:
    """
    Get user roles from Okta
    :param api_client: api client
    :param user_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: user roles data
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles
    response = api_client.get_path(f"/{user_id}/roles")
    check_rate_limit(response)
    return response.text


@timeit
def _get_group_roles(api_client: ApiClient, group_id: str, okta_org_id: str) -> str:
    """
    Get user roles from Okta
    :param api_client: api client
    :param group_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: group roles data
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles-assigned-to-group
    response = api_client.get_path(f"/{group_id}/roles")
    check_rate_limit(response)
    return response.text


@timeit
def transform_user_roles_data(data: str, okta_org_id: str) -> List[Dict]:
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


@timeit
def transform_group_roles_data(data: str, okta_org_id: str) -> List[Dict]:
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


@timeit
def _load_user_role(
    neo4j_session: neo4j.Session,
    user_id: str,
    roles_data: List[Dict],
    okta_update_tag: int,
) -> None:
    ingest = """
    MATCH (user:OktaUser{id: $USER_ID})<-[:RESOURCE]-(org:OktaOrganization)
    WITH user,org
    UNWIND $ROLES_DATA as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = $okta_update_tag
    WITH user, role_node, org
    MERGE (user)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        USER_ID=user_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_group_role(
    neo4j_session: neo4j.Session,
    group_id: str,
    roles_data: List[Dict],
    okta_update_tag: int,
) -> None:
    ingest = """
    MATCH (group:OktaGroup{id: $GROUP_ID})<-[:RESOURCE]-(org:OktaOrganization)
    WITH group,org
    UNWIND $ROLES_DATA as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = $okta_update_tag
    WITH group, role_node, org
    MERGE (group)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        GROUP_ID=group_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


@timeit
def sync_roles(
    neo4j_session: str,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
    sync_state: OktaSyncState,
) -> None:
    """
    Sync okta roles
    :param neo4j_session: Neo4j Session
    :param okta_org_id: Okta organization id
    :param okta_update_tag: Update tag
    :param okta_api_key: Okta API key
    :param sync_state: Okta sync state
    :return: None
    """

    logger.info("Syncing Okta Roles")

    # get API client
    api_client = create_api_client(okta_org_id, "/api/v1/users", okta_api_key)

    if sync_state.users:
        for user_id in sync_state.users:
            user_roles_data = _get_user_roles(api_client, user_id, okta_org_id)
            user_roles = transform_user_roles_data(user_roles_data, okta_org_id)
            if len(user_roles) > 0:
                _load_user_role(neo4j_session, user_id, user_roles, okta_update_tag)

    if sync_state.groups:
        for group_id in sync_state.groups:
            group_roles_data = _get_group_roles(api_client, group_id, okta_org_id)
            group_roles = transform_group_roles_data(group_roles_data, okta_org_id)
            if len(group_roles) > 0:
                _load_group_role(neo4j_session, group_id, group_roles, okta_update_tag)
