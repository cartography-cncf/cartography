import json
import logging
from typing import Any
from urllib.parse import unquote

import neo4j
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tencentcloud.util import build_client
from cartography.intel.tencentcloud.util import call
from cartography.intel.tencentcloud.util import paginate_page
from cartography.models.tencentcloud.cam_access_key import (
    TencentCloudCAMAccessKeySchema,
)
from cartography.models.tencentcloud.cam_group import TencentCloudCAMGroupSchema
from cartography.models.tencentcloud.cam_policy import TencentCloudCAMPolicySchema
from cartography.models.tencentcloud.cam_role import TencentCloudCAMRoleSchema
from cartography.models.tencentcloud.cam_user import TencentCloudCAMUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GetSecurityLastUsed accepts at most this many SecretIds per call.
_LAST_USED_BATCH_SIZE = 10

# ListPolicies reports the policy type as 1 (custom) or 2 (preset); attachment APIs
# report it as "User" or "QCS".
_POLICY_TYPES = {
    1: "custom",
    2: "preset",
    "1": "custom",
    "2": "preset",
    "User": "custom",
    "QCS": "preset",
}


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@timeit
def get_users(client: Any) -> list[dict[str, Any]]:
    # ListUsers is not paginated; it returns every sub-user in one response.
    return call(client, "ListUsers").get("Data") or []


@timeit
def get_access_keys(client: Any, user_uin: str) -> list[dict[str, Any]]:
    response = call(client, "ListAccessKeys", {"TargetUin": int(user_uin)})
    return response.get("AccessKeys") or []


@timeit
def get_access_keys_last_used(
    client: Any,
    secret_ids: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for start in range(0, len(secret_ids), _LAST_USED_BATCH_SIZE):
        batch = secret_ids[start : start + _LAST_USED_BATCH_SIZE]
        response = call(client, "GetSecurityLastUsed", {"SecretIdList": batch})
        rows.extend(response.get("SecretIdLastUsedRows") or [])
    return rows


@timeit
def get_groups(client: Any) -> list[dict[str, Any]]:
    return paginate_page(client, "ListGroups", "GroupInfo")


@timeit
def get_group_members(client: Any, group_id: str) -> list[dict[str, Any]]:
    return paginate_page(
        client,
        "ListUsersForGroup",
        "UserInfo",
        {"GroupId": int(group_id)},
    )


@timeit
def get_roles(client: Any) -> list[dict[str, Any]]:
    return paginate_page(client, "DescribeRoleList", "List")


@timeit
def get_custom_policies(client: Any) -> list[dict[str, Any]]:
    """Return every custom policy with its policy document."""
    policies = paginate_page(client, "ListPolicies", "List", {"Scope": "Local"})
    for policy in policies:
        detail = call(client, "GetPolicy", {"PolicyId": policy["PolicyId"]})
        policy["PolicyDocument"] = detail.get("PolicyDocument")
        policy["UpdateTime"] = detail.get("UpdateTime")
    return policies


@timeit
def get_user_policies(client: Any, user_uin: str) -> list[dict[str, Any]]:
    """Return the policies attached directly to a user (not those inherited from groups)."""
    return paginate_page(
        client,
        "ListAttachedUserPolicies",
        "List",
        {"TargetUin": int(user_uin)},
    )


@timeit
def get_group_policies(client: Any, group_id: str) -> list[dict[str, Any]]:
    return paginate_page(
        client,
        "ListAttachedGroupPolicies",
        "List",
        {"TargetGroupId": int(group_id)},
    )


@timeit
def get_role_policies(client: Any, role_id: str) -> list[dict[str, Any]]:
    return paginate_page(
        client,
        "ListAttachedRolePolicies",
        "List",
        {"RoleId": role_id},
    )


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------


def _to_bool(value: Any) -> bool | None:
    return None if value is None else bool(value)


def transform_users(raw_users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(user["Uin"]),
            "uid": str(user["Uid"]) if user.get("Uid") is not None else None,
            "name": user["Name"],
            "nick_name": user.get("NickName") or None,
            "remark": user.get("Remark") or None,
            "email": user.get("Email") or None,
            "console_login": _to_bool(user.get("ConsoleLogin")),
            "create_time": user.get("CreateTime"),
        }
        for user in raw_users
    ]


