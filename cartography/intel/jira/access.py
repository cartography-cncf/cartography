from typing import Any
from urllib.parse import quote
from urllib.parse import urlsplit

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jira.util import JiraClient
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.jira.access import JiraGroupSchema
from cartography.models.jira.access import JiraPermissionGrantSchema
from cartography.models.jira.access import JiraProjectRoleSchema
from cartography.models.jira.access import JiraProjectSchema
from cartography.models.jira.access import JiraTenantSchema
from cartography.models.jira.access import JiraUserSchema
from cartography.util import timeit


@timeit
def get(client: JiraClient) -> dict[str, Any]:
    permissions = client.get("mypermissions", permissions="ADMINISTER,BROWSE_USERS")[
        "permissions"
    ]
    if not all(
        permissions[p]["havePermission"] for p in ("ADMINISTER", "BROWSE_USERS")
    ):
        raise PermissionError(
            "Jira ingestion requires Administer Jira and Browse users and groups"
        )
    info = client.get("serverInfo")
    if info["deploymentType"] != "Cloud":
        raise ValueError("This module supports Jira Cloud only")
    users = client.pages("users/search")
    groups = client.pages("group/bulk")
    admin_groups = {
        access: client.pages("group/bulk", accessType=access)
        for access in ("admin", "site-admin")
    }
    memberships = {
        group["groupId"]: client.pages(
            "group/member", groupId=group["groupId"], includeInactiveUsers="true"
        )
        for group in groups
    }
    projects = client.pages("project/search", expand="lead", status="live")
    roles = {}
    schemes: dict[str, Any] = {}
    for project in projects:
        project_id = quote(project["id"], safe="")
        roles[project["id"]] = [
            client.get(f"project/{project_id}/role/{quote(str(role['id']), safe='')}")
            for role in client.get(f"project/{project_id}/roledetails")
        ]
        # Team-managed projects do not use the company-managed permission schemes.
        if project.get("style") == "next-gen":
            continue
        scheme_id = str(client.get(f"project/{project_id}/permissionscheme")["id"])
        project["permission_scheme_id"] = scheme_id
        if scheme_id not in schemes:
            schemes[scheme_id] = client.get(
                f"permissionscheme/{quote(scheme_id, safe='')}", expand="all"
            )
    return {
        "info": info,
        "users": users,
        "groups": groups,
        "admin_groups": admin_groups,
        "memberships": memberships,
        "projects": projects,
        "roles": roles,
        "schemes": schemes,
    }


def resource_id(tenant_id: str, kind: str, *parts: Any) -> str:
    if any(part is None or str(part) in ("", "unknown") for part in parts):
        raise ValueError("Jira returned a resource without a stable identifier")
    return ":".join([tenant_id, kind, *(quote(str(p), safe="") for p in parts)])


def _is_deleted_user(user: dict[str, Any]) -> bool:
    # Jira documents "unknown" as a corrupted deleted-user tombstone. An
    # unavailable/current profile must still fail rather than permit cleanup.
    if user["accountId"] != "unknown":
        return False
    if user.get("active") is not False:
        raise ValueError(
            "Jira returned an unavailable user without a stable identifier"
        )
    return True


