import logging
from typing import Any

import neo4j
import scaleway
from scaleway.datawarehouse.v1beta1 import DatawarehouseV1Beta1API
from scaleway.datawarehouse.v1beta1 import Deployment

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.database.datawarehouse import (
    ScalewayDataWarehouseDeploymentSchema,
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
    deployments = get(client, org_id)
    deployments_by_project = transform_deployments(deployments)
    load_deployments(neo4j_session, deployments_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Deployment]:
    api = DatawarehouseV1Beta1API(client)
    return list_all_regions(api.list_deployments_all, organization_id=org_id)


def transform_deployments(
    deployments: list[Deployment],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for deployment in deployments:
        formatted = scaleway_obj_to_dict(deployment)
        # Flatten the endpoints list to a single exposure flag; deeper endpoint
        # modeling can come later if per-endpoint detail is ever needed.
        formatted["is_public"] = any(
            bool(getattr(e, "public", None)) for e in (deployment.endpoints or [])
        )
        result.setdefault(deployment.project_id, []).append(formatted)
    return result


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, deployments in data.items():
        load(
            neo4j_session,
            ScalewayDataWarehouseDeploymentSchema(),
            deployments,
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
            ScalewayDataWarehouseDeploymentSchema(), scopped_job_parameters
        ).run(neo4j_session)
