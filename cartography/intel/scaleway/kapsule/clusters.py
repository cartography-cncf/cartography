import logging
from typing import Any

import neo4j
import scaleway
from scaleway.k8s.v1 import Cluster
from scaleway.k8s.v1 import K8SV1API
from scaleway.k8s.v1 import Node
from scaleway.k8s.v1 import Pool

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.kapsule.cluster import ScalewayKapsuleClusterSchema
from cartography.models.scaleway.kapsule.node import ScalewayKapsuleNodeSchema
from cartography.models.scaleway.kapsule.pool import ScalewayKapsulePoolSchema
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
    clusters, pools, nodes = get(client, org_id)
    clusters_by_project, pools_by_project, nodes_by_project = transform_clusters(
        clusters, pools, nodes
    )
    load_clusters(
        neo4j_session,
        clusters_by_project,
        pools_by_project,
        nodes_by_project,
        update_tag,
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Cluster], list[Pool], list[Node]]:
    api = K8SV1API(client)
    clusters = list_all_regions(api.list_clusters_all, organization_id=org_id)
    pools: list[Pool] = []
    nodes: list[Node] = []
    for cluster in clusters:
        pools.extend(api.list_pools_all(cluster_id=cluster.id, region=cluster.region))
        nodes.extend(api.list_nodes_all(cluster_id=cluster.id, region=cluster.region))
    return clusters, pools, nodes


def transform_clusters(
    clusters: list[Cluster],
    pools: list[Pool],
    nodes: list[Node],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    clusters_by_project: dict[str, list[dict[str, Any]]] = {}
    pools_by_project: dict[str, list[dict[str, Any]]] = {}
    nodes_by_project: dict[str, list[dict[str, Any]]] = {}

    # Pools and nodes inherit the project of their parent cluster: the API
    # does not return project_id on them.
    project_by_cluster_id = {cluster.id: cluster.project_id for cluster in clusters}

    for cluster in clusters:
        clusters_by_project.setdefault(cluster.project_id, []).append(
            scaleway_obj_to_dict(cluster)
        )

    for pool in pools:
        project_id = project_by_cluster_id.get(pool.cluster_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway Kapsule pool %s: unknown parent cluster %s.",
                pool.id,
                pool.cluster_id,
            )
            continue
        pools_by_project.setdefault(project_id, []).append(scaleway_obj_to_dict(pool))

    for node in nodes:
        project_id = project_by_cluster_id.get(node.cluster_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway Kapsule node %s: unknown parent cluster %s.",
                node.id,
                node.cluster_id,
            )
            continue
        nodes_by_project.setdefault(project_id, []).append(scaleway_obj_to_dict(node))

    return clusters_by_project, pools_by_project, nodes_by_project


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    clusters_by_project: dict[str, list[dict[str, Any]]],
    pools_by_project: dict[str, list[dict[str, Any]]],
    nodes_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, clusters in clusters_by_project.items():
        logger.info(
            "Loading %d Scaleway Kapsule Clusters in project '%s' into Neo4j.",
            len(clusters),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayKapsuleClusterSchema(),
            clusters,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, pools in pools_by_project.items():
        load(
            neo4j_session,
            ScalewayKapsulePoolSchema(),
            pools,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, nodes in nodes_by_project.items():
        load(
            neo4j_session,
            ScalewayKapsuleNodeSchema(),
            nodes,
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
        # Children before parents: Node -> Pool -> Cluster.
        GraphJob.from_node_schema(
            ScalewayKapsuleNodeSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayKapsulePoolSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayKapsuleClusterSchema(), scoped_job_parameters
        ).run(neo4j_session)
