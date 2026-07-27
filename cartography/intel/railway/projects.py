import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.queries import PROJECT_BUNDLE_QUERY
from cartography.intel.railway.queries import PROJECTS_QUERY
from cartography.intel.railway.queries import WORKSPACE_QUERY
from cartography.intel.railway.utils import call_railway_api
from cartography.intel.railway.utils import paginated_query
from cartography.models.railway.project import RailwayProjectSchema
from cartography.models.railway.workspace import RailwayWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# One request pulls a whole project's environments, service instances, domains, deployments,
# volume instances, variables and deployment triggers. Railway's rate limit is hourly, so
# fewer, deeper documents matter more here than they do for a per-minute limit.
_BUNDLE_PAGE_SIZE = 100


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    update_tag: int,
) -> list[dict[str, Any]]:
    """
    Sync the workspace tenant and its projects.

    :return: The list of projects, for the per-project fan-out the caller drives next.
    """
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    base_url = common_job_parameters["BASE_URL"]

    workspace = get_workspace(api_session, base_url, workspace_id)
    projects = get_projects(api_session, base_url, workspace_id)

    load_workspace(neo4j_session, workspace, update_tag)
    load_projects(neo4j_session, projects, workspace_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return projects


@timeit
def get_workspace(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> dict[str, Any]:
    data = call_railway_api(
        api_session,
        base_url,
        WORKSPACE_QUERY,
        {"workspaceId": workspace_id},
    )
    return data["workspace"]


@timeit
def get_projects(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    # Railway rejects `projects` queries that omit workspaceId, so this is always scoped.
    return paginated_query(
        api_session,
        base_url,
        PROJECTS_QUERY,
        {"workspaceId": workspace_id},
        ("projects",),
    )


@timeit
def get_project_bundle(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> dict[str, Any]:
    """
    Fetch every child resource of a single project in one request.
    """
    data = call_railway_api(
        api_session,
        base_url,
        PROJECT_BUNDLE_QUERY,
        {"projectId": project_id, "first": _BUNDLE_PAGE_SIZE},
    )
    return data["project"]


@timeit
def load_workspace(
    neo4j_session: neo4j.Session,
    workspace: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayWorkspaceSchema(),
        [workspace],
        lastupdated=update_tag,
    )


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    projects: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayProjectSchema(),
        projects,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Projects are workspace-scoped, so a single job covers them. The workspace itself is a
    # tenant node and is never cleaned up.
    GraphJob.from_node_schema(RailwayProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )
