# Okta intel module - Users
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from okta import UsersClient
from okta.models.user import User

from cartography.client.core.tx import load
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.intel.okta.utils import check_rate_limit
from cartography.models.okta.human import HumanSchema
from cartography.models.okta.user import OktaUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _create_user_client(okta_org: str, okta_api_key: str) -> UsersClient:
    """
    Create Okta User Client
    :param okta_org: Okta organization name
    :param okta_api_key: Okta API key
    :return: Instance of UsersClient
    """
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_client = UsersClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=okta_api_key,
    )

    return user_client


@timeit
def _get_okta_users(user_client: UsersClient) -> List[Dict]:
    """
    Get Okta users from Okta server
    :param user_client: user client
    :return: Array of user data
    """
    user_list: List[Dict] = []
    paged_users = user_client.get_paged_users()

    # TODO: Fix bug, we miss last page :(
    while True:
        user_list.extend(paged_users.result)
        check_rate_limit(paged_users.response)
        if not paged_users.is_last_page():
            # Keep on fetching pages of users until the last page
            paged_users = user_client.get_paged_users(url=paged_users.next_url)
        else:
            break

    return user_list


@timeit
def transform_okta_user_list(
    okta_user_list: List[User],
) -> Tuple[List[Dict], List[str]]:
    users: List[Dict] = []
    user_ids: List[str] = []

    for current in okta_user_list:
        users.append(transform_okta_user(current))
        user_ids.append(current.id)

    return users, user_ids


@timeit
def transform_okta_user(okta_user: User) -> Dict:
    """
    Transform okta user data
    :param okta_user: okta user object
    :return: Dictionary container user properties for ingestion
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props = {}
    user_props["first_name"] = okta_user.profile.firstName
    user_props["last_name"] = okta_user.profile.lastName
    user_props["login"] = okta_user.profile.login
    user_props["email"] = okta_user.profile.email

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props["id"] = okta_user.id
    user_props["created"] = okta_user.created.strftime("%m/%d/%Y, %H:%M:%S")
    if okta_user.activated:
        user_props["activated"] = okta_user.activated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["activated"] = None

    if okta_user.statusChanged:
        user_props["status_changed"] = okta_user.statusChanged.strftime(
            "%m/%d/%Y, %H:%M:%S",
        )
    else:
        user_props["status_changed"] = None

    if okta_user.lastLogin:
        user_props["last_login"] = okta_user.lastLogin.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["last_login"] = None

    if okta_user.lastUpdated:
        user_props["okta_last_updated"] = okta_user.lastUpdated.strftime(
            "%m/%d/%Y, %H:%M:%S",
        )
    else:
        user_props["okta_last_updated"] = None

    if okta_user.passwordChanged:
        user_props["password_changed"] = okta_user.passwordChanged.strftime(
            "%m/%d/%Y, %H:%M:%S",
        )
    else:
        user_props["password_changed"] = None

    if okta_user.transitioningToStatus:
        user_props["transition_to_status"] = okta_user.transitioningToStatus
    else:
        user_props["transition_to_status"] = None

    return user_props


@timeit
def _load_okta_users(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    user_list: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Load Okta user information into the graph
    :param neo4j_session: session with neo4j server
    :param okta_org_id: oktat organization id
    :param user_list: list of users
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaUserSchema(),
        user_list,
        lastupdated=okta_update_tag,
        ORG_ID=okta_org_id,
    )
    load(
        neo4j_session,
        HumanSchema(),
        user_list,
        lastupdated=okta_update_tag,
    )


@timeit
def sync_okta_users(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
    sync_state: OktaSyncState,
) -> None:
    """
    Sync okta users
    :param neo4j_session: Session with Neo4j server
    :param okta_org_id: Okta organization id to sync
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :param sync_state: Okta sync state
    :return: Nothing
    """

    logger.info("Syncing Okta users")
    user_client = _create_user_client(okta_org_id, okta_api_key)
    data = _get_okta_users(user_client)
    users_data, user_ids = transform_okta_user_list(data)

    _load_okta_users(neo4j_session, okta_org_id, users_data, okta_update_tag)

    # store result for later use
    sync_state.users = user_ids
