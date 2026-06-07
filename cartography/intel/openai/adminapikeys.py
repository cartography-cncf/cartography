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
    known_project_key_ids: set[str] | None = None,
) -> None:
    adminapikeys = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    transformed_adminapikeys = transform(adminapikeys, known_project_key_ids or set())
    load_adminapikeys(
        neo4j_session,
        transformed_adminapikeys,
        ORG_ID,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> List[Dict[str, Any]]:
    return list(
        paginated_get(
            api_session, f"{base_url}/organization/admin_api_keys", timeout=_TIMEOUT
        )
    )


def transform(
    adminapikeys: List[Dict[str, Any]],
    known_project_key_ids: set[str] | None = None,
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    skipped = 0
    for adminapikey in adminapikeys:
        # OpenAI admin_api_keys endpoint bug: it returns project-scoped keys
        # mislabeled as admin keys. Skip any key already synced as a project key.
        if known_project_key_ids and adminapikey["id"] in known_project_key_ids:
            skipped += 1
            continue
        if adminapikey["owner"]["type"] == "user":
            adminapikey["owner_user_id"] = adminapikey["owner"]["id"]
        else:
            adminapikey["owner_sa_id"] = adminapikey["owner"]["id"]
        result.append(adminapikey)
    if skipped:
        logger.debug(
            "Skipped %d keys from admin_api_keys endpoint that were already synced as project keys "
            "(OpenAI API bug workaround).",
            skipped,
        )
    return result


@timeit
def load_adminapikeys(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
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
