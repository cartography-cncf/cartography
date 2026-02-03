import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import IamV1Alpha1API
from scaleway.iam.v1alpha1 import PermissionSet

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.permissionset import ScalewayPermissionSetSchema
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
    permission_sets = get(client, org_id)
    formatted_permission_sets = transform_permission_sets(permission_sets)
    load_permission_sets(neo4j_session, formatted_permission_sets, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[PermissionSet]:
    api = IamV1Alpha1API(client)
    return api.list_permission_sets_all(organization_id=org_id)


def transform_permission_sets(
    permission_sets: list[PermissionSet],
) -> list[dict[str, Any]]:
    formatted_permission_sets = []
    for permission_set in permission_sets:
        formatted_permission_set = scaleway_obj_to_dict(permission_set)
        formatted_permission_sets.append(formatted_permission_set)
    return formatted_permission_sets


@timeit
def load_permission_sets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Scaleway PermissionSets into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayPermissionSetSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayPermissionSetSchema(), common_job_parameters).run(
        neo4j_session
    )
