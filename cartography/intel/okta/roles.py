# Okta intel module - Roles
import json
import logging
from typing import Any

import neo4j
from okta.framework.ApiClient import ApiClient

from cartography.client.core.tx import load
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.models.okta.role import OktaAdministrationRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_user_roles(api_client: ApiClient, user_id: str) -> str:
    """
    Get user roles from Okta
    :param api_client: api client
    :param user_id: user to fetch roles from
    :return: user roles data
    """
    # https://developer.okta.com/docs/reference/api/roles/#list-roles
    response = api_client.get_path(f"/users/{user_id}/roles")
    check_rate_limit(response)

    print(response.text)

    return response.text


@timeit
def _get_group_roles(api_client: ApiClient, group_id: str) -> str:
    """
    Get user roles from Okta
    :param api_client: api client
    :param group_id: user to fetch roles from
    :return: group roles dat
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles-assigned-to-group
    response = api_client.get_path(f"/groups/{group_id}/roles")
    check_rate_limit(response)
    return response.text


@timeit
def transform_user_roles_data(data: str, okta_org_id: str) -> list[dict]:
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
def transform_group_roles_data(data: str, okta_org_id: str) -> list[dict]:
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
def _aggregate_roles_by_type(
    user_roles: dict[str, list[dict]],
    group_roles: dict[str, list[dict]],
) -> list[dict[str, Any]]:
    """
    Aggregate roles by type with their associated users and groups
    :param user_roles: dict mapping user_id to their roles
    :param group_roles: dict mapping group_id to their roles
    :return: list of role objects with users and groups lists
    """
    roles_by_type: dict[str, dict[str, Any]] = {}

    # Process user roles
    for user_id, roles in user_roles.items():
        for role in roles:
            role_type = role["type"]
            if role_type not in roles_by_type:
                roles_by_type[role_type] = {
                    "type": role_type,
                    "label": role["label"],
                    "users": [],
                    "groups": [],
                }
            roles_by_type[role_type]["users"].append(user_id)

    # Process group roles
    for group_id, roles in group_roles.items():
        for role in roles:
            role_type = role["type"]
            if role_type not in roles_by_type:
                roles_by_type[role_type] = {
                    "type": role_type,
                    "label": role["label"],
                    "users": [],
                    "groups": [],
                }
            roles_by_type[role_type]["groups"].append(group_id)

    return list(roles_by_type.values())


@timeit
def _load_roles(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    roles_data: list[dict],
    okta_update_tag: int,
) -> None:
    """
    Load roles with their user and group relationships
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param roles_data: list of role objects with users and groups
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaAdministrationRoleSchema(),
        roles_data,
        lastupdated=okta_update_tag,
        ORG_ID=okta_org_id,
    )


@timeit
def sync_roles(
    neo4j_session: str,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
    users_id: list[str],
    groups_id: list[str],
) -> None:
    """
    Sync okta roles
    :param neo4j_session: Neo4j Session
    :param okta_org_id: Okta organization id
    :param okta_update_tag: Update tag
    :param okta_api_key: Okta API key
    :param users_id: List of user ids
    :param groups_id: List of group ids
    :return: None
    """

    logger.info("Syncing Okta Roles")

    # Get API client
    api_client = create_api_client(okta_org_id, "/api/v1/users", okta_api_key)

    # Fetch roles for all users
    user_roles_map: dict[str, list[dict]] = {}
    for user_id in users_id:
        user_roles_data = _get_user_roles(api_client, user_id)
        user_roles = transform_user_roles_data(user_roles_data, okta_org_id)
        if len(user_roles) > 0:
            user_roles_map[user_id] = user_roles

    # Fetch roles for all groups
    group_roles_map: dict[str, list[dict]] = {}
    for group_id in groups_id:
        group_roles_data = _get_group_roles(api_client, group_id)
        group_roles = transform_group_roles_data(group_roles_data, okta_org_id)
        if len(group_roles) > 0:
            group_roles_map[group_id] = group_roles

    # Aggregate roles by type with their associated users and groups
    aggregated_roles = _aggregate_roles_by_type(user_roles_map, group_roles_map)

    # Load roles into the graph
    if aggregated_roles:
        _load_roles(neo4j_session, okta_org_id, aggregated_roles, okta_update_tag)
