import logging
from typing import Any

import neo4j
import scaleway
from scaleway.lb.v1 import Backend
from scaleway.lb.v1 import Frontend
from scaleway.lb.v1 import Lb
from scaleway.lb.v1 import LbV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.loadbalancer.loadbalancer import (
    ScalewayLBBackendSchema,
)
from cartography.models.scaleway.loadbalancer.loadbalancer import (
    ScalewayLBFrontendSchema,
)
from cartography.models.scaleway.loadbalancer.loadbalancer import (
    ScalewayLoadBalancerSchema,
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
    lbs, frontends, backends = get(client, org_id)
    lbs_by_project, frontends_by_project, backends_by_project = transform_loadbalancers(
        lbs, frontends, backends
    )
    load_loadbalancers(
        neo4j_session,
        lbs_by_project,
        frontends_by_project,
        backends_by_project,
        update_tag,
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Lb], list[Frontend], list[Backend]]:
    api = LbV1API(client)
    lbs = list_all_regions(api.list_lbs_all, organization_id=org_id)
    frontends: list[Frontend] = []
    backends: list[Backend] = []
    for lb in lbs:
        frontends.extend(api.list_frontends_all(lb_id=lb.id, region=lb.region))
        backends.extend(api.list_backends_all(lb_id=lb.id, region=lb.region))
    return lbs, frontends, backends


def transform_loadbalancers(
    lbs: list[Lb],
    frontends: list[Frontend],
    backends: list[Backend],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    lbs_by_project: dict[str, list[dict[str, Any]]] = {}
    frontends_by_project: dict[str, list[dict[str, Any]]] = {}
    backends_by_project: dict[str, list[dict[str, Any]]] = {}

    # Frontends / backends inherit the project of their parent load balancer.
    # Resolve it from the parent LBs rather than the embedded child `lb`, so a
    # partial child payload can't strand children under PROJECT_ID=None.
    project_by_lb_id = {lb.id: lb.project_id for lb in lbs}

    for lb in lbs:
        formatted_lb = scaleway_obj_to_dict(lb)
        ip_addresses = [ip["ip_address"] for ip in (formatted_lb.get("ip") or [])]
        formatted_lb["ip_addresses"] = ip_addresses
        formatted_lb["ip_address"] = ip_addresses[0] if ip_addresses else None
        lbs_by_project.setdefault(lb.project_id, []).append(formatted_lb)

    for frontend in frontends:
        formatted_frontend = scaleway_obj_to_dict(frontend)
        lb_id = (formatted_frontend.get("lb") or {}).get("id")
        project_id = project_by_lb_id.get(lb_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway LB frontend %s: unknown parent LB %s.",
                formatted_frontend.get("id"),
                lb_id,
            )
            continue
        formatted_frontend["lb_id"] = lb_id
        formatted_frontend["backend_id"] = (
            formatted_frontend.get("backend") or {}
        ).get("id")
        frontends_by_project.setdefault(project_id, []).append(formatted_frontend)

    for backend in backends:
        formatted_backend = scaleway_obj_to_dict(backend)
        lb_id = (formatted_backend.get("lb") or {}).get("id")
        project_id = project_by_lb_id.get(lb_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway LB backend %s: unknown parent LB %s.",
                formatted_backend.get("id"),
                lb_id,
            )
            continue
        formatted_backend["lb_id"] = lb_id
        backends_by_project.setdefault(project_id, []).append(formatted_backend)

    return lbs_by_project, frontends_by_project, backends_by_project


@timeit
def load_loadbalancers(
    neo4j_session: neo4j.Session,
    lbs_by_project: dict[str, list[dict[str, Any]]],
    frontends_by_project: dict[str, list[dict[str, Any]]],
    backends_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, lbs in lbs_by_project.items():
        logger.info(
            "Loading %d Scaleway LoadBalancers in project '%s' into Neo4j.",
            len(lbs),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayLoadBalancerSchema(),
            lbs,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    # Backends before frontends: a frontend ROUTES_TO its backend.
    for project_id, backends in backends_by_project.items():
        load(
            neo4j_session,
            ScalewayLBBackendSchema(),
            backends,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, frontends in frontends_by_project.items():
        load(
            neo4j_session,
            ScalewayLBFrontendSchema(),
            frontends,
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
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        # Clean up children (frontends, backends) before the parent (LB).
        GraphJob.from_node_schema(
            ScalewayLBFrontendSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(ScalewayLBBackendSchema(), scoped_job_parameters).run(
            neo4j_session
        )
        GraphJob.from_node_schema(
            ScalewayLoadBalancerSchema(), scoped_job_parameters
        ).run(neo4j_session)
