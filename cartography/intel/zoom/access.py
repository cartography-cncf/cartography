from collections import defaultdict
from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import fetch_many
from cartography.models.zoom.group import ZoomGroupSchema
from cartography.models.zoom.privilege import ZoomRolePrivilegeSchema
from cartography.models.zoom.role import ZoomRoleSchema


def sync_groups(
    session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups = client.get_paginated("/groups", "groups")
    members: dict[str, list[str]] = defaultdict(list)
    for user in users:
        for group_id in user.get("group_ids") or []:
            members[group_id].append(user["id"])
    data = [
        {
            "id": f"{account_id}:group:{group['id']}",
            "zoom_id": group["id"],
            "name": group["name"],
            "total_members": group.get("total_members"),
            "member_ids": members.get(group["id"], []),
        }
        for group in groups
    ]
    load(
        session, ZoomGroupSchema(), data, lastupdated=update_tag, ACCOUNT_ID=account_id
    )
    GraphJob.from_node_schema(
        ZoomGroupSchema(), {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}
    ).run(session)
    return groups


def sync_roles(
    session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
) -> None:
    response = client.get("/roles")
    roles = response["roles"]
    if not isinstance(roles, list):
        raise ValueError("Zoom roles response must contain a list")
    if len(roles) != response.get("total_records", len(roles)):
        raise ValueError("Zoom roles response did not include all records")
    members: dict[str, list[str]] = defaultdict(list)
    for user in users:
        if (role_id := user.get("role_id")) is not None:
            members[role_id].append(user["id"])
    details = fetch_many(
        client, [f"/roles/{quote(role['id'], safe='')}" for role in roles]
    )
    role_data = []
    privileges = []
    for role, detail in zip(roles, details):
        node_id = f"{account_id}:role:{role['id']}"
        role_data.append(
            {
                "id": node_id,
                "zoom_id": role["id"],
                "name": role["name"],
                "description": role.get("description"),
                "total_members": role.get("total_members"),
                "member_ids": members.get(role["id"], []),
            }
        )
        restrictions = {
            scope["permission_id"]: scope["group_ids"]
            for scope in detail.get("privilege_scopes", [])
        }
        for privilege in detail["privileges"]:
            groups = restrictions.get(privilege, [])
            privileges.append(
                {
                    "id": f"{node_id}:privilege:{privilege}",
                    "privilege": privilege,
                    "role_node_id": node_id,
                    "restricted_to_groups": privilege in restrictions,
                    "group_ids": groups,
                    "group_node_ids": [
                        f"{account_id}:group:{group}" for group in groups
                    ],
                }
            )
    load(
        session,
        ZoomRoleSchema(),
        role_data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        session,
        ZoomRolePrivilegeSchema(),
        privileges,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    parameters = {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}
    GraphJob.from_node_schema(ZoomRolePrivilegeSchema(), parameters).run(session)
    GraphJob.from_node_schema(ZoomRoleSchema(), parameters).run(session)