def transform_access_keys(
    raw_keys_by_user: dict[str, list[dict[str, Any]]],
    last_used_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    last_used = {row["SecretId"]: row.get("LastUsedDate") for row in last_used_rows}
    keys = []
    for user_uin, raw_keys in raw_keys_by_user.items():
        for key in raw_keys:
            keys.append(
                {
                    "id": key["AccessKeyId"],
                    "status": key.get("Status"),
                    "description": key.get("Description") or None,
                    "create_time": key.get("CreateTime"),
                    "last_used_date": last_used.get(key["AccessKeyId"]) or None,
                    "user_uin": user_uin,
                },
            )
    return keys


def transform_groups(
    raw_groups: list[dict[str, Any]],
    members_by_group: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    return [
        {
            "id": str(group["GroupId"]),
            "name": group["GroupName"],
            "remark": group.get("Remark") or None,
            "create_time": group.get("CreateTime"),
            "member_uins": [
                str(member["Uin"])
                for member in members_by_group.get(str(group["GroupId"]), [])
            ],
        }
        for group in raw_groups
    ]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def parse_trust_policy(document: str | None) -> tuple[list[str], list[str]]:
    """Return the (principals, services) a role trust policy allows.

    Only `allow` statements are read. CAM may return the document URL-encoded.
    """
    if not document:
        return [], []
    text = document.strip()
    if not text.startswith("{"):
        text = unquote(text)
    policy = json.loads(text)
    statements = policy.get("statement") or []
    if isinstance(statements, dict):
        statements = [statements]
    principals: set[str] = set()
    services: set[str] = set()
    for statement in statements:
        if str(statement.get("effect", "")).lower() != "allow":
            continue
        principal = statement.get("principal") or {}
        if not isinstance(principal, dict):
            principals.update(_as_list(principal))
            continue
        principals.update(_as_list(principal.get("qcs")))
        services.update(_as_list(principal.get("service")))
    return sorted(principals), sorted(services)


def transform_roles(raw_roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roles = []
    for role in raw_roles:
        principals, services = parse_trust_policy(role.get("PolicyDocument"))
        roles.append(
            {
                "id": str(role["RoleId"]),
                "name": role["RoleName"],
                "arn": role.get("RoleArn"),
                "description": role.get("Description") or None,
                "role_type": role.get("RoleType"),
                "console_login": _to_bool(role.get("ConsoleLogin")),
                "session_duration": role.get("SessionDuration"),
                "trust_policy": role.get("PolicyDocument"),
                "trusted_principals": principals,
                "trusted_services": services,
                "add_time": role.get("AddTime"),
                "update_time": role.get("UpdateTime"),
            },
        )
    return roles


def transform_policies(
    account_id: str,
    custom_policies: list[dict[str, Any]],
    user_policies: dict[str, list[dict[str, Any]]],
    group_policies: dict[str, list[dict[str, Any]]],
    role_policies: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Merge custom policies with every policy attached to a user, group, or role."""
    policies: dict[str, dict[str, Any]] = {}

    def _get_or_create(raw: dict[str, Any], policy_type: Any) -> dict[str, Any]:
        policy_id = str(raw["PolicyId"])
        if policy_id not in policies:
            policies[policy_id] = {
                "id": f"{account_id}:{policy_id}",
                "policy_id": policy_id,
                "name": raw.get("PolicyName"),
                "type": _POLICY_TYPES.get(policy_type),
                "description": raw.get("Description") or raw.get("Remark") or None,
                "policy_document": None,
                "service_type": None,
                "add_time": None,
                "update_time": None,
                "attached_user_uins": [],
                "attached_group_ids": [],
                "attached_role_ids": [],
            }
        return policies[policy_id]

    for raw in custom_policies:
        policy = _get_or_create(raw, raw.get("Type"))
        policy["policy_document"] = raw.get("PolicyDocument")
        policy["service_type"] = raw.get("ServiceType") or None
        policy["add_time"] = raw.get("AddTime")
        policy["update_time"] = raw.get("UpdateTime")

    attachments = (
        (user_policies, "attached_user_uins"),
        (group_policies, "attached_group_ids"),
        (role_policies, "attached_role_ids"),
    )
    for policies_by_principal, field in attachments:
        for principal_id, raw_policies in policies_by_principal.items():
            for raw in raw_policies:
                policy = _get_or_create(
                    raw,
                    raw.get("PolicyType") or raw.get("StrategyType"),
                )
                policy[field].append(principal_id)

    return list(policies.values())


# ---------------------------------------------------------------------------
# LOAD / CLEANUP
# ---------------------------------------------------------------------------


def _load(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d %s nodes for Tencent Cloud account %s.",
        len(data),
        schema.label,
        account_id,
    )
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    for schema in (
        TencentCloudCAMPolicySchema(),
        TencentCloudCAMAccessKeySchema(),
        TencentCloudCAMGroupSchema(),
        TencentCloudCAMRoleSchema(),
        TencentCloudCAMUserSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


# ---------------------------------------------------------------------------
# SYNC
# ---------------------------------------------------------------------------


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync CAM users, API keys, groups, roles, and policies.

    CAM is a global service, so this runs once per account rather than per region.
    """
    client = build_client(credential, "cam")

    raw_users = get_users(client)
    users = transform_users(raw_users)
    _load(neo4j_session, TencentCloudCAMUserSchema(), users, account_id, update_tag)

    raw_keys_by_user = {
        user["id"]: get_access_keys(client, user["id"]) for user in users
    }
    secret_ids = [
        key["AccessKeyId"] for keys in raw_keys_by_user.values() for key in keys
    ]
    last_used_rows = get_access_keys_last_used(client, secret_ids) if secret_ids else []
    access_keys = transform_access_keys(raw_keys_by_user, last_used_rows)
    _load(
        neo4j_session,
        TencentCloudCAMAccessKeySchema(),
        access_keys,
        account_id,
        update_tag,
    )

    raw_groups = get_groups(client)
    group_ids = [str(group["GroupId"]) for group in raw_groups]
    members_by_group = {
        group_id: get_group_members(client, group_id) for group_id in group_ids
    }
    groups = transform_groups(raw_groups, members_by_group)
    _load(neo4j_session, TencentCloudCAMGroupSchema(), groups, account_id, update_tag)

    raw_roles = get_roles(client)
    roles = transform_roles(raw_roles)
    _load(neo4j_session, TencentCloudCAMRoleSchema(), roles, account_id, update_tag)

    # Policies are loaded last so their POLICY edges find every user, group, and role.
    policies = transform_policies(
        account_id,
        get_custom_policies(client),
        {user["id"]: get_user_policies(client, user["id"]) for user in users},
        {group_id: get_group_policies(client, group_id) for group_id in group_ids},
        {role["id"]: get_role_policies(client, role["id"]) for role in roles},
    )
    _load(
        neo4j_session,
        TencentCloudCAMPolicySchema(),
        policies,
        account_id,
        update_tag,
    )

    cleanup(neo4j_session, common_job_parameters)
