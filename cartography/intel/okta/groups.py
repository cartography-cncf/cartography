from __future__ import annotations

# Okta intel module - Groups
import asyncio
import json
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.group import Group as OktaGroup
from okta.models.group_rule import GroupRule as OktaGroupRule
from okta.models.role import Role as OktaGroupRole
from okta.models.user import User as OktaUser

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_paginated
from cartography.intel.okta.common import OktaApiError
from cartography.intel.okta.common import raise_for_okta_error
from cartography.models.okta.group import OktaGroupRoleSchema
from cartography.models.okta.group import OktaGroupRuleSchema
from cartography.models.okta.group import OktaGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

####
# Groups
####


@timeit
def sync_okta_groups(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta groups and group roles
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Syncing Okta groups")
    groups = asyncio.run(_get_okta_groups(okta_client))

    # For each group, grab what roles might be assigned
    # Note: This could be more efficient using the bulk role assignment API:
    # https://developer.okta.com/docs/reference/api/roles/#list-users-with-role-assignments
    # However, this endpoint is not currently supported in the Okta Python SDK.
    # When SDK support is added, this can be refactored to use a single API call
    # instead of iterating through each group.
    # Role endpoints require super-admin; soft-fail on E0000006 so sync continues.
    # https://developer.okta.com/docs/reference/error-codes/
    group_roles: list[tuple[str, OktaGroupRole]] = []
    logger.info("Syncing Okta group roles")
    try:
        for okta_group in groups:
            group_roles += asyncio.run(
                _get_okta_group_roles(okta_client, okta_group.id)
            )
        transformed_group_roles = _transform_okta_group_roles(group_roles)
        _load_okta_group_roles(
            neo4j_session, transformed_group_roles, common_job_parameters
        )
        _cleanup_okta_group_roles(neo4j_session, common_job_parameters)
    except OktaApiError as exc:
        if exc.error_code == "E0000006":
            logger.warning(
                "Unable to sync group roles - api token needs admin rights to pull admin roles data",
            )
            group_roles = []
            # Still run cleanup so stale roles from a previously privileged
            # token don't linger and overstate admin access.
            _cleanup_okta_group_roles(neo4j_session, common_job_parameters)
        else:
            raise

    # Continue syncing groups, which need group roles at transform time
    transformed_groups = _transform_okta_groups(okta_client, groups, group_roles)
    _load_okta_groups(neo4j_session, transformed_groups, common_job_parameters)
    _cleanup_okta_groups(neo4j_session, common_job_parameters)

    logger.info("Syncing Okta group rules")
    group_rules = asyncio.run(_get_okta_group_rules(okta_client))
    transformed_group_rules = _transform_okta_group_rules(group_rules)
    _load_okta_group_rules(
        neo4j_session, transformed_group_rules, common_job_parameters
    )
    _cleanup_okta_group_rules(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_groups(okta_client: OktaClient) -> list[OktaGroup]:
    """
    Get Okta groups list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta groups
    """
    return await collect_paginated(okta_client.list_groups, limit=200)


@timeit
def _transform_okta_groups(
    okta_client: OktaClient,
    okta_groups: list[OktaGroup],
    okta_group_roles: list[tuple[str, OktaGroupRole]],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta groups into a format for Neo4j
    :param okta_client: An Okta client object
    :param okta_groups: List of Okta groups
    :param okta_group_roles: List of (group_id, role) tuples
    :return: List of group dicts
    """
    transformed_groups: list[dict] = []
    logger.info("Transforming %s Okta groups", len(okta_groups))

    # Build a hashmap of group roles keyed by group_id for O(1) lookup. The
    # SDK's role model is a discriminated pydantic union without an `assignee`
    # field, so we carry the owning group_id alongside rather than mutating
    # the model (which validate_assignment=True would reject).
    roles_by_group: dict[str, list[OktaGroupRole]] = {}
    for group_id, role in okta_group_roles:
        roles_by_group.setdefault(group_id, []).append(role)

    for okta_group in okta_groups:
        group_props: dict[str, Any] = {}
        group_props["id"] = okta_group.id
        group_props["created"] = okta_group.created
        group_props["last_membership_updated"] = okta_group.last_membership_updated
        group_props["last_updated"] = okta_group.last_updated
        group_props["object_class"] = json.dumps(okta_group.object_class)
        # `okta_group.profile` is a discriminated-union wrapper (anyOf
        # OktaUserGroupProfile / OktaActiveDirectoryGroupProfile); concrete
        # fields live on `actual_instance`. AD-only fields (sam_account_name,
        # dn, windows_domain_qualified_name, external_id) need getattr
        # because OktaUserGroupProfile doesn't declare them.
        profile = okta_group.profile
        if profile is not None and hasattr(profile, "actual_instance"):
            profile = profile.actual_instance
        group_props["description"] = getattr(profile, "description", None)
        group_props["name"] = getattr(profile, "name", None)
        group_props["group_type"] = okta_group.type.value if okta_group.type else None
        # Legacy AD-synced group fields for backward compatibility
        group_props["sam_account_name"] = getattr(profile, "sam_account_name", None)
        group_props["dn"] = getattr(profile, "dn", None)
        group_props["windows_domain_qualified_name"] = getattr(
            profile, "windows_domain_qualified_name", None
        )
        group_props["external_id"] = getattr(profile, "external_id", None)
        # For each group, grab what users might assigned
        group_members: list[OktaUser] = asyncio.run(
            _get_okta_group_members(okta_client, okta_group.id),
        )
        for group_member in group_members:
            match_user = {**group_props, "user_id": group_member.id}
            transformed_groups.append(match_user)
        # Check to see if this group has any matching group roles
        for group_role in roles_by_group.get(okta_group.id, []):
            match_role = {**group_props, "role_id": group_role.id}
            transformed_groups.append(match_role)
        transformed_groups.append(group_props)
    return transformed_groups


@timeit
def _load_okta_groups(
    neo4j_session: neo4j.Session,
    group_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta group information into the graph
    :param neo4j_session: session with neo4j server
    :param group_list: list of groups
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info("Loading %s Okta groups", len(group_list))

    load(
        neo4j_session,
        OktaGroupSchema(),
        group_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_groups(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Cleanup group nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


####
# Group Rules
####


@timeit
async def _get_okta_group_rules(okta_client: OktaClient) -> list[OktaGroupRule]:
    """
    Get Okta group rules list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta group rules
    """

    # Note: The pagination limit for group rules is not officially documented by Okta.
    # Based on testing, the API accepts up to 200 per page (similar to other endpoints).
    return await collect_paginated(okta_client.list_group_rules, limit=200)


@timeit
def _transform_okta_group_rules(
    okta_group_rules: list[OktaGroupRule],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta group rules into a format for Neo4j
    :param okta_group_rules: List of Okta group rules
    :return: List of group rule dicts
    """
    transformed_group_rules: list[dict] = []
    logger.info("Transforming %s Okta group rules", len(okta_group_rules))
    for okta_group_rule in okta_group_rules:
        group_rule_props = {}
        group_rule_props["id"] = okta_group_rule.id
        group_rule_props["name"] = okta_group_rule.name
        group_rule_props["status"] = (
            okta_group_rule.status.value if okta_group_rule.status else None
        )
        group_rule_props["last_updated"] = okta_group_rule.last_updated
        group_rule_props["created"] = okta_group_rule.created

        # Handle different condition types
        # Expression-based conditions (most common)
        if (
            okta_group_rule.conditions
            and okta_group_rule.conditions.expression
            and okta_group_rule.conditions.expression.value
        ):
            group_rule_props["condition_type"] = "expression"
            group_rule_props["conditions"] = okta_group_rule.conditions.expression.value
            group_rule_props["expression_type"] = (
                okta_group_rule.conditions.expression.type
                if hasattr(okta_group_rule.conditions.expression, "type")
                else None
            )
        # Group membership conditions
        elif (
            okta_group_rule.conditions
            and hasattr(okta_group_rule.conditions, "people")
            and okta_group_rule.conditions.people
            and hasattr(okta_group_rule.conditions.people, "groups")
            and okta_group_rule.conditions.people.groups
        ):
            group_rule_props["condition_type"] = "group_membership"
            include_groups = (
                okta_group_rule.conditions.people.groups.include
                if hasattr(okta_group_rule.conditions.people.groups, "include")
                else []
            )
            group_rule_props["conditions"] = json.dumps(include_groups)
            group_rule_props["expression_type"] = None
        # Unknown or complex condition types - store as JSON
        elif okta_group_rule.conditions:
            group_rule_props["condition_type"] = "complex"
            try:
                group_rule_props["conditions"] = json.dumps(
                    okta_group_rule.conditions.as_dict()
                )
            except (AttributeError, TypeError):
                group_rule_props["conditions"] = str(okta_group_rule.conditions)
            group_rule_props["expression_type"] = None
        else:
            group_rule_props["condition_type"] = None
            group_rule_props["conditions"] = None
            group_rule_props["expression_type"] = None

        # These rules may have optional exclusions for people
        if (
            okta_group_rule.conditions
            and hasattr(okta_group_rule.conditions, "people")
            and okta_group_rule.conditions.people
            and hasattr(okta_group_rule.conditions.people, "users")
            and okta_group_rule.conditions.people.users
        ):
            group_rule_props["exclusions"] = (
                okta_group_rule.conditions.people.users.exclude
            )
            group_rule_props["inclusions"] = (
                okta_group_rule.conditions.people.users.include
                if hasattr(okta_group_rule.conditions.people.users, "include")
                else None
            )
        else:
            group_rule_props["exclusions"] = None
            group_rule_props["inclusions"] = None

        transformed_group_rules.append(group_rule_props)
        # Create an entry for each group rule and for each group_id.
        # Rules may have non-assignment actions (or no actions), so every
        # level must be guarded.
        actions = okta_group_rule.actions
        assign_user_to_groups = (
            getattr(actions, "assign_user_to_groups", None) if actions else None
        )
        group_ids = (
            getattr(assign_user_to_groups, "group_ids", None)
            if assign_user_to_groups
            else None
        ) or []
        for group_id in group_ids:
            match_group = {
                **group_rule_props,
                "group_id": group_id,
            }
            transformed_group_rules.append(match_group)
    return transformed_group_rules


@timeit
def _load_okta_group_rules(
    neo4j_session: neo4j.Session,
    group_rule_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta group rule information into the graph
    :param neo4j_session: session with neo4j server
    :param group_rule_list: list of group rules
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta group rules", len(group_rule_list))

    load(
        neo4j_session,
        OktaGroupRuleSchema(),
        group_rule_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_group_rules(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Cleanup group rule nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaGroupRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


####
# Group Roles
####


@timeit
async def _get_okta_group_roles(
    okta_client: OktaClient, group_id: str
) -> list[tuple[str, OktaGroupRole]]:
    """
    Get Okta group roles list from Okta
    :param okta_client: An Okta client object
    :param group_id: The id of the group to look up roles for
    :return: List of (group_id, role) tuples
    """
    # This won't ever be paginated
    group_roles, _, error = await okta_client.list_group_assigned_roles(group_id)
    raise_for_okta_error(error, f"list_group_assigned_roles(group_id={group_id})")
    if not group_roles:
        return []
    # The SDK returns a discriminated-union wrapper; the Role fields live on
    # `actual_instance` (StandardRole | CustomRole), so unwrap here.
    return [
        (group_id, role.actual_instance if hasattr(role, "actual_instance") else role)
        for role in group_roles
    ]


@timeit
def _transform_okta_group_roles(
    okta_group_roles: list[tuple[str, OktaGroupRole]],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta group roles into a format for Neo4j
    :param okta_group_roles: List of (group_id, role) tuples
    :return: List of group role dicts
    """
    transformed_group_roles: list[dict] = []
    logger.info("Transforming %s Okta group roles", len(okta_group_roles))
    for _assignee, okta_group_role in okta_group_roles:
        # The SDK emits StandardRole or CustomRole here; StandardRole has no
        # `description` field, and the enum-typed fields are Optional on both
        # variants, so guard everything that isn't guaranteed by the schema.
        role_props = {}
        role_props["id"] = okta_group_role.id
        role_props["assignment_type"] = (
            okta_group_role.assignment_type.value
            if okta_group_role.assignment_type
            else None
        )
        role_props["created"] = okta_group_role.created
        role_props["description"] = getattr(okta_group_role, "description", None)
        role_props["label"] = okta_group_role.label
        role_props["last_updated"] = okta_group_role.last_updated
        role_props["status"] = (
            okta_group_role.status.value if okta_group_role.status else None
        )
        role_props["role_type"] = (
            okta_group_role.type.value if okta_group_role.type else None
        )
        transformed_group_roles.append(role_props)
    return transformed_group_roles


@timeit
def _load_okta_group_roles(
    neo4j_session: neo4j.Session,
    group_roles_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta group roles information into the graph
    :param neo4j_session: session with neo4j server
    :param group_roles_list: list of group roles
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta group roles", len(group_roles_list))

    load(
        neo4j_session,
        OktaGroupRoleSchema(),
        group_roles_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_group_roles(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Cleanup group roles nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaGroupRoleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def _get_okta_group_members(
    okta_client: OktaClient, group_id: str
) -> list[OktaUser]:
    """
    Get Okta group members list from Okta
    :param okta_client: An Okta client object
    :param group_id: The id of the group to look up membership for
    :return: List of Okta Users who are members of a group
    """
    return await collect_paginated(
        okta_client.list_group_users, limit=1000, group_id=group_id
    )
