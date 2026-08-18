import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.railway.serviceinstances import EMPTY_EXTERNAL_IMAGE_STATE
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.serviceinstances import RailwayExternalImageState
from cartography.intel.railway.serviceinstances import RailwayUnresolvedImageReference
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.deployment import RailwayDeploymentSchema
from cartography.models.railway.deploymenttrigger import RailwayDeploymentTriggerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _successful_latest_deployment_id(instance: dict[str, Any]) -> str | None:
    latest_deployment = instance.get("latestDeployment") or {}
    if latest_deployment.get("status") != "SUCCESS":
        return None
    return latest_deployment.get("id")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
    external_images: RailwayExternalImageState = EMPTY_EXTERNAL_IMAGE_STATE,
) -> None:
    deployments, triggers = transform(bundles, external_images)
    load_deployments(neo4j_session, deployments, update_tag)
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
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    deployments: dict[str, list[dict[str, Any]]] = {}
    triggers: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        configured_images = {
            (instance["serviceId"], instance["environmentId"]): (
                (instance.get("source") or {}).get("image")
            )
            for instance in iter_service_instances(bundle)
        }
        # latestDeployment can be a pending or failed attempt rather than a running revision.
        # Without Railway's exact active-deployment signal, only SUCCESS is runtime evidence;
        # do not guess that an older successful deployment is active.
        current_ids = {
            _successful_latest_deployment_id(instance)
            for instance in iter_service_instances(bundle)
        }
        current_ids.discard(None)

        project_deployments: list[dict[str, Any]] = []
        project_triggers: list[dict[str, Any]] = []
        for environment in unwrap_edges(bundle["environments"]):
            for deployment in unwrap_edges(environment["deployments"]):
                is_current = deployment["id"] in current_ids
                binding = (
                    external_images.by_service_environment.get(
                        (deployment["serviceId"], deployment["environmentId"]),
                    )
                    if is_current
                    else None
                )
                project_deployments.append(
                    {
                        **deployment,
                        "lifecycle": "current" if is_current else "historical",
                        "source_image": (
                            configured_images.get(
                                (
                                    deployment["serviceId"],
                                    deployment["environmentId"],
                                ),
                            )
                            if is_current
                            else None
                        ),
                        "source_image_normalized": (
                            binding.reference.normalized if binding else None
                        ),
                        "source_image_digest": (
                            binding.reference.digest if binding else None
                        ),
                        # A registry lookup of a mutable tag proves its current target,
                        # not the exact artifact this deployment ran. Only an explicit
                        # digest may feed the Container HAS_IMAGE/RESOLVED_IMAGE path.
                        "resolved_source_image_digest": (
                            binding.resolved_digest
                            if binding and binding.reference.digest
                            else None
                        ),
                    },
                )
            project_triggers.extend(unwrap_edges(environment["deploymentTriggers"]))
        deployments[project_id] = project_deployments
        triggers[project_id] = project_triggers

    return deployments, triggers


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
            deployment_id = _successful_latest_deployment_id(instance)
            unresolved = external_images.unresolved_by_service_environment.get(
                (instance["serviceId"], instance["environmentId"]),
            )
            if deployment_id and unresolved:
                unresolved_deployments[deployment_id] = unresolved
    if not unresolved_deployments:
        return
    unresolved_images = [
        {
            "deployment_id": deployment_id,
            "source_reference": unresolved.source_reference,
            "normalized_reference": unresolved.normalized_reference,
        }
        for deployment_id, unresolved in sorted(unresolved_deployments.items())
    ]
    run_write_query(
        neo4j_session,
        """
        UNWIND $unresolved_images AS unresolved
        MATCH (:RailwayDeployment {id: unresolved.deployment_id})
              -[relationship:HAS_IMAGE]->(:ExternalContainerImage)
        WHERE relationship.source_reference = unresolved.source_reference
           OR (
               unresolved.normalized_reference IS NOT NULL
               AND relationship.normalized_reference = unresolved.normalized_reference
           )
        SET relationship.lastupdated = $update_tag
        """,
        unresolved_images=unresolved_images,
        update_tag=update_tag,
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
            RailwayDeploymentTriggerSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
