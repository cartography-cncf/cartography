import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openai.util import paginated_get
from cartography.models.openai.assistant import OpenAIAssistantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    ORG_ID: str,
) -> None:
    assistants = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    load_assistants(neo4j_session, assistants, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    assistant_id: str,
) -> List[Dict[str, Any]]:
    return list(paginated_get(api_session, f"{base_url}/assistants", timeout=_TIMEOUT))


@timeit
def load_assistants(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d OpenAIAssistantSchema into Neo4j.", len(data))
    load(
        neo4j_session,
        OpenAIAssistantSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OpenAIAssistantSchema(), common_job_parameters).run(
        neo4j_session
    )
