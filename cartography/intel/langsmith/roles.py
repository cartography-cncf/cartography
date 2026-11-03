import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import org_scoped_id
from cartography.models.langsmith.permission import LangSmithPermissionSchema
from cartography.models.langsmith.role import LangSmithRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_roles, complete = get_roles(client, org_id)
    roles = transform_roles(raw_roles, org_id)
    permissions = transform_permissions(raw_roles, org_id)
    load_roles(
        neo4j_session,
        permissions,
        roles,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    # Permissions are derived from the roles, so both depend on the same listing.
    cleanup_if_complete(
        neo4j_session, LangSmithRoleSchema(), complete, common_job_parameters
    )
    cleanup_if_complete(
        neo4j_session, LangSmithPermissionSchema(), complete, common_job_parameters
    )


def _permission_id(org_id: str, permission: str) -> str:
    return f"{org_id}|{permission}"


def transform_permissions(
    roles: list[dict[str, Any]], org_id: str
) -> list[dict[str, Any]]:
    """
    Derive the permission catalog from the permissions the roles grant.

    /api/v1/orgs/permissions would be the authoritative source, including each
    permission's description, but it is gated on a UI session JWT and returns 403 for a
    personal access token. Every permission that any role grants still appears here, which
    is what the GRANTS edges need; only the human-readable descriptions are lost.

    A permission's access_scope is taken from the scope of a role that grants it.
    """
    scopes: dict[str, str | None] = {}
    for role in roles:
        for permission in role.get("permissions") or []:
            if scopes.get(permission) is None:
                scopes[permission] = role.get("access_scope")
    return [
        {
            "id": _permission_id(org_id, name),
            "name": name,
            "access_scope": scope,
        }
        for name, scope in sorted(scopes.items())
    ]


@timeit
def get_roles(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the role catalog, tolerating a credential that cannot read it.

    Without roles, memberships, keys and policies still load; only their role edges are
    missing.
    """
    try:
        return client.get("/api/v1/orgs/current/roles", org_id=org_id), True
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith roles: %s", err)
        return [], err.not_found


def transform_roles(roles: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    """
    Shape roles for ingest.

    LangSmith stores every organization-defined role under the system name CUSTOM, so the
    only way to tell a custom role from a built-in is that a custom role carries an owning
    organization_id. That distinction is materialized here as is_custom.

    Built-in roles carry no organization_id and keep the same UUID in every organization,
    so role nodes are keyed by organization as well.
    """
    transformed = []
    for role in roles:
        transformed.append(
            {
                "id": org_scoped_id(org_id, role["id"]),
                "role_id": role["id"],
                "name": role["name"],
                "display_name": role["display_name"],
                "description": role.get("description"),
                "access_scope": role.get("access_scope"),
                "is_custom": role.get("organization_id") is not None,
                "role_type": (
                    "custom" if role.get("organization_id") is not None else "builtin"
                ),
                "is_restricted": role.get("is_restricted"),
                "permission_ids": [
                    _permission_id(org_id, permission)
                    for permission in role.get("permissions") or []
                ],
            }
        )
    return transformed


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    permissions: list[dict[str, Any]],
    roles: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    # Permissions must land before roles so the role GRANTS edges have targets to match.
    load(
        neo4j_session,
        LangSmithPermissionSchema(),
        permissions,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithRoleSchema(),
        roles,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
