import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
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
    raw_roles = get_roles(client, org_id)
    roles = transform_roles(raw_roles)
    permissions = transform_permissions(raw_roles)
    load_roles(
        neo4j_session,
        permissions,
        roles,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


def transform_permissions(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        {"name": name, "description": None, "access_scope": scope}
        for name, scope in sorted(scopes.items())
    ]


@timeit
def get_roles(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    return client.get("/api/v1/orgs/current/roles", org_id=org_id)


def transform_roles(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Shape roles for ingest.

    LangSmith stores every organization-defined role under the system name CUSTOM, so the
    only way to tell a custom role from a built-in is that a custom role carries an owning
    organization_id. That distinction is materialized here as is_custom.
    """
    transformed = []
    for role in roles:
        transformed.append(
            {
                "id": role["id"],
                "name": role["name"],
                "display_name": role["display_name"],
                "description": role.get("description"),
                "access_scope": role.get("access_scope"),
                "is_custom": role.get("organization_id") is not None,
                "is_restricted": role.get("is_restricted"),
                "permissions": role.get("permissions") or [],
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


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(LangSmithRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(LangSmithPermissionSchema(), common_job_parameters).run(
        neo4j_session
    )
