from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get
from cartography.intel.anthropic.util import resolve_org_id
from cartography.models.anthropic.workspace import AnthropicWorkspaceSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    header_org_id, workspaces = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    org_id = resolve_org_id(common_job_parameters, header_org_id)
    common_job_parameters["ORG_ID"] = org_id
    for workspace in workspaces:
        transform_workspace(workspace)
        workspace["users"] = []
        workspace["admins"] = []
        for user in get_workspace_users(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace["id"],
        ):
            workspace["users"].append(user["user_id"])
            if user["workspace_role"] == "workspace_admin":
                workspace["admins"].append(user["user_id"])
    load_workspaces(
        neo4j_session, workspaces, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return workspaces


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Tuple[str, list[dict[str, Any]]]:
    return paginated_get(
        api_session, f"{base_url}/organizations/workspaces", timeout=_TIMEOUT
    )


@timeit
def get_workspace_users(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    _, result = paginated_get(
        api_session,
        f"{base_url}/organizations/workspaces/{workspace_id}/members",
        timeout=_TIMEOUT,
    )
    return result


def transform_workspace(workspace: dict[str, Any]) -> None:
    """Flatten the nested data_residency object into scalar properties.

    Neo4j node properties cannot hold maps. `tags` is dropped for the same reason:
    it is an arbitrary string map with no fixed keys to flatten onto.
    """
    data_residency = workspace.pop("data_residency", None) or {}
    workspace["workspace_geo"] = data_residency.get("workspace_geo")
    workspace["default_inference_geo"] = data_residency.get("default_inference_geo")
    # Either a list of geo names or the literal string "unrestricted"; normalise both
    # to a list so the property has a single type in the graph.
    allowed = data_residency.get("allowed_inference_geos")
    if isinstance(allowed, str):
        allowed = [allowed]
    workspace["allowed_inference_geos"] = allowed
    workspace.pop("tags", None)


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
