"""Running tasks and multi-node clusters.

These two live together because their edges are interlocked: a task's MEMBER_OF edge needs
its cluster to exist, and both hang off the same apps. Clusters are loaded first for that
reason.

Note the asymmetry in the API: `TaskList` is per-app, while `ClusterList` is per-environment
(its request message has no app_id field), so tasks fan out over apps and clusters do not.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_clusters
from cartography.intel.modal.util import list_tasks
from cartography.intel.modal.util import MODAL_API_ERRORS
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.cluster import ModalClusterSchema
from cartography.models.modal.task import ModalTaskSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    apps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw_clusters = await list_clusters(client, environment_name)
    clusters = transform_clusters(raw_clusters, environment_name)
    load_clusters(neo4j_session, clusters, environment_id, update_tag)

    raw_tasks: list[dict[str, Any]] = []
    complete = True
    for app in apps:
        try:
            raw_tasks.extend(await list_tasks(client, environment_name, app["id"]))
        except MODAL_API_ERRORS as exc:
            # Only expected API failures degrade to "partial enumeration, skip cleanup".
            # A programming or protocol error must propagate rather than be laundered into a
            # partial success that silently preserves stale data.
            logger.warning("Could not list tasks of Modal app %s: %s", app["id"], exc)
            complete = False

    tasks = transform_tasks(raw_tasks, raw_clusters, environment_name)
    load_tasks(neo4j_session, tasks, environment_id, update_tag)

    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Modal task cleanup for environment %s: at least one app could not be "
            "listed this run, so stale nodes are preserved rather than risk deleting live "
            "tasks.",
            environment_name,
        )
    return tasks


def transform_clusters(
    raw: list[dict[str, Any]], environment_name: str
) -> list[dict[str, Any]]:
    return [{**cluster, "environment_name": environment_name} for cluster in raw]


def transform_tasks(
    raw: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    environment_name: str,
) -> list[dict[str, Any]]:
    """Attach each task's cluster id.

    Modal reports membership on the cluster (`task_ids`), not on the task, so it is inverted
    here: materialising the edge from the task side means a task leaving a cluster is cleaned
    up with the task, without needing the cluster to be re-synced.
    """
    cluster_id_by_task: dict[str, str] = {}
    for cluster in clusters:
        for task_id in cluster.get("task_ids") or []:
            cluster_id_by_task[task_id] = cluster["id"]
    return [
        {
            **task,
            "cluster_id": cluster_id_by_task.get(task["id"]),
            "environment_name": environment_name,
        }
        for task in raw
    ]


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalClusterSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_tasks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalTaskSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalTaskSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalClusterSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
