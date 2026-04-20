import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.authtoken import VercelAuthTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Vercel only exposes tokens for the authenticated caller (no team-tokens
    # endpoint). We fetch the caller identity first so we can anchor tokens to
    # the owning VercelUser, and we keep only tokens whose scopes include the
    # current team.
    caller_id = get_caller_id(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    tokens = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    tokens = transform_tokens(
        tokens,
        caller_id,
        common_job_parameters["TEAM_ID"],
    )
    load_auth_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_caller_id(api_session: requests.Session, base_url: str) -> str:
    # /v2/user keys the caller's identifier as `id`, while the team-members
    # endpoint keys the same identifier as `uid`. Accept either so the value
    # still matches the VercelUser node id.
    resp = api_session.get(f"{base_url}/v2/user", timeout=_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    user = body.get("user", body)
    return user.get("id") or user["uid"]


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    # /v6/user/tokens is user-scoped and rejects `teamId` with 400; team scope
    # is represented inside each token's `scopes` array and applied during
    # transform.
    return paginated_get(
        api_session,
        f"{base_url}/v6/user/tokens",
        "tokens",
        None,
    )


def transform_tokens(
    tokens: list[dict[str, Any]],
    caller_id: str,
    team_id: str,
) -> list[dict[str, Any]]:
    # Keep only tokens whose scopes include the current team (covers both
    # team-only and user+team mixed scopes). Purely user-scoped tokens leak
    # no team context and are dropped.
    filtered: list[dict[str, Any]] = []
    for token in tokens:
        scopes = token.get("scopes") or []
        if any(s.get("type") == "team" and s.get("teamId") == team_id for s in scopes):
            token["owner_id"] = caller_id
            filtered.append(token)
    return filtered


@timeit
def load_auth_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelAuthTokenSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelAuthTokenSchema(), common_job_parameters).run(
        neo4j_session,
    )
