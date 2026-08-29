import logging
import re
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.serviceinstances import EMPTY_EXTERNAL_IMAGE_STATE
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.serviceinstances import RailwayExternalImageState
from cartography.intel.railway.serviceinstances import RailwayUnresolvedImageReference
from cartography.intel.railway.utils import preserve_image_relationships
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.deployment import RailwayDeploymentSchema
from cartography.models.railway.deploymenttrigger import RailwayDeploymentTriggerSchema
from cartography.models.railway.filesystem_snapshot import (
    RailwayFilesystemSnapshotSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _current_deployments(instance: dict[str, Any]) -> list[dict[str, Any]]:
    current_deployments = list(instance.get("activeDeployments") or [])
    latest_deployment = instance.get("latestDeployment") or {}
    if latest_deployment.get("status") == "SLEEPING":
        current_deployments.append(latest_deployment)
    return current_deployments


def _runtime_image_deployment(
    instance: dict[str, Any],
    current_deployments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    latest_id = (instance.get("latestDeployment") or {}).get("id")
    return next(
        (
            deployment
            for deployment in current_deployments
            if deployment["id"] == latest_id
        ),
        None,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
    external_images: RailwayExternalImageState = EMPTY_EXTERNAL_IMAGE_STATE,
) -> None:
    deployments, snapshots, triggers = transform(bundles, external_images)
    load_deployments(neo4j_session, deployments, update_tag)
    load_filesystem_snapshots(neo4j_session, snapshots, update_tag)
    load_deployment_triggers(neo4j_session, triggers, update_tag)
    preserve_unresolved_image_relationships(
        neo4j_session,
        bundles,
        external_images,
        update_tag,
    )
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
    external_images: RailwayExternalImageState = EMPTY_EXTERNAL_IMAGE_STATE,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    deployments: dict[str, list[dict[str, Any]]] = {}
    snapshots: dict[str, list[dict[str, Any]]] = {}
    triggers: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        environments = unwrap_edges(bundle["environments"])
        project_deployments_by_id = {
            deployment["id"]: deployment
            for environment in environments
            for deployment in unwrap_edges(environment["deployments"])
        }

        current_instances: dict[str, dict[str, Any]] = {}
        runtime_image_instances: dict[str, dict[str, Any]] = {}
        for instance in iter_service_instances(bundle):
            current_deployments = _current_deployments(instance)
            for deployment in current_deployments:
                project_deployments_by_id[deployment["id"]] = deployment
                current_instances[deployment["id"]] = instance
            runtime_image_deployment = _runtime_image_deployment(
                instance,
                current_deployments,
            )
            if runtime_image_deployment:
                runtime_image_instances[runtime_image_deployment["id"]] = instance

        project_deployments: list[dict[str, Any]] = []
        project_snapshots: list[dict[str, Any]] = []
        project_triggers: list[dict[str, Any]] = []
        for deployment in project_deployments_by_id.values():
            meta = deployment.get("meta")
            commit_hash = meta.get("commitHash") if isinstance(meta, dict) else None
            source_revision = (
                commit_hash.lower()
                if isinstance(commit_hash, str)
                and re.fullmatch(r"[0-9a-fA-F]{40}", commit_hash)
                else None
            )
            current_instance = current_instances.get(deployment["id"])
            runtime_image_instance = runtime_image_instances.get(deployment["id"])
            binding = (
                external_images.by_instance_id.get(runtime_image_instance["id"])
                if runtime_image_instance
                else None
            )
            project_deployments.append(
                {
                    **deployment,
                    "source_revision": source_revision,
                    "lifecycle": "current" if current_instance else "historical",
                    "source_image": (
                        (runtime_image_instance.get("source") or {}).get("image")
                        if runtime_image_instance
                        else None
                    ),
                    "source_image_normalized": (
                        binding.reference.normalized if binding else None
                    ),
                    "source_image_digest": (
                        binding.reference.digest if binding else None
                    ),
                    # Resolving a mutable tag proves its current target, not what this
                    # deployment ran. Only an explicit digest is runtime evidence.
                    "resolved_source_image_digest": (
                        binding.resolved_digest
                        if binding and binding.reference.digest
                        else None
                    ),
                },
            )
            source_repo = meta.get("repo") if isinstance(meta, dict) else None
            root_directory = (
                meta.get("rootDirectory") if isinstance(meta, dict) else None
            )
            if (
                current_instance
                and source_revision
                and isinstance(meta, dict)
                and isinstance(source_repo, str)
                and source_repo
                and "rootDirectory" in meta
                and (root_directory is None or isinstance(root_directory, str))
            ):
                project_snapshots.append(
                    {
                        "id": f"railway:filesystem-snapshot:{deployment['id']}",
                        "deployment_id": deployment["id"],
                        "kind": "source",
                        "source_revision": source_revision,
                        "source_repo": source_repo,
                        "root_directory": root_directory,
                    },
                )
        for environment in environments:
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


def preserve_unresolved_image_relationships(
    neo4j_session: neo4j.Session,
    bundles: dict[str, dict[str, Any]],
    external_images: RailwayExternalImageState,
    update_tag: int,
) -> None:
    unresolved_deployments: dict[str, RailwayUnresolvedImageReference] = {}
    for bundle in bundles.values():
        for instance in iter_service_instances(bundle):
            unresolved = external_images.unresolved_by_instance_id.get(instance["id"])
            runtime_image_deployment = _runtime_image_deployment(
                instance,
                _current_deployments(instance),
            )
            if unresolved and runtime_image_deployment:
                unresolved_deployments[runtime_image_deployment["id"]] = unresolved
    if not unresolved_deployments:
        return
    unresolved_images = [
        {
            "source_id": deployment_id,
            "source_reference": unresolved.source_reference,
            "normalized_reference": unresolved.normalized_reference,
        }
        for deployment_id, unresolved in sorted(unresolved_deployments.items())
    ]
    preserve_image_relationships(
        neo4j_session,
        unresolved_images,
        "RailwayDeployment",
        "ExternalContainerImage",
        update_tag,
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
