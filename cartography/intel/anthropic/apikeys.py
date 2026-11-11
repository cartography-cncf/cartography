import logging
from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import is_unavailable_to_organization
from cartography.intel.anthropic.util import paginated_get
from cartography.intel.anthropic.util import TIMEOUT
from cartography.models.anthropic.apikey import AnthropicApiKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        org_id, apikeys = get(
            api_session,
            common_job_parameters["BASE_URL"],
        )
    except requests.HTTPError as e:
        if not is_unavailable_to_organization(e):
            raise
        logger.info(
            "Anthropic apikeys are not available to this organization; skipping.",
        )
        return
    common_job_parameters["ORG_ID"] = org_id
    load_apikeys(
        neo4j_session,
        apikeys,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Tuple[str, list[dict[str, Any]]]:
    return paginated_get(
        api_session, f"{base_url}/organizations/api_keys", timeout=TIMEOUT
    )


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicApiKeySchema(), common_job_parameters).run(
        neo4j_session
    )
