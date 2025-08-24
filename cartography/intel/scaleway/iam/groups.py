import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import Group
from scaleway.iam.v1alpha1 import IamV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.group import ScalewayGroupSchema
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
    groups = get(client, org_id)
    formatted_groups = transform_groups(groups)
    load_groups(neo4j_session, formatted_groups, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Group]:
    api = IamV1Alpha1API(client)
    return api.list_groups_all(organization_id=org_id)


def transform_groups(groups: list[Group]) -> list[dict[str, Any]]:
    formatted_groups = []
    for group in groups:
        formatted_groups.append(scaleway_obj_to_dict(group))
    return formatted_groups


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Scaleway Groups into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayGroupSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
