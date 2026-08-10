from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import IamV1Alpha1API
from scaleway.iam.v1alpha1 import PermissionSetScopeType
from scaleway.iam.v1alpha1 import Policy
from scaleway.iam.v1alpha1 import Rule

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayApplicationToPermissionSetMatchLink,
)
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayApplicationToProjectMatchLink,
)
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayGroupToPermissionSetMatchLink,
)
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayGroupToProjectMatchLink,
)
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayUserToPermissionSetMatchLink,
)
from cartography.models.scaleway.iam.permission_relationship import (
    ScalewayUserToProjectMatchLink,
)
from cartography.util import timeit

# Scaleway policies target exactly one principal kind; map it to the id field
# name expected by the MatchLink source matchers.
_HAS_ROLE_MATCHLINKS = {
    "user": ScalewayUserToPermissionSetMatchLink(),
    "application": ScalewayApplicationToPermissionSetMatchLink(),
    "group": ScalewayGroupToPermissionSetMatchLink(),
}
_CAN_ACCESS_MATCHLINKS = {
    "user": ScalewayUserToProjectMatchLink(),
    "application": ScalewayApplicationToProjectMatchLink(),
    "group": ScalewayGroupToProjectMatchLink(),
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    api = IamV1Alpha1API(client)
    policies = get_policies(api, org_id)
    rules_by_policy = {policy.id: get_rules(api, policy.id) for policy in policies}
    has_role, can_access = transform(policies, rules_by_policy, projects_id)
    load_permissions(neo4j_session, has_role, can_access, org_id, update_tag)
    cleanup(neo4j_session, org_id, update_tag)


@timeit
def get_policies(api: IamV1Alpha1API, org_id: str) -> list[Policy]:
    return api.list_policies_all(organization_id=org_id)


@timeit
def get_rules(api: IamV1Alpha1API, policy_id: str) -> list[Rule]:
    return api.list_rules_all(policy_id=policy_id)


def _principal(policy: Policy) -> tuple[str | None, str | None]:
    if policy.user_id:
        return "user", policy.user_id
    if policy.application_id:
        return "application", policy.application_id
    if policy.group_id:
        return "group", policy.group_id
    return None, None


def _scope_projects(rule: Rule, projects_id: list[str]) -> list[str]:
    if rule.permission_sets_scope_type == PermissionSetScopeType.PROJECTS:
        return rule.project_ids or []
    if rule.permission_sets_scope_type == PermissionSetScopeType.ORGANIZATION:
        # Organization-scoped rules apply to every project in the org.
        return projects_id
    # account_root_user (and any future scope): no project-level edge.
    return []


def transform(
    policies: list[Policy],
    rules_by_policy: dict[str, list[Rule]],
    projects_id: list[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Resolve the policy/rule graph into HAS_ROLE and CAN_ACCESS edge rows.

    Returns two dicts keyed by principal kind ("user"/"application"/"group"),
    each holding the row list for the matching MatchLink.
    """
    has_role: dict[str, list[dict[str, Any]]] = {
        "user": [],
        "application": [],
        "group": [],
    }
    can_access: dict[str, list[dict[str, Any]]] = {
        "user": [],
        "application": [],
        "group": [],
    }
    seen_roles: set[tuple[str, str, str]] = set()
    # (kind, principal_id, project_id) -> has_condition (AND across grant paths:
    # only True when every path to the project is conditional).
    access_conditions: dict[tuple[str, str, str], bool] = {}

    for policy in policies:
        kind, principal_id = _principal(policy)
        if kind is None or principal_id is None:
            continue
        id_field = f"{kind}_id"
        for rule in rules_by_policy.get(policy.id, []):
            has_condition = bool(rule.condition)
            for ps_name in rule.permission_set_names or []:
                role_key = (kind, principal_id, ps_name)
                if role_key not in seen_roles:
                    seen_roles.add(role_key)
                    has_role[kind].append(
                        {id_field: principal_id, "permission_set_name": ps_name}
                    )
            for project_id in _scope_projects(rule, projects_id):
                access_key = (kind, principal_id, project_id)
                if access_key in access_conditions:
                    access_conditions[access_key] = (
                        access_conditions[access_key] and has_condition
                    )
                else:
                    access_conditions[access_key] = has_condition

    for (kind, principal_id, project_id), has_condition in access_conditions.items():
        can_access[kind].append(
            {
                f"{kind}_id": principal_id,
                "project_id": project_id,
                "has_condition": has_condition,
            }
        )

    return has_role, can_access


@timeit
def load_permissions(
    neo4j_session: neo4j.Session,
    has_role: dict[str, list[dict[str, Any]]],
    can_access: dict[str, list[dict[str, Any]]],
    org_id: str,
    update_tag: int,
) -> None:
    for kind, matchlink in _HAS_ROLE_MATCHLINKS.items():
        load_matchlinks(
            neo4j_session,
            matchlink,
            has_role[kind],
            lastupdated=update_tag,
            _sub_resource_label="ScalewayOrganization",
            _sub_resource_id=org_id,
        )
    for kind, matchlink in _CAN_ACCESS_MATCHLINKS.items():
        load_matchlinks(
            neo4j_session,
            matchlink,
            can_access[kind],
            lastupdated=update_tag,
            _sub_resource_label="ScalewayOrganization",
            _sub_resource_id=org_id,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, org_id: str, update_tag: int) -> None:
    for matchlink in _HAS_ROLE_MATCHLINKS.values():
        GraphJob.from_matchlink(
            matchlink, "ScalewayOrganization", org_id, update_tag
        ).run(neo4j_session)
    for matchlink in _CAN_ACCESS_MATCHLINKS.values():
        GraphJob.from_matchlink(
            matchlink, "ScalewayOrganization", org_id, update_tag
        ).run(neo4j_session)
