import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.models.circleci.user import CircleCIUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> None:
    user = get(api_session, common_job_parameters["BASE_URL"])
    load_users(
        neo4j_session,
        [user],
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> dict[str, Any]:
    # /me returns the token owner only (a single object).
    req = api_session.get(f"{base_url}/me", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