@timeit
def transform(raw: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    groups = {g["groupId"]: g for g in raw["groups"]}
    admin_types: dict[str, list[str]] = {g: [] for g in groups}
    for access, admin_groups in raw["admin_groups"].items():
        for group in admin_groups:
            # A concurrent group change makes this snapshot unsafe to clean up.
            admin_types[group["groupId"]].append(access)
    group_names = {g["name"]: g["groupId"] for g in groups.values()}
    users = {u["accountId"]: dict(u) for u in raw["users"] if not _is_deleted_user(u)}
    user_groups: dict[str, list[str]] = {}
    for group_id, members in raw["memberships"].items():
        for user in members:
            if _is_deleted_user(user):
                continue
            account_id = user["accountId"]
            users.setdefault(account_id, {}).update(user)
            user_groups.setdefault(account_id, []).append(
                resource_id(tenant_id, "group", group_id)
            )
    projects = []
    roles = []
    grants = []
    for project in raw["projects"]:
        project_id = resource_id(tenant_id, "project", project["id"])
        lead = project.get("lead")
        if lead is not None and _is_deleted_user(lead):
            lead = None
        if lead:
            users.setdefault(lead["accountId"], {}).update(lead)
        scheme_id = project.get("permission_scheme_id")
        projects.append(
            {
                "id": project_id,
                "project_id": project["id"],
                "key": project["key"],
                "name": project["name"],
                "project_type": project.get("projectTypeKey"),
                "style": project.get("style"),
                "permission_scheme_id": scheme_id,
                "permission_scheme_supported": project.get("style") != "next-gen",
                "lead_id": (
                    resource_id(tenant_id, "user", lead["accountId"]) if lead else None
                ),
            }
        )
        for role in raw["roles"][project["id"]]:
            role_users = []
            role_groups = []
            for actor in role["actors"]:
                if actor["type"] == "atlassian-user-role-actor":
                    account_id = actor["actorUser"]["accountId"]
                    if account_id == "unknown":
                        continue
                    users.setdefault(
                        account_id,
                        {
                            "accountId": account_id,
                            "displayName": actor.get("displayName"),
                        },
                    )
                    role_users.append(resource_id(tenant_id, "user", account_id))
                elif actor["type"] == "atlassian-group-role-actor":
                    group_id = actor["actorGroup"]["groupId"]
                    # Require the group to be present in the completed group inventory.
                    groups[group_id]
                    role_groups.append(resource_id(tenant_id, "group", group_id))
                else:
                    raise ValueError(
                        f"Unsupported Jira role actor type: {actor['type']}"
                    )
            roles.append(
                {
                    "id": resource_id(tenant_id, "role", project["id"], role["id"]),
                    "role_id": str(role["id"]),
                    "project_id": project_id,
                    "name": role["name"],
                    "description": role.get("description"),
                    "admin": role.get("admin"),
                    "user_ids": role_users,
                    "group_ids": role_groups,
                }
            )
        if scheme_id is None:
            continue
        for grant in raw["schemes"][scheme_id]["permissions"]:
            holder = grant["holder"]
            holder_type = holder["type"]
            value = holder.get("value") or holder.get("parameter")
            user_id = group_id = role_id = None
            if holder_type == "user" and value != "unknown":
                users.setdefault(value, {"accountId": value})
                user_id = resource_id(tenant_id, "user", value)
            elif holder_type == "group":
                # Empty group holders mean any logged-in user; keep the raw fact.
                if value:
                    group_id = holder.get("value") or group_names[holder["parameter"]]
                    groups[group_id]
                    group_id = resource_id(tenant_id, "group", group_id)
            elif holder_type == "projectRole":
                role_id = resource_id(tenant_id, "role", project["id"], value)
            elif holder_type == "projectLead" and lead:
                user_id = resource_id(tenant_id, "user", lead["accountId"])
            grants.append(
                {
                    "id": resource_id(
                        tenant_id, "grant", project["id"], scheme_id, grant["id"]
                    ),
                    "grant_id": str(grant["id"]),
                    "scheme_id": scheme_id,
                    "project_id": project_id,
                    "permission": grant["permission"],
                    "holder_type": holder_type,
                    "holder_parameter": holder.get("parameter"),
                    "holder_value": holder.get("value"),
                    "user_id": user_id,
                    "group_id": group_id,
                    "role_id": role_id,
                }
            )
    return {
        "tenant": [
            {
                "id": tenant_id,
                "name": raw["info"].get("serverTitle"),
                "url": raw["info"]["baseUrl"],
                "domain": urlsplit(raw["info"]["baseUrl"]).hostname,
            }
        ],
        "groups": [
            {
                "id": resource_id(tenant_id, "group", gid),
                "group_id": gid,
                "name": g["name"],
                "admin_access_types": sorted(admin_types[gid]),
                "admin_tenant_id": tenant_id if admin_types[gid] else None,
            }
            for gid, g in groups.items()
        ],
        "users": [
            {
                "id": resource_id(tenant_id, "user", uid),
                "account_id": uid,
                "display_name": u.get("displayName"),
                "email": u.get("emailAddress"),
                "active": u.get("active"),
                "account_type": u.get("accountType"),
                "group_ids": user_groups.get(uid, []),
            }
            for uid, u in users.items()
        ],
        "projects": projects,
        "roles": roles,
        "grants": grants,
    }


@timeit
def sync(neo4j_session: neo4j.Session, client: JiraClient, update_tag: int) -> None:
    # Fetch and validate the entire site first. Failed or partial reads cannot erase prior data.
    data = transform(get(client), client.cloud_id)
    load(neo4j_session, JiraTenantSchema(), data["tenant"], lastupdated=update_tag)
    schemas: tuple[tuple[CartographyNodeSchema, str], ...] = (
        (JiraGroupSchema(), "groups"),
        (JiraUserSchema(), "users"),
        (JiraProjectSchema(), "projects"),
        (JiraProjectRoleSchema(), "roles"),
        (JiraPermissionGrantSchema(), "grants"),
    )
    for schema, key in schemas:
        load(
            neo4j_session,
            schema,
            data[key],
            lastupdated=update_tag,
            TENANT_ID=client.cloud_id,
        )
    for schema, _ in reversed(schemas):
        GraphJob.from_node_schema(
            schema, {"UPDATE_TAG": update_tag, "TENANT_ID": client.cloud_id}
        ).run(neo4j_session)
