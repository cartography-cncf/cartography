# Okta intel module - Users
from __future__ import annotations

import asyncio
import dataclasses
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.role import Role as OktaUserRole
from okta.models.user import User as OktaUser
from okta.models.user_type import UserType as OktaUserType

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.core.common import PropertyRef
from cartography.models.okta.user import OktaUserRoleSchema
from cartography.models.okta.user import OktaUserSchema
from cartography.models.okta.user import OktaUserTypeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

####
# Okta User Types
####


@timeit
def sync_okta_user_types(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta users types
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Syncing Okta user types")
    user_types = asyncio.run(_get_okta_user_types(okta_client))
    transformed_user_types = _transform_okta_user_types(user_types)
    _load_okta_user_types(neo4j_session, transformed_user_types, common_job_parameters)
    _cleanup_okta_user_types(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_user_types(okta_client: OktaClient) -> list[OktaUserType]:
    """
    Get Okta user types list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta authenticators
    """
    output_user_types = []
    # This won't ever be paginated
    user_types, _, _ = await okta_client.list_user_types()
    output_user_types += user_types
    logger.debug("Fetched %s user types", len(user_types))
    return output_user_types


@timeit
def _transform_okta_user_types(
    okta_user_types: list[OktaUserType],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta user types into a format for Neo4j
    :param okta_user_types: List of Okta user types
    :return: List of user type dicts
    """

    transformed_users: list[dict] = []
    logger.info("Transforming %s Okta user types", len(okta_user_types))
    for okta_user_type in okta_user_types:
        user_type_props = {}
        user_type_props["id"] = okta_user_type.id
        user_type_props["created"] = okta_user_type.created
        user_type_props["created_by"] = okta_user_type.created_by
        user_type_props["default"] = okta_user_type.default
        user_type_props["description"] = okta_user_type.description
        user_type_props["display_name"] = okta_user_type.display_name
        user_type_props["last_updated"] = okta_user_type.last_updated
        user_type_props["last_updated_by"] = okta_user_type.last_updated_by
        user_type_props["name"] = okta_user_type.name
        transformed_users.append(user_type_props)
    return transformed_users


@timeit
def _load_okta_user_types(
    neo4j_session: neo4j.Session,
    user_type_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta user type information into the graph
    :param neo4j_session: session with neo4j server
    :param user_type_list: list of user types
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info("Loading %s Okta user types", len(user_type_list))
    load(
        neo4j_session,
        OktaUserTypeSchema(),
        user_type_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_user_types(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup user types nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaUserTypeSchema(), common_job_parameters).run(
        neo4j_session,
    )


##############
# Okta Users
##############


@timeit
def sync_okta_users(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """
    Sync Okta users
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: List of user IDs that were synced
    """

    logger.info("Syncing Okta users")
    users = asyncio.run(_get_okta_users(okta_client))

    # Gather user roles
    # Note: Per-user role fetching is currently disabled because it requires O(n) API calls
    # (one per user), which is inefficient for large organizations.
    # The Okta API supports bulk role assignment listing via:
    # https://developer.okta.com/docs/reference/api/roles/#list-users-with-role-assignments
    # However, this endpoint is not currently supported in the Okta Python SDK.
    # When SDK support is added, this can be enabled using a single bulk API call.
    # The _get_okta_user_roles function below is ready to use when SDK support is available.
    user_roles: list[OktaUserRole] = []
    transformed_user_roles = _transform_okta_user_roles(user_roles)
    _load_okta_user_roles(neo4j_session, transformed_user_roles, common_job_parameters)
    _cleanup_okta_user_roles(neo4j_session, common_job_parameters)

    transformed_users = _transform_okta_users(users, user_roles)
    _load_okta_users(neo4j_session, transformed_users, common_job_parameters)
    _cleanup_okta_users(neo4j_session, common_job_parameters)

    # Return user IDs for factors sync
    return [user.id for user in users]


@timeit
async def _get_okta_users(okta_client: OktaClient) -> list[OktaUser]:
    """
    Get Okta users list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta users
    """
    output_users = []
    # All users except deprovisioned users are returned
    # We'll have to call deprovisioned users sep
    statuses = [None, "DEPROVISIONED"]
    for status in statuses:
        query_parameters: dict[str, Any] = {"limit": 200}
        if status:
            query_parameters["filter"] = f'(status eq "{status}" )'
        else:
            status = "NON-DEPROVISIONED"
        users, resp, _ = await okta_client.list_users(query_parameters)
        output_users += users
        while resp.has_next():
            users, _ = await resp.next()
            output_users += users
            logger.debug("Fetched %s %s users", len(users), status)
    return output_users


@timeit
def _transform_okta_users(
    okta_users: list[OktaUser],
    okta_user_roles: list[OktaUserRole],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta users into a format for Neo4j
    :param okta_users: List of Okta users
    :param okta_user_roles: List of Okta user roles
    :return: List of users dicts
    """
    transformed_users: list[dict] = []
    logger.info("Transforming %s Okta users", len(okta_users))
    for okta_user in okta_users:
        user_props: dict[str, Any] = {}
        # Dynamic properties added that change based on tenant
        user_props.update(okta_user.profile.__dict__)
        user_props["id"] = okta_user.id
        user_props["created"] = okta_user.created
        user_props["status"] = okta_user.status.value if okta_user.status else None
        user_props["transition_to_status"] = okta_user.transitioning_to_status
        user_props["activated"] = okta_user.activated
        user_props["status_changed"] = okta_user.status_changed
        user_props["last_login"] = okta_user.last_login
        user_props["last_updated"] = okta_user.last_updated
        user_props["password_changed"] = okta_user.password_changed
        user_props["type"] = okta_user.type.id if okta_user.type else None
        # Add role information on a per user basis
        for user_role in okta_user_roles:
            if user_role.assignee != okta_user.id:
                continue
            match_role = {**user_props, "role_id": user_role.id}
            transformed_users.append(match_role)
        transformed_users.append(user_props)
    return transformed_users


@timeit
def _load_okta_users(
    neo4j_session: neo4j.Session,
    user_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta user information into the graph
    :param neo4j_session: session with neo4j server
    :param user_list: list of users
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta users", len(user_list))
    # We want to allow for dynamic properties on this element
    # Iterate through all the users and pick out all valid profile attribute names
    valid_keys: set[str] = set()
    for user in user_list:
        valid_keys.update(user.keys())

    # Ensure mandatory properties are included
    valid_keys.add("id")
    valid_keys.add("lastupdated")

    # Make sure each user has a value set for every parameter, even if None
    for user in user_list:
        for key in valid_keys:
            if key not in user:
                user[key] = None

    # Next we need to dynamically construct an equivalent to a NodeProperties Dataclass
    properties = []
    prop_value_dict = {}
    for key in valid_keys:
        properties.append((key, PropertyRef))
        if key == "lastupdated":
            prop_value_dict[key] = PropertyRef(key, set_in_kwargs=True)
        else:
            prop_value_dict[key] = PropertyRef(key)

    custom_node_prop_class_def = dataclasses.make_dataclass(
        "OktaUserNodeProperties",
        properties,
        frozen=True,
    )
    custom_node_prop_class = custom_node_prop_class_def(**prop_value_dict)
    # Create a new schema instance with the custom properties
    # We use dataclasses.replace to create a modified copy of the frozen dataclass
    base_schema = OktaUserSchema()
    custom_okta_user_schema = dataclasses.replace(
        base_schema,
        properties=custom_node_prop_class,
    )
    load(
        neo4j_session,
        custom_okta_user_schema,
        user_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup user nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaUserSchema(), common_job_parameters).run(
        neo4j_session,
    )


####
# User Roles
####


@timeit
async def _get_okta_user_roles(
    okta_client: OktaClient,
    user_id: str,
) -> list[OktaUserRole]:
    """
    Get Okta user roles list from Okta
    :param okta_client: An Okta client object
    :param user_id: The user ID to fetch roles for
    :return: List of Okta user roles
    """
    # This won't ever be paginated
    output_user_roles, _, _ = await okta_client.list_assigned_roles_for_user(user_id)
    # The user role object doesn't include an easily parsable user_id
    # for which it applies. So we manually add it
    for output_user_role in output_user_roles:
        output_user_role.assignee = user_id
    return output_user_roles


@timeit
def _transform_okta_user_roles(
    okta_user_roles: list[OktaUserRole],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta user roles into a format for Neo4j
    :param okta_user_roles: List of Okta user roles
    :return: List of user roles dicts
    """
    transformed_user_roles: list[dict] = []
    logger.info("Transforming %s Okta user roles", len(okta_user_roles))
    for okta_user_role in okta_user_roles:
        role_props: dict[str, Any] = {}
        role_props["id"] = okta_user_role.id
        role_props["assignment_type"] = (
            okta_user_role.assignment_type.value
            if okta_user_role.assignment_type
            else None
        )
        role_props["created"] = okta_user_role.created
        role_props["description"] = okta_user_role.description
        role_props["label"] = okta_user_role.label
        role_props["last_updated"] = okta_user_role.last_updated
        role_props["status"] = (
            okta_user_role.status.value if okta_user_role.status else None
        )
        role_props["role_type"] = (
            okta_user_role.type.value if okta_user_role.type else None
        )
        transformed_user_roles.append(role_props)
    return transformed_user_roles


@timeit
def _load_okta_user_roles(
    neo4j_session: neo4j.Session,
    user_roles_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta user role information into the graph
    :param neo4j_session: session with neo4j server
    :param user_roles_list: list of user roles
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta user roles", len(user_roles_list))

    load(
        neo4j_session,
        OktaUserRoleSchema(),
        user_roles_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_user_roles(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup user role nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaUserRoleSchema(), common_job_parameters).run(
        neo4j_session,
    )
