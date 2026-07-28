import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.queries import DEPLOYMENT_PAGE_SIZE
from cartography.intel.railway.queries import ENVIRONMENT_CHILD_QUERIES
from cartography.intel.railway.queries import PROJECT_BUNDLE_QUERY
from cartography.intel.railway.queries import PROJECT_CHILD_QUERIES
from cartography.intel.railway.queries import PROJECT_ENVIRONMENTS_QUERY
from cartography.intel.railway.queries import PROJECTS_QUERY
from cartography.intel.railway.queries import WORKSPACE_QUERY
from cartography.intel.railway.utils import call_railway_api
from cartography.intel.railway.utils import paginated_query
from cartography.intel.railway.utils import unwrap_edges
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
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Sync the workspace tenant and its projects.

    :return: The workspace and its projects, for the fan-out the caller drives next.
    """
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    base_url = common_job_parameters["BASE_URL"]

    workspace = get_workspace(api_session, base_url, workspace_id)
    projects = get_projects(api_session, base_url, workspace_id)

    load_workspace(neo4j_session, workspace, update_tag)
    load_projects(neo4j_session, projects, workspace_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return workspace, projects


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
    Fetch every child resource of a single project.

    The happy path is a single request. Any connection that came back truncated is then
    drained with a targeted follow-up query, so callers always receive a complete bundle.
    Returning a truncated one would be worse than failing: the cleanup jobs treat whatever
    they are given as exhaustive and would delete every resource past the first page.
    """
    data = call_railway_api(
        api_session,
        base_url,
        PROJECT_BUNDLE_QUERY,
        {
            "projectId": project_id,
            "first": _BUNDLE_PAGE_SIZE,
            "deploymentFirst": DEPLOYMENT_PAGE_SIZE,
        },
    )
    bundle = data["project"]
    drain_project_bundle(api_session, base_url, bundle)
    return bundle


def _drain_connection(
    api_session: requests.Session,
    base_url: str,
    connection: dict[str, Any],
    query: str,
    variables: dict[str, Any],
    connection_path: tuple[str, ...],
) -> list[dict[str, Any]]:
    """
    Append the remaining pages of an already-started connection, in place.

    :return: The nodes that were appended, so the caller can recurse into them.
    """
    page_info = connection["pageInfo"]
    if not page_info["hasNextPage"]:
        return []

    logger.debug(
        "Railway connection %s was truncated at %d items; fetching the remainder.",
        ".".join(connection_path),
        len(connection["edges"]),
    )
    remainder = paginated_query(
        api_session,
        base_url,
        query,
        variables,
        connection_path,
        page_size=_BUNDLE_PAGE_SIZE,
        after=page_info["endCursor"],
    )
    connection["edges"].extend({"node": node} for node in remainder)
    # The connection is now complete, so a transform reading pageInfo sees the truth.
    connection["pageInfo"] = {"hasNextPage": False, "endCursor": None}
    return remainder


@timeit
def drain_project_bundle(
    api_session: requests.Session,
    base_url: str,
    bundle: dict[str, Any],
) -> None:
    """
    Fetch every page of every connection in a project bundle, mutating it in place.

    Costs no extra requests for projects that fit inside one page, which is the common case.
    """
    project_id = bundle["id"]

    for key, query in PROJECT_CHILD_QUERIES.items():
        _drain_connection(
            api_session,
            base_url,
            bundle[key],
            query,
            {"projectId": project_id},
            ("project", key),
        )

    # Environments arrive with their own children already populated, and the follow-up query
    # requests the same selection, so the child-draining loop below covers both the
    # first-page environments and any fetched here.
    _drain_connection(
        api_session,
        base_url,
        bundle["environments"],
        PROJECT_ENVIRONMENTS_QUERY,
        {"projectId": project_id, "deploymentFirst": DEPLOYMENT_PAGE_SIZE},
        ("project", "environments"),
    )

    for environment in unwrap_edges(bundle["environments"]):
        for key, query in ENVIRONMENT_CHILD_QUERIES.items():
            _drain_connection(
                api_session,
                base_url,
                environment[key],
                query,
                {"environmentId": environment["id"]},
                ("environment", key),
            )


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
    #
    # cascade_delete is required, not an optimisation. Every other domain's cleanup iterates
    # the projects the API just returned, so a project that has been deleted upstream is not
    # in that list and its environments, services, instances, deployments, domains, proxies,
    # volumes and variables would never be visited. Deleting the project node alone would
    # strip their RESOURCE edges and leave them as unreachable orphans that no later sync can
    # collect. Cascading from the stale project takes its stale children with it.
    GraphJob.from_node_schema(
        RailwayProjectSchema(),
        common_job_parameters,
        cascade_delete=True,
    ).run(neo4j_session)
