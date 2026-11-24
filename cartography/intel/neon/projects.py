import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_json
from cartography.intel.neon.util import iso_to_datetime
from cartography.models.neon.project import NeonProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_PROJECTS_PAGE_SIZE = 400


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> tuple[list[dict[str, Any]], bool]:
    """
    List every project in the organization.

    Returns the projects and whether the listing is complete. The API answers with
    an ``unavailable_project_ids`` list when some projects could not be read in
    time. A project missing for that reason is not deleted, so a partial listing
    must not drive the cascading project cleanup.
    """
    projects: list[dict[str, Any]] = []
    complete = True
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"org_id": org_id, "limit": _PROJECTS_PAGE_SIZE}
        if cursor:
            params["cursor"] = cursor
        page = get_json(api_session, f"{base_url}/projects", params=params)
        batch = page["projects"]
        projects.extend(batch)
        if page.get("unavailable_project_ids"):
            logger.warning(
                "Neon could not return %d project(s) in organization %s: %s",
                len(page["unavailable_project_ids"]),
                org_id,
                page["unavailable_project_ids"],
            )
            complete = False
        next_cursor = (page.get("pagination") or {}).get("cursor")
        if not batch or not next_cursor or next_cursor == cursor:
            return projects, complete
        cursor = next_cursor


def transform_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for project in projects:
        settings = project.get("settings") or {}
        allowed_ips = settings.get("allowed_ips") or {}
        result.append(
            {
                "id": project["id"],
                "name": project["name"],
                "region_id": project["region_id"],
                "platform_id": project.get("platform_id"),
                "pg_version": project.get("pg_version"),
                "proxy_host": project.get("proxy_host"),
                "org_id": project.get("org_id"),
                "owner_id": project.get("owner_id"),
                "creation_source": project.get("creation_source"),
                "created_at": iso_to_datetime(project.get("created_at")),
                "updated_at": iso_to_datetime(project.get("updated_at")),
                "compute_last_active_at": iso_to_datetime(
                    project.get("compute_last_active_at"),
                ),
                "history_retention_seconds": project.get("history_retention_seconds"),
                "store_passwords": project.get("store_passwords"),
                "allowed_ips": allowed_ips.get("ips") or None,
                "allowed_ips_protected_branches_only": allowed_ips.get(
                    "protected_branches_only",
                ),
                "block_public_connections": settings.get("block_public_connections"),
                "block_vpc_connections": settings.get("block_vpc_connections"),
                "enable_logical_replication": settings.get(
                    "enable_logical_replication",
                ),
                "hipaa": settings.get("hipaa"),
                "audit_log_level": settings.get("audit_log_level"),
            },
        )
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    projects: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load the organization's projects.

    Cleanup is deliberately not run here. Stale projects must be removed only
    after their children have been synced, and with a cascade, so a project
    deleted upstream does not leave orphaned children behind. See cleanup().
    """
    load_projects(
        neo4j_session,
        transform_projects(projects),
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove projects that no longer exist in the organization, and their children.

    ``cascade_delete`` is required: child cleanups are scoped to ``PROJECT_ID``
    and only run for projects that still exist, so without the cascade a project
    deleted upstream would leave its branches, endpoints, databases and buckets
    behind as unreachable orphans.
    """
    GraphJob.from_node_schema(
        NeonProjectSchema(),
        common_job_parameters,
        cascade_delete=True,
    ).run(neo4j_session)
