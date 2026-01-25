# Okta intel module - Applications
import json
import logging
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError

from cartography.client.core.tx import run_write_query
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_okta_applications(api_client: ApiClient) -> List[Dict]:
    """
    Get application data from Okta server
    :param app_client: api client
    :return: application data
    """
    app_list: List[Dict] = []

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
def _get_application_assigned_users(api_client: ApiClient, app_id: str) -> List[str]:
    """
    Get users assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of user data
    """
    app_users: List[str] = []

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
def _get_application_assigned_groups(api_client: ApiClient, app_id: str) -> List[str]:
    """
    Get groups assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of group id
    """
    app_groups: List[str] = []

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
    assigned_user_list: List[str],
) -> List[str]:
    """
    Transform application users Okta data
    :param assigned_user_list: Okta data on assigned users
    :return: Array of users
    """
    users: List[str] = []

    for current in assigned_user_list:
        users.extend(transform_application_assigned_users(current))

    return users


@timeit
def transform_application_assigned_users(json_app_data: str) -> List[str]:
    """
    Transform application users data for graph consumption
    :param json_app_data: raw json application data
    :return: individual user id
    """

    users: List[str] = []
    app_data = json.loads(json_app_data)
    for user in app_data:
        users.append(user["id"])

    return users


@timeit
def transform_application_assigned_groups_list(
    assigned_group_list: List[str],
) -> List[Dict]:
    group_list: List[Dict] = []

    for current in assigned_group_list:
        group_data = transform_application_assigned_groups(current)
        group_list.extend(group_data)

    return group_list


@timeit
def transform_application_assigned_groups(json_app_data: str) -> List[str]:
    """
    Transform application group assignment to consumable data for the graph
    :param json_app_data: raw json group application assignment data.
    :return: group ids
    """
    groups: List[str] = []
    app_data = json.loads(json_app_data)

    for group in app_data:
        groups.append(group["id"])

    return groups


@timeit
def transform_okta_application_list(okta_applications: List[Dict]) -> List[Dict]:
    app_list: List[Dict] = []

    for current in okta_applications:
        app_info = transform_okta_application(current)
        app_list.append(app_info)

    return app_list


@timeit
def transform_okta_application(okta_application: Dict) -> Dict:
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
    okta_application: Dict,
) -> Optional[str]:
    """
    Extracts the reply uri information from an okta app
    """

    if "oauthClient" in okta_application["settings"]:
        if "redirect_uris" in okta_application["settings"]["oauthClient"]:
            return okta_application["settings"]["oauthClient"]["redirect_uris"]
    return None


@timeit
def _load_okta_applications(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    app_list: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Add application into the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param app_list: application list - Array of dictionary
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (org:OktaOrganization{id: $ORG_ID})
    WITH org
    UNWIND $APP_LIST as app_data
    MERGE (new_app:OktaApplication{id: app_data.id})
    ON CREATE SET new_app.firstseen = timestamp()
    SET new_app:ThirdPartyApp,
    new_app.name = app_data.name,
    new_app._ont_client_id = app_data.id,
    new_app._ont_name = app_data.label,
    new_app._ont_enabled = (app_data.status IN ['ACTIVE']),
    new_app._ont_protocol = app_data.sign_on_mode,
    new_app.label = app_data.label,
    new_app.created = app_data.created,
    new_app.okta_last_updated = app_data.okta_last_updated,
    new_app.status = app_data.status,
    new_app.activated = app_data.activated,
    new_app.features = app_data.features,
    new_app.sign_on_mode = app_data.sign_on_mode,
    new_app.lastupdated = $okta_update_tag
    WITH org, new_app
    MERGE (org)-[org_r:RESOURCE]->(new_app)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest_statement,
        ORG_ID=okta_org_id,
        APP_LIST=app_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_application_user(
    neo4j_session: neo4j.Session,
    app_id: str,
    user_list: List[str],
    okta_update_tag: int,
) -> None:
    """
    Add application users into the graph
    :param neo4j_session: session with the Neo4j server
    :param app_id: application to map
    :param user_list: users to map
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MATCH (app:OktaApplication{id: $APP_ID})
    WITH app
    UNWIND $USER_LIST as user_id
    MATCH (user:OktaUser{id: user_id})
    WITH app, user
    MERGE (user)-[r:APPLICATION]->(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        APP_ID=app_id,
        USER_LIST=user_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_application_group(
    neo4j_session: neo4j.Session,
    app_id: str,
    group_list: List[str],
    okta_update_tag: int,
) -> None:
    """
    Add application groups into the graph
    :param neo4j_session: session with the Neo4j server
    :param app_id: application to map
    :param group_list: groups to map
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MATCH (app:OktaApplication{id: $APP_ID})
    WITH app
    UNWIND $GROUP_LIST as group_id
    MATCH (group:OktaGroup{id: group_id})
    WITH app, group
    MERGE (group)-[r:APPLICATION]->(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        APP_ID=app_id,
        GROUP_LIST=group_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_application_reply_urls(
    neo4j_session: neo4j.Session,
    app_id: str,
    reply_urls: List[str],
    okta_update_tag: int,
) -> None:
    """
    Add reply urls to their applications
    :param neo4j_session: session with the Neo4j server
    :param app_id: application to map the reply urls to
    :param reply_urls: reply urls to map
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    if not reply_urls:
        return
    ingest = """
    MATCH (app:OktaApplication{id: $APP_ID})
    WITH app
    UNWIND $URL_LIST as url_list
    MERGE (uri:ReplyUri{id: url_list})
    ON CREATE SET uri.firstseen = timestamp()
    SET uri.uri = url_list,
    uri.lastupdated = $okta_update_tag
    WITH app, uri
    MERGE (uri)<-[r:REPLYURI]-(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        APP_ID=app_id,
        URL_LIST=reply_urls,
        okta_update_tag=okta_update_tag,
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

    okta_app_data = _get_okta_applications(api_client)
    app_data = transform_okta_application_list(okta_app_data)
    _load_okta_applications(neo4j_session, okta_org_id, app_data, okta_update_tag)

    for app in okta_app_data:
        app_id = app["id"]
        user_list_data = _get_application_assigned_users(api_client, app_id)
        user_list = transform_application_assigned_users_list(user_list_data)
        _load_application_user(neo4j_session, app_id, user_list, okta_update_tag)

        group_list_data = _get_application_assigned_groups(api_client, app_id)
        group_list = transform_application_assigned_groups_list(group_list_data)
        _load_application_group(neo4j_session, app_id, group_list, okta_update_tag)

        reply_urls = transform_okta_application_extract_replyurls(app)
        _load_application_reply_urls(neo4j_session, app_id, reply_urls, okta_update_tag)
