import logging
from typing import Any

import neo4j
import scaleway
from scaleway.flexibleip.v1alpha1 import FlexibleIP
from scaleway.flexibleip.v1alpha1 import FlexibleipV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_zones
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.baremetal.flexible_ip import (
    ScalewayElasticMetalFlexibleIpSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    flexibleips = get(client, org_id)
    flexibleips_by_project = transform_flexibleips(flexibleips)
    load_flexibleips(neo4j_session, flexibleips_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[FlexibleIP]:
    api = FlexibleipV1Alpha1API(client)
    return list_all_zones(api.list_flexible_i_ps_all, organization_id=org_id)


def transform_flexibleips(
    flexibleips: list[FlexibleIP],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for flexibleip in flexibleips:
        formatted = scaleway_obj_to_dict(flexibleip)
        result.setdefault(flexibleip.project_id, []).append(formatted)
    return result


@timeit
def load_flexibleips(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, flexibleips in data.items():
        load(
            neo4j_session,
            ScalewayElasticMetalFlexibleIpSchema(),
            flexibleips,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scopped_job_parameters = common_job_parameters.copy()
        scopped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayElasticMetalFlexibleIpSchema(), scopped_job_parameters
        ).run(neo4j_session)
