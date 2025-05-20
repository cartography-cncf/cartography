import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openai.util import paginated_get
from cartography.models.openai.adminapikey import OpenAIAdminApiKeySchema
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
) -> List[Dict]:
    adminapikeys = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    # CHANGEME: You can configure here a transform operation
    # formated_adminapikeys = transform(adminapikeys)
    load_adminapikeys(
        neo4j_session,
        adminapikeys,  # CHANGEME: replace with `formated_adminapikeys` if your added a transform step
        ORG_ID,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return adminapikeys


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> List[Dict[str, Any]]:
    return list(
        paginated_get(api_session, f"{base_url}/admin_api_keys", timeout=_TIMEOUT)
    )


@timeit
def load_adminapikeys(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d OpenAI AdminApiKey into Neo4j.", len(data))
    load(
        neo4j_session,
        OpenAIAdminApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OpenAIAdminApiKeySchema(), common_job_parameters).run(
        neo4j_session
    )
