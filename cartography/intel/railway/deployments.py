import logging
import re
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.deployment import RailwayDeploymentSchema
from cartography.models.railway.deploymenttrigger import RailwayDeploymentTriggerSchema
from cartography.models.railway.filesystem_snapshot import (
    RailwayFilesystemSnapshotSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
) -> None:
    deployments, snapshots, triggers = transform(bundles)
    load_deployments(neo4j_session, deployments, update_tag)
    load_filesystem_snapshots(neo4j_session, snapshots, update_tag)
    load_deployment_triggers(neo4j_session, triggers, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    deployments: dict[str, list[dict[str, Any]]] = {}
    snapshots: dict[str, list[dict[str, Any]]] = {}
    triggers: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        # The deployment each service instance is currently serving. Everything else in the
        # window is a superseded revision.
        current_instances: dict[str, dict[str, Any]] = {}
        for instance in iter_service_instances(bundle):
            latest_deployment = instance.get("latestDeployment") or {}
            if latest_deployment.get("id"):
                current_instances[latest_deployment["id"]] = instance
        current_ids = set(current_instances)

        project_deployments: list[dict[str, Any]] = []
        project_snapshots: list[dict[str, Any]] = []
        project_triggers: list[dict[str, Any]] = []
        for environment in unwrap_edges(bundle["environments"]):
            for deployment in unwrap_edges(environment["deployments"]):
                meta = deployment.get("meta")
                commit_hash = meta.get("commitHash") if isinstance(meta, dict) else None
                source_revision = (
                    commit_hash.lower()
                    if isinstance(commit_hash, str)
                    and re.fullmatch(r"[0-9a-fA-F]{40}", commit_hash)
                    else None
                )
                project_deployments.append(
                    {
                        **deployment,
                        "source_revision": source_revision,
                        "lifecycle": (
                            "current"
                            if deployment["id"] in current_ids
                            else "historical"
                        ),
                    },
                )
                current_instance = current_instances.get(deployment["id"])
                source = (current_instance or {}).get("source") or {}
                if source_revision and source.get("repo"):
                    project_snapshots.append(
                        {
                            "id": f"railway:filesystem-snapshot:{deployment['id']}",
                            "deployment_id": deployment["id"],
                            "kind": "source",
                            "source_revision": source_revision,
                            "source_repo": source["repo"],
                            "root_directory": (current_instance or {}).get(
                                "rootDirectory"
                            ),
                        },
                    )
            project_triggers.extend(unwrap_edges(environment["deploymentTriggers"]))
        deployments[project_id] = project_deployments
        snapshots[project_id] = project_snapshots
        triggers[project_id] = project_triggers

    return deployments, snapshots, triggers


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, deployments in by_project.items():
        load(
            neo4j_session,
            RailwayDeploymentSchema(),
            deployments,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_filesystem_snapshots(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, snapshots in by_project.items():
        load(
            neo4j_session,
            RailwayFilesystemSnapshotSchema(),
            snapshots,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_deployment_triggers(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, triggers in by_project.items():
        load(
            neo4j_session,
            RailwayDeploymentTriggerSchema(),
            triggers,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in project_ids:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            RailwayDeploymentSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            RailwayFilesystemSnapshotSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            RailwayDeploymentTriggerSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
