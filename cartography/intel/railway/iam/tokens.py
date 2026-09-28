import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.queries import API_TOKENS_QUERY
from cartography.intel.railway.queries import PROJECT_TOKENS_QUERY
from cartography.intel.railway.utils import paginated_query
from cartography.intel.railway.utils import RailwayGraphQLError
from cartography.models.railway.iam.apitoken import RailwayApiTokenSchema
from cartography.models.railway.iam.projecttoken import RailwayProjectTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    account_user_id: str | None,
    update_tag: int,
) -> None:
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    base_url = common_job_parameters["BASE_URL"]

    api_tokens, api_tokens_readable = get_api_tokens(
        api_session,
        base_url,
        workspace_id,
    )
    if api_tokens_readable:
        load_api_tokens(
            neo4j_session,
            transform_api_tokens(api_tokens, account_user_id),
            workspace_id,
            update_tag,
        )
    else:
        # An unreadable inventory is not an empty one. Loading nothing and then running
        # cleanup would mark every previously ingested API token stale and delete it, so
        # switching from an account token to a workspace token would silently wipe them.
        logger.warning(
            "Skipping RailwayApiToken load and cleanup for workspace %s: the token cannot "
            "read the API token inventory, so previously ingested tokens are left in place.",
            workspace_id,
        )

    for project in projects:
        project_tokens = get_project_tokens(api_session, base_url, project["id"])
        load_project_tokens(
            neo4j_session,
            project_tokens,
            workspace_id,
            project["id"],
            update_tag,
        )

    cleanup(
        neo4j_session,
        common_job_parameters,
        projects,
        cleanup_api_tokens=api_tokens_readable,
    )


@timeit
def get_api_tokens(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> tuple[list[dict[str, Any]], bool]:
    """
    List the account's API tokens.

    `apiTokens` is not readable by every token type: a workspace-scoped token gets
    `Not Authorized` back rather than an empty list. Missing token inventory should not
    abort the rest of the workspace sync, so that case degrades to a warning.

    :return: (tokens, readable). `readable` is False when the token could not read the
        inventory at all. Callers must not load or clean up API tokens in that case: an
        empty list would otherwise be indistinguishable from "this workspace has no tokens"
        and cleanup would delete the ones a previous sync ingested.
    """
    try:
        tokens = paginated_query(
            api_session,
            base_url,
            API_TOKENS_QUERY,
            {},
            ("apiTokens",),
        )
    except RailwayGraphQLError as err:
        if not err.is_not_authorized:
            raise
        logger.warning(
            "Railway token is not authorized to read apiTokens - skipping API token "
            "inventory. Use an account-scoped token to ingest them.",
        )
        return [], False
    # apiTokens is account-scoped, so filter down to the workspace being synced. Tokens with
    # no workspaceId are personal-scope tokens, which reach every workspace.
    return [
        token for token in tokens if token.get("workspaceId") in (None, workspace_id)
    ], True


def transform_api_tokens(
    tokens: list[dict[str, Any]],
    account_user_id: str | None,
) -> list[dict[str, Any]]:
    """
    Attach the owning principal to each API token.

    Railway's ApiToken type has no owner field. `apiTokens` is account-scoped, so every
    token it returns belongs to the token holder identified by `me`. When `me` was not
    readable the owner stays unset and no OWNED_BY edge is created.
    """
    return [{**token, "user_id": account_user_id} for token in tokens]


@timeit
def get_project_tokens(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> list[dict[str, Any]]:
    return paginated_query(
        api_session,
        base_url,
        PROJECT_TOKENS_QUERY,
        {"projectId": project_id},
        ("projectTokens",),
    )


@timeit
def load_api_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayApiTokenSchema(),
        tokens,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_project_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    workspace_id: str,
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayProjectTokenSchema(),
        tokens,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    cleanup_api_tokens: bool = True,
) -> None:
    if cleanup_api_tokens:
        GraphJob.from_node_schema(RailwayApiTokenSchema(), common_job_parameters).run(
            neo4j_session,
        )
    for project in projects:
        # .copy() matters: mutating the shared dict would leak this project's scope into
        # every later cleanup job.
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project["id"]
        GraphJob.from_node_schema(
            RailwayProjectTokenSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
