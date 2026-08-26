import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.notion.util import get_scim_paginated
from cartography.intel.notion.util import scoped_id
from cartography.models.notion.group import NotionGroupSchema
from cartography.models.notion.manager import NotionUserReportsToMatchLink
from cartography.models.notion.scim_user import NotionSCIMUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

ENTERPRISE_USER_EXTENSION = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
NOTION_USER_EXTENSION = "urn:ietf:params:scim:schemas:extension:notion:2.0:User"
SCIM_USER_FIELDS = (
    "active",
    "workspace_role",
    "scim_external_id",
    "title",
    "user_type",
    "locale",
    "preferred_language",
    "department",
    "division",
    "cost_center",
    "organization",
    "employee_number",
    "manager_email",
    "is_workspace_member",
)


def get(
    scim_session: requests.Session,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    users = get_scim_paginated(scim_session, "Users")
    groups = get_scim_paginated(scim_session, "Groups")
    return users, groups


def _object(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Notion SCIM {field} must be an object")
    return value


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Notion SCIM {field} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Notion SCIM {field} must be a string")
    return value.strip() or None


def transform_users(
    scim_users: list[dict[str, Any]],
    public_people: list[dict[str, Any]],
    workspace_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    enriched_by_id = {
        person["notion_user_id"]: {
            **person,
            **dict.fromkeys(SCIM_USER_FIELDS),
        }
        for person in public_people
    }
    manager_emails: dict[str, str] = {}
    email_to_ids: dict[str, list[str]] = {}
    seen_ids: set[str] = set()

    for user in scim_users:
        notion_user_id = _required_string(user.get("id"), "user id")
        if notion_user_id in seen_ids:
            raise ValueError(
                f"Notion SCIM returned duplicate user ID {notion_user_id!r}"
            )
        seen_ids.add(notion_user_id)

        email = _required_string(user.get("userName"), "userName").lower()
        name = _object(user.get("name"), "user name")
        formatted_name = _optional_string(name.get("formatted"), "name.formatted")
        if formatted_name is None:
            formatted_name = (
                " ".join(
                    part
                    for part in (
                        _optional_string(name.get("givenName"), "name.givenName"),
                        _optional_string(name.get("familyName"), "name.familyName"),
                    )
                    if part
                )
                or None
            )

        enterprise = _object(
            user.get(ENTERPRISE_USER_EXTENSION),
            "enterprise user extension",
        )
        notion = _object(user.get(NOTION_USER_EXTENSION), "Notion user extension")
        manager = _object(enterprise.get("manager"), "manager")
        manager_email = _optional_string(manager.get("value"), "manager.value")
        if manager_email:
            manager_email = manager_email.lower()

        active = user.get("active")
        if active is not None and not isinstance(active, bool):
            raise ValueError("Notion SCIM active must be a boolean")

        existing = enriched_by_id.get(notion_user_id, {})
        user_id = scoped_id(workspace_id, notion_user_id)
        enriched_by_id[notion_user_id] = {
            "id": user_id,
            "notion_user_id": notion_user_id,
            "name": formatted_name or existing.get("name"),
            "email": email,
            "active": active,
            "workspace_role": _optional_string(notion.get("role"), "role"),
            "scim_external_id": _optional_string(
                user.get("externalId"),
                "externalId",
            ),
            "title": _optional_string(user.get("title"), "title"),
            "user_type": _optional_string(user.get("userType"), "userType"),
            "locale": _optional_string(user.get("locale"), "locale"),
            "preferred_language": _optional_string(
                user.get("preferredLanguage"),
                "preferredLanguage",
            ),
            "department": _optional_string(
                enterprise.get("department"),
                "department",
            ),
            "division": _optional_string(enterprise.get("division"), "division"),
            "cost_center": _optional_string(
                enterprise.get("costCenter"),
                "costCenter",
            ),
            "organization": _optional_string(
                enterprise.get("organization"),
                "organization",
            ),
            "employee_number": _optional_string(
                enterprise.get("employeeNumber"),
                "employeeNumber",
            ),
            "manager_email": manager_email,
            "is_workspace_member": True,
        }
        email_to_ids.setdefault(email, []).append(user_id)
        if manager_email:
            manager_emails[user_id] = manager_email

    manager_relationships = [
        {"source_id": user_id, "target_id": email_to_ids[manager_email][0]}
        for user_id, manager_email in manager_emails.items()
        if len(email_to_ids.get(manager_email, [])) == 1
    ]
    return list(enriched_by_id.values()), manager_relationships


def transform_groups(
    scim_groups: list[dict[str, Any]],
    workspace_id: str,
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for group in scim_groups:
        notion_group_id = _required_string(group.get("id"), "group id")
        if notion_group_id in seen_ids:
            raise ValueError(
                f"Notion SCIM returned duplicate group ID {notion_group_id!r}"
            )
        seen_ids.add(notion_group_id)

        members = group.get("members", [])
        if not isinstance(members, list) or not all(
            isinstance(member, dict) for member in members
        ):
            raise ValueError("Notion SCIM group members must be a list of objects")
        member_ids = [
            scoped_id(
                workspace_id,
                _required_string(member.get("value"), "group member value"),
            )
            for member in members
        ]
        groups.append(
            {
                "id": scoped_id(workspace_id, notion_group_id),
                "notion_group_id": notion_group_id,
                "name": _required_string(group.get("displayName"), "displayName"),
                "scim_external_id": _optional_string(
                    group.get("externalId"),
                    "externalId",
                ),
                "member_ids": list(dict.fromkeys(member_ids)),
            },
        )
    return groups


def load_scim_data(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    manager_relationships: list[dict[str, str]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NotionSCIMUserSchema(),
        users,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )
    load(
        neo4j_session,
        NotionGroupSchema(),
        groups,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )
    load_matchlinks(
        neo4j_session,
        NotionUserReportsToMatchLink(),
        manager_relationships,
        lastupdated=update_tag,
        _sub_resource_label="NotionWorkspace",
        _sub_resource_id=workspace_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NotionGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        NotionUserReportsToMatchLink(),
        "NotionWorkspace",
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    scim_session: requests.Session,
    public_people: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Notion SCIM sync for workspace %s", workspace_id)
    raw_users, raw_groups = get(scim_session)
    users, manager_relationships = transform_users(
        raw_users,
        public_people,
        workspace_id,
    )
    groups = transform_groups(raw_groups, workspace_id)
    load_scim_data(
        neo4j_session,
        users,
        groups,
        manager_relationships,
        workspace_id,
        update_tag,
    )
    cleanup(neo4j_session, workspace_id, common_job_parameters)
    logger.info("Completed Notion SCIM sync for workspace %s", workspace_id)
