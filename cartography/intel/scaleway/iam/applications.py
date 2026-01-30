import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import Application
from scaleway.iam.v1alpha1 import IamV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.application import ScalewayApplicationSchema
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
    applications = get(client, org_id)
    formatted_applications = transform_applications(applications)
    load_applications(neo4j_session, formatted_applications, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Application]:
    api = IamV1Alpha1API(client)
    return api.list_applications_all(organization_id=org_id)


def transform_applications(applications: list[Application]) -> list[dict[str, Any]]:
    formatted_applications = []
    for application in applications:
        formatted_applications.append(scaleway_obj_to_dict(application))
    return formatted_applications


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Scaleway Applications into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayApplicationSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayApplicationSchema(), common_job_parameters).run(
        neo4j_session
    )
