import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.rbac import AnthropicRbacGroupSchema
from cartography.models.anthropic.rbac import AnthropicRbacRolePermissionSchema
from cartography.models.anthropic.rbac import AnthropicRbacRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Every RBAC endpoint requires this opt-in. It must be sent per request rather than
# on the session: other Anthropic betas are mutually exclusive with each other.
_BETA_HEADERS = {"anthropic-beta": "ce-user-management-2026-07-13"}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync RBAC groups, roles and role permissions.

    The RBAC API is a Claude Enterprise beta. A non-Enterprise organization gets a
    403 or 404 rather than an empty list, so the whole sync is best-effort: it logs
    and returns instead of failing the module.
    """
    roles = get_roles(api_session, common_job_parameters["BASE_URL"])
    permissions: list[dict[str, Any]] = []
    for role in roles:
        permissions.extend(
            transform_permissions(
                role["id"],
                get_role_permissions(
                    api_session,
                    common_job_parameters["BASE_URL"],
                    role["id"],
                ),
            )
        )
    load_roles(
        neo4j_session,
        roles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_role_permissions(
        neo4j_session,
        permissions,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )

    groups = get_groups(api_session, common_job_parameters["BASE_URL"])
    known_roles = get_known_role_ids(
        neo4j_session,
        [group["id"] for group in groups if group.get("roles") is None],
    )
    for group in groups:
        transform_group(
            group,
            get_group_members(
                api_session,
                common_job_parameters["BASE_URL"],
                group["id"],
            ),
            known_roles.get(group["id"]),
        )
    load_groups(
        neo4j_session,
        groups,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_roles(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/rbac_roles",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


@timeit
def get_role_permissions(
    api_session: requests.Session,
    base_url: str,
    role_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/rbac_roles/{role_id}/permissions",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


@timeit
def get_groups(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/rbac_groups",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


@timeit
def get_group_members(
    api_session: requests.Session,
    base_url: str,
    group_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/organizations/rbac_groups/{group_id}/members",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


def transform_permissions(
    role_id: str,
    permissions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Give each permission a stable id.

    The API returns none, so it is synthesised from the fields that make a grant
    unique: the role, the action, and the resource it applies to.
    """
    results: list[dict[str, Any]] = []
    for permission in permissions:
        resource = permission.get("resource") or {}
        resource_key = "/".join(
            str(resource[field])
            for field in (
                "type",
                "organization_id",
                "connector_id",
                "tool_name",
                "scope",
            )
            if resource.get(field)
        )
        results.append(
            {
                **permission,
                "id": f"{role_id}/{permission.get('action')}/{resource_key}",
                "role_id": role_id,
            }
        )
    return results


@timeit
def get_known_role_ids(
    neo4j_session: neo4j.Session,
    group_ids: list[str],
) -> dict[str, list[str]]:
    """Read back the roles the graph already holds for these groups.

    Used only when the API reports a group's roles as unavailable. Re-writing the
    known ids keeps the existing edges and refreshes their lastupdated, which is what
    stops the cleanup job from deleting them.
    """
    if not group_ids:
        return {}
    records = neo4j_session.run(
        """
        MATCH (g:AnthropicRbacGroup)-[:HAS_ROLE]->(r:AnthropicRbacRole)
        WHERE g.id IN $group_ids
        RETURN g.id AS group_id, collect(r.id) AS role_ids
        """,
        group_ids=group_ids,
    )
    return {record["group_id"]: record["role_ids"] for record in records}


def transform_group(
    group: dict[str, Any],
    members: list[dict[str, Any]],
    known_role_ids: list[str] | None = None,
) -> None:
    """Attach member ids, and normalise the roles field.

    A null `roles` means the role data was temporarily unavailable, not that the
    group holds no roles. Writing an empty list would let the cleanup job delete the
    group's real HAS_ROLE edges, turning a transient API failure into an
    under-reported set of permissions. Carry forward what the graph already knows
    instead, so the edges survive until a sync reads the field successfully.
    """
    group["members"] = [m["user_id"] for m in members]
    if group.get("roles") is None:
        logger.warning(
            "Anthropic RBAC group %s returned null roles, meaning the role data was "
            "temporarily unavailable. Carrying forward the %d role(s) already in the "
            "graph.",
            group["id"],
            len(known_role_ids or []),
        )
        group["roles"] = known_role_ids or []


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicRbacRoleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def load_role_permissions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicRbacRolePermissionSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicRbacGroupSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicRbacGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    # Permissions before roles: they hang off the roles.
    GraphJob.from_node_schema(
        AnthropicRbacRolePermissionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(AnthropicRbacRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
