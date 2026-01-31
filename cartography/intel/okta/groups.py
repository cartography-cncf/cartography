# Okta intel module - Groups
import asyncio
import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from okta.client import Client as OktaClient
from okta.models.group import Group as OktaGroup
from okta.models.group_rule import GroupRule as OktaGroupRule
from okta.models.role import Role as OktaGroupRole
from okta.models.user import User as OktaUser

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
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
    common_job_parameters: Dict[str, Any],
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
    group_roles = []
    logger.info("Syncing Okta group roles")
    for okta_group in groups:
        group_roles += asyncio.run(_get_okta_group_roles(okta_client, okta_group.id))
    transformed_group_roles = _transform_okta_group_roles(group_roles)
    _load_okta_group_roles(
        neo4j_session, transformed_group_roles, common_job_parameters
    )
    _cleanup_okta_group_roles(neo4j_session, common_job_parameters)

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
async def _get_okta_groups(okta_client: OktaClient) -> List[OktaGroup]:
    """
    Get Okta groups list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta groups
    """
    output_groups = []
    query_parameters = {"limit": 200}
    groups, resp, _ = await okta_client.list_groups(query_parameters)
    output_groups += groups
    while resp.has_next():
        groups, _ = await resp.next()
        output_groups += groups
        logger.info(f"Fetched {len(groups)} groups")
    return output_groups


@timeit
def _transform_okta_groups(
    okta_client: OktaClient,
    okta_groups: List[OktaGroup],
    okta_group_roles: List[OktaGroupRole],
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta groups into a format for Neo4j
    :param okta_client: An Okta client object
    :param okta_groups: List of Okta groups
    :param okta_group_roles: List of Okta group roles
    :return: List of group dicts
    """
    transformed_groups: List[Dict] = []
    logger.info(f"Transforming {len(okta_groups)} Okta groups")

    # Build a hashmap of group roles keyed by group_id for O(1) lookup
    roles_by_group: Dict[str, List[OktaGroupRole]] = {}
    for role in okta_group_roles:
        if role.assignee not in roles_by_group:
            roles_by_group[role.assignee] = []
        roles_by_group[role.assignee].append(role)

    for okta_group in okta_groups:
        group_props: Dict[str, Any] = {}
        group_props["id"] = okta_group.id
        group_props["created"] = okta_group.created
        group_props["last_membership_updated"] = okta_group.last_membership_updated
        group_props["last_updated"] = okta_group.last_updated
        group_props["object_class"] = json.dumps(okta_group.object_class)
        group_props["profile_description"] = okta_group.profile.description
        group_props["profile_name"] = okta_group.profile.name
        group_props["group_type"] = okta_group.type.value
        # For each group, grab what users might assigned
        group_members: List[OktaUser] = asyncio.run(
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
    group_list: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Okta group information into the graph
    :param neo4j_session: session with neo4j server
    :param group_list: list of groups
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info(f"Loading {len(group_list)} Okta groups")

    load(
        neo4j_session,
        OktaGroupSchema(),
        group_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_groups(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
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
async def _get_okta_group_rules(okta_client: OktaClient) -> List[OktaGroupRule]:
    """
    Get Okta group rules list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta group rules
    """

    output_group_rules: List[Dict] = []
    # Note: The pagination limit for group rules is not officially documented by Okta.
    # Based on testing, the API accepts up to 200 per page (similar to other endpoints).
    # We use 200 here as a safe default that aligns with other Okta API pagination limits.
    query_parameters = {"limit": 200}
    group_rules, resp, _ = await okta_client.list_group_rules(query_parameters)
    output_group_rules += group_rules
    while resp.has_next():
        group_rules, _ = await resp.next()
        output_group_rules += group_rules
    return output_group_rules


@timeit
def _transform_okta_group_rules(
    okta_group_rules: List[OktaGroupRule],
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta group rules into a format for Neo4j
    :param okta_group_rules: List of Okta group rules
    :return: List of group rule dicts
    """
    transformed_group_rules: List[Dict] = []
    logger.info(f"Transforming {len(okta_group_rules)} Okta group rules")
    for okta_group_rule in okta_group_rules:
        group_rule_props = {}
        group_rule_props["id"] = okta_group_rule.id
        group_rule_props["name"] = okta_group_rule.name
        group_rule_props["status"] = okta_group_rule.status.value
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
        # Create an entry for each group rule and for each group_id
        for group_id in okta_group_rule.actions.assign_user_to_groups.group_ids:
            match_group = {
                **group_rule_props,
                "group_id": group_id,
            }
            transformed_group_rules.append(match_group)
    return transformed_group_rules


@timeit
def _load_okta_group_rules(
    neo4j_session: neo4j.Session,
    group_rule_list: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Okta group rule information into the graph
    :param neo4j_session: session with neo4j server
    :param group_rule_list: list of group rules
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info(f"Loading {len(group_rule_list)} Okta group rules")

    load(
        neo4j_session,
        OktaGroupRuleSchema(),
        group_rule_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_group_rules(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
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
) -> List[OktaGroupRole]:
    """
    Get Okta group roles list from Okta
    :param okta_client: An Okta client object
    :param group_id: The id of the group to look up roles for
    :return: List of Okta group rules
    """
    # This won't ever be paginated
    group_roles, _, _ = await okta_client.list_group_assigned_roles(group_id)
    # By default these objects won't cleanly include group_id
    # So we add it into the object since we have them here
    for group_role in group_roles:
        group_role.assignee = group_id
    return group_roles


@timeit
def _transform_okta_group_roles(
    okta_group_roles: List[OktaGroupRole],
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta group roles into a format for Neo4j
    :param okta_group_roles: List of Okta group roles
    :return: List of group role dicts
    """
    transformed_group_roles: List[Dict] = []
    logger.info(f"Transforming {len(okta_group_roles)} Okta group roles")
    for okta_group_role in okta_group_roles:
        role_props = {}
        role_props["id"] = okta_group_role.id
        role_props["assignment_type"] = okta_group_role.assignment_type.value
        role_props["created"] = okta_group_role.created
        role_props["description"] = okta_group_role.description
        role_props["label"] = okta_group_role.label
        role_props["last_updated"] = okta_group_role.last_updated
        role_props["status"] = okta_group_role.status.value
        role_props["role_type"] = okta_group_role.type.value
        transformed_group_roles.append(role_props)
    return transformed_group_roles


@timeit
def _load_okta_group_roles(
    neo4j_session: neo4j.Session,
    group_roles_list: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Okta group roles information into the graph
    :param neo4j_session: session with neo4j server
    :param group_roles_list: list of group roles
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info(f"Loading {len(group_roles_list)} Okta group roles")

    load(
        neo4j_session,
        OktaGroupRoleSchema(),
        group_roles_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_group_roles(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
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
) -> List[OktaUser]:
    """
    Get Okta group members list from Okta
    :param okta_client: An Okta client object
    :param group_id: The id of the group to look up membership for
    :return: List of Okta Users who are members of a group
    """
    member_list: List[OktaUser] = []
    query_parameters = {"limit": 1000}
    group_users, resp, _ = await okta_client.list_group_users(
        group_id, query_parameters
    )
    member_list += group_users
    while resp.has_next():
        group_users, _ = await resp.next()
        member_list += group_users
        logger.info(f"Loaded {len(group_users)} Users for Group {group_id}")
    return member_list
