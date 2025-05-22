import logging
from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get
from cartography.models.anthropic.workspace import AnthropicWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    org_id, workspaces = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    common_job_parameters["ORG_ID"] = org_id
    for workspace in workspaces:
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


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Anthropic workspaces into Neo4j.", len(data))
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
