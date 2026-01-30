import logging
from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get
from cartography.models.anthropic.organization import AnthropicOrganizationSchema
from cartography.models.anthropic.user import AnthropicUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> str:
    org_id, users = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    common_job_parameters["ORG_ID"] = org_id
    load_users(neo4j_session, users, org_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return org_id


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Tuple[str, list[dict[str, Any]]]:
    return paginated_get(
        api_session, f"{base_url}/organizations/users", timeout=_TIMEOUT
    )


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicOrganizationSchema(),
        [{"id": ORG_ID}],
        lastupdated=update_tag,
    )
    logger.info("Loading %d Anthropic User into Neo4j.", len(data))
    load(
        neo4j_session,
        AnthropicUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicUserSchema(), common_job_parameters).run(
        neo4j_session
    )
