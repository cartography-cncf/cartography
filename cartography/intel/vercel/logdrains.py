import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.logdrain import VercelLogDrainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    drains = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    load_log_drains(
        neo4j_session,
        drains,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    # Vercel's documented log-drains endpoint; returns a bare array.
    return paginated_get(
        api_session,
        f"{base_url}/v1/integrations/log-drains",
        "",
        team_id,
    )


@timeit
def load_log_drains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelLogDrainSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelLogDrainSchema(), common_job_parameters).run(
        neo4j_session,
    )
