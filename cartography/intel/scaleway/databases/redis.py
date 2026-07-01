import logging
from typing import Any

import neo4j
import scaleway
from scaleway.redis.v1 import Cluster
from scaleway.redis.v1 import RedisV1API
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_REGIONS
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.database.redis_cluster import (
    ScalewayRedisClusterSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Redis is zone-scoped, not region-scoped. Scaleway currently exposes two AZs
# per region (e.g. fr-par-1, fr-par-2). We fan out across both for every known
# region; zones where Redis is not deployed answer "unknown service" and are
# skipped, so unsupported permutations are harmless.
_REDIS_ZONES = tuple(f"{region}-{az}" for region in DEFAULT_REGIONS for az in (1, 2))


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    clusters = get(client, org_id)
    clusters_by_project = transform_clusters(clusters)
    load_clusters(neo4j_session, clusters_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(client: scaleway.Client, org_id: str) -> list[Cluster]:
    api = RedisV1API(client)
    clusters: list[Cluster] = []
    for zone in _REDIS_ZONES:
        try:
            clusters.extend(api.list_clusters_all(zone=zone, organization_id=org_id))
        except ScalewayException as exc:
            if "unknown service" in str(exc).lower():
                logger.info("Scaleway Redis not available in zone %s, skipping.", zone)
                continue
            raise
    return clusters


def transform_clusters(
    clusters: list[Cluster],
) -> dict[str, list[dict[str, Any]]]:
    clusters_by_project: dict[str, list[dict[str, Any]]] = {}
    for cluster in clusters:
        formatted = scaleway_obj_to_dict(cluster)
        _flatten_redis_endpoints(formatted)
        clusters_by_project.setdefault(cluster.project_id, []).append(formatted)
    return clusters_by_project


def _flatten_redis_endpoints(formatted: dict[str, Any]) -> None:
    """Flatten the Redis endpoints list into scalar public/private fields.

    A Redis endpoint is either ``public_network`` (publicly reachable) or
    ``private_network`` (attached to a VPC private network).
    """
    endpoints = formatted.get("endpoints") or []
    is_public = False
    public_ip: str | None = None
    public_port: int | None = None
    private_ip: str | None = None
    private_port: int | None = None
    private_network_ids: list[str] = []

    for endpoint in endpoints:
        ips = endpoint.get("ips") or []
        first_ip = ips[0] if ips else None
        if endpoint.get("public_network") is not None:
            is_public = True
            if public_ip is None:
                public_ip = first_ip
                public_port = endpoint.get("port")
        elif endpoint.get("private_network") is not None:
            pn = endpoint["private_network"]
            pn_id = pn.get("id")
            if pn_id:
                private_network_ids.append(pn_id)
            if private_ip is None:
                private_ip = first_ip
                private_port = endpoint.get("port")

    formatted["is_public"] = is_public
    formatted["public_endpoint_ip"] = public_ip
    formatted["public_endpoint_port"] = public_port
    formatted["private_endpoint_ip"] = private_ip
    formatted["private_endpoint_port"] = private_port
    formatted["private_network_ids"] = private_network_ids or None


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    clusters_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, clusters in clusters_by_project.items():
        logger.info(
            "Loading %d Scaleway Redis clusters in project '%s' into Neo4j.",
            len(clusters),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayRedisClusterSchema(),
            clusters,
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
        GraphJob.from_node_schema(
            ScalewayRedisClusterSchema(), scoped_job_parameters
        ).run(neo4j_session)
