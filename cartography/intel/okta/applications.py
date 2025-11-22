# Okta intel module - Applications
import json
import logging
from datetime import datetime
from typing import Any

import neo4j
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError

from cartography.client.core.tx import load
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.models.okta.application import OktaApplicationSchema
from cartography.models.okta.replyuri import ReplyUriSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_okta_applications(api_client: ApiClient) -> list[dict]:
    """
    Get application data from Okta server
    :param app_client: api client
    :return: application data
    """
    app_list: list[dict] = []

    next_url = None
    while True:
        try:
            # https://developer.okta.com/docs/reference/api/apps/#list-applications
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    "limit": 500,
                }
                paged_response = api_client.get_path("/", params)
        except OktaError as okta_error:
            logger.debug(f"Got error while listing applications {okta_error}")
            break

        app_list.extend(json.loads(paged_response.text))

        check_rate_limit(paged_response)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_list


@timeit
def _get_application_assigned_users(api_client: ApiClient, app_id: str) -> list[str]:
    """
    Get users assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of user data
    """
    app_users: list[str] = []

    next_url = None
    while True:
        try:
            # https://developer.okta.com/docs/reference/api/apps/#list-users-assigned-to-application
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    "limit": 500,
                }
                paged_response = api_client.get_path(f"/{app_id}/users", params)
        except OktaError as okta_error:
            logger.debug(
                f"Got error while going through list application assigned users {okta_error}",
            )
            break

        app_users.append(paged_response.text)

        check_rate_limit(paged_response)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_users


@timeit
def _get_application_assigned_groups(api_client: ApiClient, app_id: str) -> list[str]:
    """
    Get groups assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of group id
    """
    app_groups: list[str] = []

    next_url = None

    while True:
        try:
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    "limit": 500,
                }
                paged_response = api_client.get_path(f"/{app_id}/groups", params)
        except OktaError as okta_error:
            logger.debug(
                f"Got error while going through list application assigned groups {okta_error}",
            )
            break

        app_groups.append(paged_response.text)

        check_rate_limit(paged_response)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_groups


@timeit
def transform_application_assigned_users_list(
    assigned_user_list: list[str],
) -> list[str]:
    """
    Transform application users Okta data
    :param assigned_user_list: Okta data on assigned users
    :return: Array of users
    """
    users: list[str] = []

    for current in assigned_user_list:
        users.extend(transform_application_assigned_users(current))

    return users


@timeit
def transform_application_assigned_users(json_app_data: str) -> list[str]:
    """
    Transform application users data for graph consumption
    :param json_app_data: raw json application data
    :return: individual user id
    """

    users: list[str] = []
    app_data = json.loads(json_app_data)
    for user in app_data:
        users.append(user["id"])

    return users


@timeit
def transform_application_assigned_groups_list(
    assigned_group_list: list[str],
) -> list[dict]:
    group_list: list[dict] = []

    for current in assigned_group_list:
        group_data = transform_application_assigned_groups(current)
        group_list.extend(group_data)

    return group_list


@timeit
def transform_application_assigned_groups(json_app_data: str) -> list[str]:
    """
    Transform application group assignment to consumable data for the graph
    :param json_app_data: raw json group application assignment data.
    :return: group ids
    """
    groups: list[str] = []
    app_data = json.loads(json_app_data)

    for group in app_data:
        groups.append(group["id"])

    return groups


@timeit
def transform_okta_application_list(okta_applications: list[dict]) -> list[dict]:
    app_list: list[dict] = []

    for current in okta_applications:
        app_info = transform_okta_application(current)
        app_list.append(app_info)

    return app_list


