# Okta intel module - Group
import json
import logging

import neo4j
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError
from okta.framework.PagedResults import PagedResults
from okta.models.usergroup import UserGroup

from cartography.client.core.tx import load
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.models.okta.group import OktaGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_okta_groups(api_client: ApiClient) -> list[UserGroup]:
    """
    Get groups from Okta server
    :param api_client: Okta api client
    :return: Array of group information
    """
    group_list: list[UserGroup] = []
    next_url = None

    # SDK Bug
    # get_paged_groups returns User object instead of UserGroup

    while True:
        # https://developer.okta.com/docs/reference/api/groups/#list-groups
        if next_url:
            paged_response = api_client.get(next_url)
        else:
            params = {
                "limit": 10000,
            }
            paged_response = api_client.get_path("/", params)

        paged_results = PagedResults(paged_response, UserGroup)

        group_list.extend(paged_results.result)

        check_rate_limit(paged_response)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return group_list


@timeit
def _get_okta_group_members(api_client: ApiClient, group_id: str) -> list[dict]:
    """
    Get group members from Okta server
    :param api_client: Okta api client
    :param group_id: group to fetch members from
    :return: Array or group membership information
    """
    member_list: list[dict] = []
    next_url = None

    while True:
        try:
            # https://developer.okta.com/docs/reference/api/groups/#list-group-members
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    "limit": 1000,
                }
                paged_response = api_client.get_path(f"/{group_id}/users", params)
        except OktaError:
            logger.error(f"OktaError while listing members of group {group_id}")
            raise

        member_list.extend(json.loads(paged_response.text))

        check_rate_limit(paged_response)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return member_list


@timeit
def transform_okta_group_list(
    okta_group_list: list[UserGroup],
    group_members_map: dict[str, list[str]],
) -> tuple[list[dict], list[str]]:
    """
    Transform okta group list with members data
    :param okta_group_list: list of okta groups
    :param group_members_map: dict mapping group_id to list of member user IDs
    :return: tuple of (groups with members, group ids)
    """
    groups: list[dict] = []
    groups_id: list[str] = []

    for current in okta_group_list:
        group_data = transform_okta_group(current)
        group_id = current.id

        # Add member IDs from the provided map
        group_data["members"] = group_members_map.get(group_id, [])

        groups.append(group_data)
        groups_id.append(group_id)

    return groups, groups_id


def transform_okta_group(okta_group: UserGroup) -> dict:
    """
    Transform okta group object to consumable dictionary for graph
    :param okta_group: okta group object
    :return: dictionary representing the group properties
    """
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/usergroup/UserGroup.py
    group_props = {}
    group_props["id"] = okta_group.id
    group_props["name"] = okta_group.profile.name
    group_props["description"] = okta_group.profile.description
    if okta_group.profile.samAccountName:
        group_props["sam_account_name"] = okta_group.profile.samAccountName
    else:
        group_props["sam_account_name"] = None

    if okta_group.profile.dn:
        group_props["dn"] = okta_group.profile.dn
    else:
        group_props["dn"] = None

    if okta_group.profile.windowsDomainQualifiedName:
        group_props["windows_domain_qualified_name"] = (
            okta_group.profile.windowsDomainQualifiedName
        )
    else:
        group_props["windows_domain_qualified_name"] = None

    if okta_group.profile.externalId:
        group_props["external_id"] = okta_group.profile.externalId
    else:
        group_props["external_id"] = None

    return group_props


@timeit
def _load_okta_groups(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    group_list: list[dict],
    okta_update_tag: int,
) -> None:
    """
    Add okta groups with their members to the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param group_list: list of groups with members field
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaGroupSchema(),
        group_list,
        lastupdated=okta_update_tag,
        ORG_ID=okta_org_id,
    )


@timeit
def sync_okta_groups(
    neo4_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
) -> list[str]:
    """
    Synchronize okta groups with their members
    :param neo4_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :return: List of group ids
    """
    logger.info("Syncing Okta groups")
    api_client = create_api_client(okta_org_id, "/api/v1/groups", okta_api_key)

    # Get all groups from Okta
    okta_group_data = _get_okta_groups(api_client)

    # Fetch members for each group
    group_members_map: dict[str, list[str]] = {}
    for group in okta_group_data:
        group_id = group.id
        members_data = _get_okta_group_members(api_client, group_id)
        # Extract just the user IDs for the relationship
        member_ids = [member["id"] for member in members_data]
        group_members_map[group_id] = member_ids

    # Transform groups with their members
    group_list_info, group_ids = transform_okta_group_list(
        okta_group_data, group_members_map
    )

    # Load groups with their member relationships
    _load_okta_groups(neo4_session, okta_org_id, group_list_info, okta_update_tag)

    return group_ids
