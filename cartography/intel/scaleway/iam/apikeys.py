import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import APIKey
from scaleway.iam.v1alpha1 import IamV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.apikey import ScalewayApiKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    update_tag: int,
) -> None:
    apikeys = get(client, org_id)
    formatted_apikeys = transform_apikeys(apikeys)
    load_apikeys(neo4j_session, formatted_apikeys, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[APIKey]:
    api = IamV1Alpha1API(client)
    return api.list_api_keys_all(organization_id=org_id)


def transform_apikeys(apikeys: list[APIKey]) -> list[dict[str, Any]]:
    formatted_apikeys = []
    for apikey in apikeys:
        formatted_apikeys.append(scaleway_obj_to_dict(apikey))
    return formatted_apikeys


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Scaleway ApiKeys into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayApiKeySchema(), common_job_parameters).run(
        neo4j_session
    )