@timeit
def transform_okta_application(okta_application: dict) -> dict:
    app_props = {}
    app_props["id"] = okta_application["id"]
    app_props["name"] = okta_application["name"]
    app_props["label"] = okta_application["label"]
    if "created" in okta_application and okta_application["created"]:
        app_props["created"] = datetime.strptime(
            okta_application["created"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["created"] = None

    if "lastUpdated" in okta_application and okta_application["lastUpdated"]:
        app_props["okta_last_updated"] = datetime.strptime(
            okta_application["lastUpdated"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["okta_last_updated"] = None

    app_props["status"] = okta_application["status"]

    if "activated" in okta_application and okta_application["activated"]:
        app_props["activated"] = datetime.strptime(
            okta_application["activated"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["activated"] = None

    app_props["features"] = okta_application["features"]
    app_props["sign_on_mode"] = okta_application["signOnMode"]

    return app_props


@timeit
def transform_okta_application_extract_replyurls(
    okta_application: dict,
) -> str | None:
    """
    Extracts the reply uri information from an okta app
    """

    if "oauthClient" in okta_application["settings"]:
        if "redirect_uris" in okta_application["settings"]["oauthClient"]:
            return okta_application["settings"]["oauthClient"]["redirect_uris"]
    return None


@timeit
def transform_okta_application_list_with_relationships(
    okta_app_data: list[dict],
    app_users_map: dict[str, list[str]],
    app_groups_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """
    Transform application data with their assigned users and groups
    :param okta_app_data: Raw application data from Okta
    :param app_users_map: dict mapping app_id to list of user IDs
    :param app_groups_map: dict mapping app_id to list of group IDs
    :return: list of application objects with users and groups lists
    """
    app_list: list[dict[str, Any]] = []

    for app in okta_app_data:
        app_info = transform_okta_application(app)
        app_id = app["id"]

        # Add user and group IDs from the provided maps
        app_info["users"] = app_users_map.get(app_id, [])
        app_info["groups"] = app_groups_map.get(app_id, [])

        app_list.append(app_info)

    return app_list


@timeit
def _load_okta_applications(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    app_list: list[dict],
    okta_update_tag: int,
) -> None:
    """
    Add application into the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param app_list: application list - Array of dictionary with users and groups
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaApplicationSchema(),
        app_list,
        lastupdated=okta_update_tag,
        ORG_ID=okta_org_id,
    )


@timeit
def transform_reply_uris_with_applications(
    app_reply_urls_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """
    Transform reply URLs by aggregating applications per URL
    :param app_reply_urls_map: dict mapping app_id to list of reply URLs
    :return: list of ReplyUri objects with applications field
    """
    # Aggregate applications by reply URL
    uri_to_apps: dict[str, list[str]] = {}

    for app_id, reply_urls in app_reply_urls_map.items():
        if reply_urls:
            for url in reply_urls:
                if url not in uri_to_apps:
                    uri_to_apps[url] = []
                uri_to_apps[url].append(app_id)

    # Transform to ReplyUri objects
    reply_uris = []
    for uri, app_ids in uri_to_apps.items():
        reply_uris.append(
            {
                "id": uri,
                "uri": uri,
                "applications": app_ids,
            }
        )

    return reply_uris


@timeit
def _load_reply_uris(
    neo4j_session: neo4j.Session,
    reply_uris: list[dict],
    okta_update_tag: int,
) -> None:
    """
    Load reply URIs into the graph
    :param neo4j_session: session with the Neo4j server
    :param reply_uris: list of reply URI objects with applications
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    if not reply_uris:
        return

    load(
        neo4j_session,
        ReplyUriSchema(),
        reply_uris,
        lastupdated=okta_update_tag,
    )


@timeit
def sync_okta_applications(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
) -> None:
    """
    Sync okta application
    :param neo4j_session: session from the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta api key
    :return: Nothing
    """
    logger.info("Syncing Okta Applications")

    api_client = create_api_client(okta_org_id, "/api/v1/apps", okta_api_key)

    # Get all applications from Okta
    okta_app_data = _get_okta_applications(api_client)

    # Fetch assigned users for each application
    app_users_map: dict[str, list[str]] = {}
    for app in okta_app_data:
        app_id = app["id"]
        user_list_data = _get_application_assigned_users(api_client, app_id)
        user_list = transform_application_assigned_users_list(user_list_data)
        app_users_map[app_id] = user_list

    # Fetch assigned groups for each application
    app_groups_map: dict[str, list[str]] = {}
    for app in okta_app_data:
        app_id = app["id"]
        group_list_data = _get_application_assigned_groups(api_client, app_id)
        group_list = transform_application_assigned_groups_list(group_list_data)
        app_groups_map[app_id] = group_list

    # Extract reply URLs for each application
    app_reply_urls_map: dict[str, list[str]] = {}
    for app in okta_app_data:
        app_id = app["id"]
        reply_urls = transform_okta_application_extract_replyurls(app)
        app_reply_urls_map[app_id] = reply_urls

    # Transform applications with their relationships
    app_data_with_relationships = transform_okta_application_list_with_relationships(
        okta_app_data, app_users_map, app_groups_map
    )

    # Load applications into the graph
    _load_okta_applications(
        neo4j_session, okta_org_id, app_data_with_relationships, okta_update_tag
    )

    # Transform and load reply URIs
    reply_uris = transform_reply_uris_with_applications(app_reply_urls_map)
    _load_reply_uris(neo4j_session, reply_uris, okta_update_tag)
