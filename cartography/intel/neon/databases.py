import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_json
from cartography.intel.neon.util import iso_to_datetime
from cartography.models.neon.database import NeonDatabaseSchema
from cartography.models.neon.role import NeonRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project: dict[str, Any],
    branches: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the Postgres roles and databases on every branch of the project in scope.

    Roles are loaded before databases so the OWNS edge from the owner role
    resolves. Both cleanups are project-scoped and run once every branch has been
    read, so a database dropped from one branch is removed while the same-named
    database on its siblings is kept.
    """
    base_url = common_job_parameters["BASE_URL"]
    project_id = common_job_parameters["PROJECT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    host_by_branch = {
        e["branch_id"]: e["host"] for e in endpoints if e.get("type") == "read_write"
    }

    roles: list[dict[str, Any]] = []
    databases: list[dict[str, Any]] = []
    for branch in branches:
        roles.extend(
            transform_roles(get_roles(api_session, base_url, project_id, branch["id"]))
        )
        databases.extend(
            transform_databases(
                get_databases(api_session, base_url, project_id, branch["id"]),
                project,
                host_by_branch.get(branch["id"]),
            ),
        )

    load(
        neo4j_session,
        NeonRoleSchema(),
        roles,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    load(
        neo4j_session,
        NeonDatabaseSchema(),
        databases,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    GraphJob.from_node_schema(NeonDatabaseSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(NeonRoleSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def get_roles(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    branch_id: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/projects/{project_id}/branches/{branch_id}/roles",
    )["roles"]


@timeit
def get_databases(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    branch_id: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/projects/{project_id}/branches/{branch_id}/databases",
    )["databases"]


def transform_roles(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Build each record from an explicit field list: the listing can include the
    # role's `password`, which must never reach the graph.
    return [
        {
            "id": f"{role['branch_id']}/{role['name']}",
            "name": role["name"],
            "branch_id": role["branch_id"],
            "protected": role.get("protected"),
            "authentication_method": role.get("authentication_method"),
            "created_at": iso_to_datetime(role.get("created_at")),
            "updated_at": iso_to_datetime(role.get("updated_at")),
        }
        for role in roles
    ]


def transform_databases(
    databases: list[dict[str, Any]],
    project: dict[str, Any],
    host: str | None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{database['branch_id']}/{database['name']}",
            "database_id": database.get("id"),
            "name": database["name"],
            "owner_name": database.get("owner_name"),
            "owner_role_id": (
                f"{database['branch_id']}/{database['owner_name']}"
                if database.get("owner_name")
                else None
            ),
            "branch_id": database["branch_id"],
            "host": host,
            "pg_version": project.get("pg_version"),
            "region_id": project.get("region_id"),
            "created_at": iso_to_datetime(database.get("created_at")),
            "updated_at": iso_to_datetime(database.get("updated_at")),
        }
        for database in databases
    ]
