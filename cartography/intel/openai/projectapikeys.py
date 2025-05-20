import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openai.util import paginated_get
from cartography.models.openai.projectapikey import OpenAIProjectApiKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    project_id: str,
) -> None:
    projectapikeys = get(
        api_session,
        common_job_parameters["BASE_URL"],
        project_id,
    )
    # CHANGEME: You can configure here a transform operation
    # formated_projectapikeys = transform(projectapikeys)
    load_projectapikeys(
        neo4j_session,
        projectapikeys,  # CHANGEME: replace with `formated_projectapikeys` if your added a transform step
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> List[Dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            "{base_url}/projects/{project_id}/api-keys".format(
                base_url=base_url,
                project_id=project_id,
            ),
            timeout=_TIMEOUT,
        )
    )


@timeit
def load_projectapikeys(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d OpenAI ProjectApiKey into Neo4j.", len(data))
    load(
        neo4j_session,
        OpenAIProjectApiKeySchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OpenAIProjectApiKeySchema(), common_job_parameters).run(
        neo4j_session
    )
