import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal import apps
from cartography.intel.modal import dicts
from cartography.intel.modal import environment_roles
from cartography.intel.modal import functions
from cartography.intel.modal import images
from cartography.intel.modal import nfs
from cartography.intel.modal import proxies
from cartography.intel.modal import queues
from cartography.intel.modal import sandboxes
from cartography.intel.modal import secrets
from cartography.intel.modal import volumes
from cartography.intel.modal import workloads
from cartography.intel.modal.util import list_environments
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.environment import ModalEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Per-environment cleanups to run when an environment disappears from Modal.
#
# Environment-scoped resources are reached by their own cleanup *through* their
# ModalEnvironment node, and the entry point only fans out over environments that are still
# listed. So once an environment's node is deleted, its children become unreachable and
# survive as orphans. Every environment-scoped Modal resource must therefore expose
# `cleanup_for_environment(neo4j_session, workspace_id, environment_id, update_tag)` and be
# registered here.
# Ordered children-before-parents: functions and sandboxes reference apps, tasks reference
# clusters and apps, sandboxes reference images.
_ENVIRONMENT_SCOPED_CLEANUPS = (
    environment_roles.cleanup_for_environment,
    functions.cleanup_for_environment,
    sandboxes.cleanup_for_environment,
    workloads.cleanup_for_environment,
    images.cleanup_for_environment,
    apps.cleanup_for_environment,
    secrets.cleanup_for_environment,
    volumes.cleanup_for_environment,
    nfs.cleanup_for_environment,
    dicts.cleanup_for_environment,
    queues.cleanup_for_environment,
    proxies.cleanup_for_environment,
)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Ingest every environment in the workspace.

    All environments are always loaded, even when --modal-environments narrows which ones
    have their *contents* synced. `EnvironmentList` is a single cheap complete call, and
    loading only the allowlisted subset would make this workspace-scoped cleanup delete the
    other ModalEnvironment nodes while their environment-scoped children, whose cleanup
    never runs, survive as orphans.
    """
    raw = await list_environments(client)
    environments = transform(raw)
    load_environments(
        neo4j_session,
        environments,
        common_job_parameters["WORKSPACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    # Must run before the cleanup below deletes the disappeared environments' nodes.
    cleanup_removed_environments(
        neo4j_session,
        common_job_parameters["WORKSPACE_ID"],
        {environment["id"] for environment in environments},
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return environments


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(environment) for environment in raw]


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


def get_removed_environment_ids(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    live_environment_ids: set[str],
) -> list[str]:
    """Return ids of environments still in the graph but no longer present in Modal."""
    result = neo4j_session.run(
        """
        MATCH (:ModalWorkspace{id: $workspace_id})-[:RESOURCE]->(e:ModalEnvironment)
        WHERE NOT e.id IN $live_environment_ids
        RETURN e.id AS environment_id
        """,
        workspace_id=workspace_id,
        live_environment_ids=list(live_environment_ids),
    )
    return [record["environment_id"] for record in result]


@timeit
def cleanup_removed_environments(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    live_environment_ids: set[str],
    update_tag: int,
) -> None:
    """Run every environment-scoped cleanup for environments deleted in Modal.

    Must be called while those environments' nodes still exist, since the cleanups reach
    their targets through them.
    """
    for environment_id in get_removed_environment_ids(
        neo4j_session, workspace_id, live_environment_ids
    ):
        logger.info(
            "Modal environment %s no longer exists; removing its scoped resources.",
            environment_id,
        )
        for cleanup_fn in _ENVIRONMENT_SCOPED_CLEANUPS:
            cleanup_fn(neo4j_session, workspace_id, environment_id, update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalEnvironmentSchema(), common_job_parameters).run(
        neo4j_session
    )
