# Okta intel module - Users
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.role import Role as OktaUserRole
from okta.models.user import User as OktaUser
from okta.models.user_type import UserType as OktaUserType

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_paginated
from cartography.intel.okta.common import OktaApiError
from cartography.intel.okta.common import raise_for_okta_error
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
    # This won't ever be paginated
    user_types, _, error = await okta_client.list_user_types()
    raise_for_okta_error(error, "list_user_types")
    return user_types or []


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

    # Gather user roles using the bulk API to minimize API calls.
    # Role endpoints require super-admin; most tokens won't have it. When the
    # API returns E0000006 we log and continue so the rest of the sync runs.
    # https://developer.okta.com/docs/reference/error-codes/
    user_roles: list[tuple[str, OktaUserRole]] = []
    try:
        user_roles = asyncio.run(_get_all_user_roles(okta_client))
        transformed_user_roles = _transform_okta_user_roles(user_roles)
        _load_okta_user_roles(
            neo4j_session, transformed_user_roles, common_job_parameters
        )
        _cleanup_okta_user_roles(neo4j_session, common_job_parameters)
    except OktaApiError as exc:
        if exc.error_code == "E0000006":
            logger.warning(
                "Unable to sync user roles - api token needs admin rights to pull admin roles data",
            )
            # Still run cleanup so stale roles from a previously privileged
            # token don't linger and overstate admin access.
            _cleanup_okta_user_roles(neo4j_session, common_job_parameters)
        else:
            raise

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
    output_users: list[OktaUser] = []
    # All users except deprovisioned users are returned
    # We'll have to call deprovisioned users sep
    statuses = [None, "DEPROVISIONED"]
    for status in statuses:
        kwargs: dict[str, Any] = {}
        if status:
            kwargs["filter"] = f'(status eq "{status}" )'
        users = await collect_paginated(okta_client.list_users, limit=200, **kwargs)
        output_users += users
    return output_users


@timeit
def _transform_okta_users(
    okta_users: list[OktaUser],
    okta_user_roles: list[tuple[str, OktaUserRole]],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta users into a format for Neo4j
    :param okta_users: List of Okta users
    :param okta_user_roles: List of (user_id, role) tuples
    :return: List of users dicts
    """
    transformed_users: list[dict] = []
    logger.info("Transforming %s Okta users", len(okta_users))
    # The SDK's role model is a discriminated pydantic union without an
    # `assignee` field, so we carry the owning user_id alongside rather than
    # mutating the model (which validate_assignment=True would reject).
    roles_by_user: dict[str, list[OktaUserRole]] = {}
    for user_id, user_role in okta_user_roles:
        roles_by_user.setdefault(user_id, []).append(user_role)
    for okta_user in okta_users:
        user_props: dict[str, Any] = {}
        # Standard UserProfile fields are declared explicitly on the schema;
        # tenant-specific custom attributes (Okta's `additional_properties`)
        # are JSON-serialised into a single `custom_attributes` blob so they
        # don't require a dynamic schema.
        if okta_user.profile is not None:
            profile_data = okta_user.profile.model_dump()
            custom_attrs = profile_data.pop("additional_properties", None) or {}
            user_props.update(profile_data)
            user_props["custom_attributes"] = (
                json.dumps(custom_attrs) if custom_attrs else None
            )
        else:
            user_props["custom_attributes"] = None
        user_props["id"] = okta_user.id
        user_props["created"] = okta_user.created
        user_props["status"] = okta_user.status.value if okta_user.status else None
        user_props["transition_to_status"] = okta_user.transitioning_to_status
        user_props["activated"] = okta_user.activated
        user_props["status_changed"] = okta_user.status_changed
        user_props["last_login"] = okta_user.last_login
        user_props["okta_last_updated"] = okta_user.last_updated
        user_props["password_changed"] = okta_user.password_changed
        user_props["type"] = okta_user.type.id if okta_user.type else None
        # Add role information on a per user basis
        for user_role in roles_by_user.get(okta_user.id, []):
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
    load(
        neo4j_session,
        OktaUserSchema(),
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
async def _get_all_user_roles(
    okta_client: OktaClient,
) -> list[tuple[str, OktaUserRole]]:
    """
    Get all user roles using the bulk API for efficiency.

    Uses list_users_with_role_assignments to first get users who have roles,
    then fetches roles only for those users. This is O(m) where m is the number
    of users with roles, rather than O(n) for all users.

    :param okta_client: An Okta client object
    :return: List of (user_id, role) tuples across all users
    """
    from okta.pagination import PaginationHelper

    all_user_roles: list[tuple[str, OktaUserRole]] = []

    # Step 1: Get all users who have role assignments (bulk API). This endpoint
    # returns a RoleAssignedUsers wrapper (with a `value` list) per page, so we
    # paginate manually via the Link header cursor.
    user_ids_with_roles: list[str] = []
    after: str | None = None
    while True:
        result, resp, error = await okta_client.list_users_with_role_assignments(
            limit=200, after=after
        )
        raise_for_okta_error(error, "list_users_with_role_assignments")
        if result and result.value:
            user_ids_with_roles.extend([u.id for u in result.value if u.id])
        cursor = (
            PaginationHelper.extract_next_cursor(resp.headers)
            if resp is not None
            else None
        )
        if not cursor:
            break
        after = cursor

    logger.info("Found %d users with role assignments", len(user_ids_with_roles))

    # Step 2: For each user with roles, fetch their actual roles
    for user_id in user_ids_with_roles:
        user_roles = await _get_okta_user_roles(okta_client, user_id)
        all_user_roles.extend(user_roles)

    return all_user_roles


@timeit
async def _get_okta_user_roles(
    okta_client: OktaClient,
    user_id: str,
) -> list[tuple[str, OktaUserRole]]:
    """
    Get Okta user roles list from Okta for a specific user.
    :param okta_client: An Okta client object
    :param user_id: The user ID to fetch roles for
    :return: List of (user_id, role) tuples
    """
    output_user_roles, _, error = await okta_client.list_assigned_roles_for_user(
        user_id
    )
    raise_for_okta_error(error, f"list_assigned_roles_for_user(user_id={user_id})")
    if not output_user_roles:
        return []
    # The SDK returns a discriminated-union wrapper; the Role fields live on
    # `actual_instance` (StandardRole | CustomRole), so unwrap here.
    return [
        (user_id, role.actual_instance if hasattr(role, "actual_instance") else role)
        for role in output_user_roles
    ]


@timeit
def _transform_okta_user_roles(
    okta_user_roles: list[tuple[str, OktaUserRole]],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta user roles into a format for Neo4j
    :param okta_user_roles: List of (user_id, role) tuples
    :return: List of user roles dicts
    """
    transformed_user_roles: list[dict] = []
    logger.info("Transforming %s Okta user roles", len(okta_user_roles))
    for _assignee, okta_user_role in okta_user_roles:
        # The SDK emits StandardRole or CustomRole here; StandardRole has no
        # `description` field, so fall back to None for any optional field not
        # present on the concrete variant.
        role_props: dict[str, Any] = {}
        role_props["id"] = okta_user_role.id
        role_props["assignment_type"] = (
            okta_user_role.assignment_type.value
            if okta_user_role.assignment_type
            else None
        )
        role_props["created"] = okta_user_role.created
        role_props["description"] = getattr(okta_user_role, "description", None)
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
