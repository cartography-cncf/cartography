import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openai.util import paginated_get
from cartography.models.openai.serviceaccount import OpenAIServiceAccountSchema
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
    serviceaccountss = get(
        api_session,
        common_job_parameters["BASE_URL"],
        project_id,
    )
    load_serviceaccounts(
        neo4j_session,
        serviceaccountss,
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
            "{base_url}/organization/projects/{project_id}/service_accounts".format(
                base_url=base_url,
                project_id=project_id,
            ),
            timeout=_TIMEOUT,
        )
    )


@timeit
def load_serviceaccounts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d OpenAI ServiceAccount into Neo4j.", len(data))
    load(
        neo4j_session,
        OpenAIServiceAccountSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OpenAIServiceAccountSchema(), common_job_parameters).run(
        neo4j_session
    )
