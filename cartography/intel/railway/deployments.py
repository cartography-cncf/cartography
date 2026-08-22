import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_image import parse_image_uri
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.deployment import RailwayDeploymentSchema
from cartography.models.railway.deploymenttrigger import RailwayDeploymentTriggerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
) -> None:
    deployments, triggers = transform(bundles)
    load_deployments(neo4j_session, deployments, update_tag)
    load_deployment_triggers(neo4j_session, triggers, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    deployments: dict[str, list[dict[str, Any]]] = {}
    triggers: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        instances = iter_service_instances(bundle)
        # The deployment each service instance is currently serving. Everything else in the
        # window is a superseded revision.
        current_ids = {
            (instance.get("latestDeployment") or {}).get("id") for instance in instances
        }
        current_ids.discard(None)
        # The image reference lives on the parent service instance, not the deployment. Key it
        # by the same (service, environment) pair the WORKLOAD_PARENT edge joins on so we can
        # copy it onto the current revision.
        source_image_by_instance = {
            (instance.get("serviceId"), instance.get("environmentId")): (
                instance.get("source") or {}
            ).get("image")
            for instance in instances
        }

        project_deployments: list[dict[str, Any]] = []
        project_triggers: list[dict[str, Any]] = []
        for environment in unwrap_edges(bundle["environments"]):
            for deployment in unwrap_edges(environment["deployments"]):
                is_current = deployment["id"] in current_ids
                # Only the current revision is guaranteed to run the instance's current source
                # image; a superseded revision may have run something else, so leave it null.
                image_uri, image_digest = (None, None)
                if is_current:
                    image_uri, image_digest = parse_image_uri(
                        source_image_by_instance.get(
                            (
                                deployment.get("serviceId"),
                                deployment.get("environmentId"),
                            ),
                        ),
                    )
                project_deployments.append(
                    {
                        **deployment,
                        "lifecycle": "current" if is_current else "historical",
                        "image_uri": image_uri,
                        "image_digest": image_digest,
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
