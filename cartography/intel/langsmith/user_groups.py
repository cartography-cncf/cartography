"""
User groups: their members, the role they hold in each workspace, and the access policies
attached to them.

LangSmith evaluates a user's role and every user group they belong to together, so a
policy attached only to a user group still applies to its members.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import org_scoped_id
from cartography.intel.langsmith.util import resolve_ls_user_id
from cartography.models.langsmith.usergroup import LangSmithAccessPolicyToUserGroupRel
from cartography.models.langsmith.usergroup import LangSmithUserGroupGrantSchema
from cartography.models.langsmith.usergroup import LangSmithUserGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_USER_GROUPS_PATH = "/api/v1/platform/orgs/current/user-groups"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    user_lookup: dict[str, str],
    common_job_parameters: dict[str, Any],
) -> None:
    raw_groups, groups_complete = get_user_groups(client, org_id)

    members: dict[str, list[dict[str, Any]]] = {}
    grants: dict[str, list[dict[str, Any]]] = {}
    policies: dict[str, list[dict[str, Any]]] = {}
    members_complete = grants_complete = policies_complete = groups_complete
    for group in raw_groups:
        group_id = group["id"]
        members[group_id], ok = _get_group_listing(client, org_id, group_id, "members")
        members_complete = members_complete and ok
        if group.get("workspace_id"):
            # A workspace-scoped user group's only grant is the member-only access to its
            # own workspace that it was created with. LangSmith rejects listing it with 400.
            grants[group_id] = []
        else:
            grants[group_id], ok = _get_group_listing(
                client, org_id, group_id, "workspaces"
            )
            grants_complete = grants_complete and ok
        policies[group_id], ok = _get_group_listing(
            client, org_id, group_id, "access-policies"
        )
        policies_complete = policies_complete and ok

    load_user_groups(
        neo4j_session,
        transform_user_groups(raw_groups, members, user_lookup),
        transform_grants(grants, org_id),
        transform_policy_attachments(policies),
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(
        neo4j_session,
        common_job_parameters,
        members_complete,
        grants_complete,
        policies_complete,
    )


@timeit
def get_user_groups(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the organization's user groups, including the workspace-scoped ones.

    LangSmith answers 403 both when the token lacks organization:user-groups:read and when
    the organization doesn't have user groups. Both are reported incomplete, so cleanup
    keeps what an earlier sync loaded.
    """
    try:
        return client.get_cursor_paginated(_USER_GROUPS_PATH, org_id=org_id), True
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith user groups: %s", err)
        return [], err.not_found


def _get_group_listing(
    client: LangSmithClient, org_id: str, group_id: str, listing: str
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch one of a user group's sub-listings: members, workspaces or access-policies."""
    try:
        return (
            client.get_cursor_paginated(
                f"{_USER_GROUPS_PATH}/{group_id}/{listing}", org_id=org_id
            ),
            True,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith user group %s for user group %s: %s",
            listing,
            group_id,
            err,
        )
        return [], err.not_found


def transform_user_groups(
    groups: list[dict[str, Any]],
    members: dict[str, list[dict[str, Any]]],
    user_lookup: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Shape user groups for ingest, with the ls_user_id of each member.

    Members are listed by their organization identity, which the user lookup maps to an
    ls_user_id.
    """
    transformed = []
    for group in groups:
        member_ls_user_ids = set()
        for member in members.get(group["id"]) or []:
            ls_user_id = resolve_ls_user_id(member.get("identity_id"), user_lookup)
            if ls_user_id:
                member_ls_user_ids.add(ls_user_id)
            else:
                logger.debug(
                    "Skipping an unrecognized member of LangSmith user group %s",
                    group["id"],
                )
        transformed.append(
            {
                "id": group["id"],
                "name": group.get("name"),
                "description": group.get("description"),
                "workspace_id": group.get("workspace_id"),
                "parent_user_group_id": group.get("parent_user_group_id"),
                "idp_group_name": group.get("idp_group_name"),
                "idp_sync_enabled": group.get("idp_sync_enabled"),
                "created_at": group.get("created_at"),
                "updated_at": group.get("updated_at"),
                "member_ls_user_ids": sorted(member_ls_user_ids),
            }
        )
    return transformed


def transform_grants(
    grants: dict[str, list[dict[str, Any]]], org_id: str
) -> list[dict[str, Any]]:
    """Flatten each user group's workspace grants into (user group, workspace, role)."""
    return [
        {
            "id": f"{group_id}|{grant['workspace_id']}",
            "user_group_id": group_id,
            "workspace_id": grant["workspace_id"],
            "role_id": org_scoped_id(org_id, grant.get("role_id")),
            "role_name": grant.get("role_name"),
            "created_at": grant.get("created_at"),
            "updated_at": grant.get("updated_at"),
        }
        for group_id, group_grants in grants.items()
        for grant in group_grants
    ]


def transform_policy_attachments(
    policies: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Collapse each user group's attachments of the same policy into one record.

    A policy can be attached for all of the user group's workspaces, which the API reports
    with no workspace_id, and for specific workspaces at the same time.
    """
    attachments: dict[tuple[str, str], dict[str, Any]] = {}
    for group_id, group_policies in policies.items():
        for policy in group_policies:
            attachment = attachments.setdefault(
                (policy["id"], group_id),
                {
                    "access_policy_id": policy["id"],
                    "user_group_id": group_id,
                    "all_workspaces": False,
                    "workspace_ids": set(),
                },
            )
            if policy.get("workspace_id"):
                attachment["workspace_ids"].add(policy["workspace_id"])
            else:
                attachment["all_workspaces"] = True
    return [
        {**attachment, "workspace_ids": sorted(attachment["workspace_ids"])}
        for attachment in attachments.values()
    ]


@timeit
def load_user_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    grants: list[dict[str, Any]],
    attachments: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithUserGroupSchema(),
        groups,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithUserGroupGrantSchema(),
        grants,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load_matchlinks(
        neo4j_session,
        LangSmithAccessPolicyToUserGroupRel(),
        attachments,
        lastupdated=update_tag,
        _sub_resource_label="LangSmithOrganization",
        _sub_resource_id=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    members_complete: bool,
    grants_complete: bool,
    policies_complete: bool,
) -> None:
    cleanup_if_complete(
        neo4j_session,
        LangSmithUserGroupGrantSchema(),
        grants_complete,
        common_job_parameters,
    )
    # The user group cleanup also prunes MEMBER_OF edges, so it needs every member
    # listing to have been read.
    cleanup_if_complete(
        neo4j_session,
        LangSmithUserGroupSchema(),
        members_complete,
        common_job_parameters,
    )
    if not policies_complete:
        logger.warning(
            "Skipping LangSmith user group policy attachment cleanup for organization "
            "%s: collection was incomplete.",
            common_job_parameters["ORG_ID"],
        )
        return
    GraphJob.from_matchlink(
        LangSmithAccessPolicyToUserGroupRel(),
        "LangSmithOrganization",
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
