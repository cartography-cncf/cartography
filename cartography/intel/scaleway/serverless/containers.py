import logging
from typing import Any

import neo4j
import scaleway
from scaleway.container.v1beta1 import Container
from scaleway.container.v1beta1 import ContainerV1Beta1API
from scaleway.container.v1beta1 import Namespace
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.serverless.container import (
    ScalewayServerlessContainerSchema,
)
from cartography.models.scaleway.serverless.container_namespace import (
    ScalewayServerlessContainerNamespaceSchema,
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
    namespaces, containers = get(client, org_id)
    namespaces_by_project, containers_by_project = transform(namespaces, containers)
    load_containers(
        neo4j_session, namespaces_by_project, containers_by_project, update_tag
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Namespace], list[Container]]:
    api = ContainerV1Beta1API(client)
    namespaces = list_all_regions(api.list_namespaces_all, organization_id=org_id)
    # Containers can only be listed per-namespace (namespace_id is required); the
    # namespace already knows its region, so query each one directly.
    containers: list[Container] = []
    for namespace in namespaces:
        # A namespace can be deleted between the list and this per-namespace
        # call; skip it on a 404 rather than aborting the whole sync, but let
        # any other API error surface.
        try:
            containers.extend(
                api.list_containers_all(
                    region=namespace.region, namespace_id=namespace.id
                )
            )
        except ScalewayException as exc:
            if exc.status_code == 404:
                logger.warning(
                    "Skipping Scaleway containers for namespace %s: not found (%s).",
                    namespace.id,
                    exc,
                )
                continue
            raise
    return namespaces, containers


def transform(
    namespaces: list[Namespace],
    containers: list[Container],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    namespaces_by_project: dict[str, list[dict[str, Any]]] = {}
    containers_by_project: dict[str, list[dict[str, Any]]] = {}

    # Containers inherit the project of their parent namespace: the API does not
    # return project_id on them.
    project_by_namespace_id = {ns.id: ns.project_id for ns in namespaces}

    for namespace in namespaces:
        namespaces_by_project.setdefault(namespace.project_id, []).append(
            scaleway_obj_to_dict(namespace)
        )

    for container in containers:
        project_id = project_by_namespace_id.get(container.namespace_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway container %s: unknown parent namespace %s.",
                container.id,
                container.namespace_id,
            )
            continue
        containers_by_project.setdefault(project_id, []).append(
            scaleway_obj_to_dict(container)
        )

    return namespaces_by_project, containers_by_project


@timeit
def load_containers(
    neo4j_session: neo4j.Session,
    namespaces_by_project: dict[str, list[dict[str, Any]]],
    containers_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, namespaces in namespaces_by_project.items():
        logger.info(
            "Loading %d Scaleway container namespaces in project '%s' into Neo4j.",
            len(namespaces),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayServerlessContainerNamespaceSchema(),
            namespaces,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, containers in containers_by_project.items():
        load(
            neo4j_session,
            ScalewayServerlessContainerSchema(),
            containers,
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
        # Children before parent: Container -> ContainerNamespace.
        GraphJob.from_node_schema(
            ScalewayServerlessContainerSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayServerlessContainerNamespaceSchema(), scoped_job_parameters
        ).run(neo4j_session)
