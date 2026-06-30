import logging
from typing import Any

import neo4j
import scaleway
from scaleway.registry.v1 import Image
from scaleway.registry.v1 import Namespace
from scaleway.registry.v1 import RegistryV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from cartography.models.scaleway.container_registry.namespace import (
    ScalewayContainerRegistryNamespaceSchema,
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
    namespaces, images = get(client, org_id)
    namespaces_by_project, images_by_project = transform_namespaces(namespaces, images)
    load_namespaces(neo4j_session, namespaces_by_project, images_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Namespace], list[Image]]:
    api = RegistryV1API(client)
    namespaces = list_all_regions(api.list_namespaces_all, organization_id=org_id)
    # Images are listable per-region with org_id, no need to iterate per
    # namespace. This both saves API calls and keeps the cross-namespace
    # ordering stable.
    images = list_all_regions(api.list_images_all, organization_id=org_id)
    return namespaces, images


def transform_namespaces(
    namespaces: list[Namespace],
    images: list[Image],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    namespaces_by_project: dict[str, list[dict[str, Any]]] = {}
    images_by_project: dict[str, list[dict[str, Any]]] = {}

    # Images inherit the project of their parent namespace: the API does not
    # return project_id on them.
    project_by_namespace_id = {ns.id: ns.project_id for ns in namespaces}

    for namespace in namespaces:
        namespaces_by_project.setdefault(namespace.project_id, []).append(
            scaleway_obj_to_dict(namespace)
        )

    for image in images:
        project_id = project_by_namespace_id.get(image.namespace_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway Container Registry image %s: unknown parent namespace %s.",
                image.id,
                image.namespace_id,
            )
            continue
        images_by_project.setdefault(project_id, []).append(scaleway_obj_to_dict(image))

    return namespaces_by_project, images_by_project


@timeit
def load_namespaces(
    neo4j_session: neo4j.Session,
    namespaces_by_project: dict[str, list[dict[str, Any]]],
    images_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, namespaces in namespaces_by_project.items():
        logger.info(
            "Loading %d Scaleway Container Registry namespaces in project '%s' into Neo4j.",
            len(namespaces),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayContainerRegistryNamespaceSchema(),
            namespaces,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, images in images_by_project.items():
        load(
            neo4j_session,
            ScalewayContainerRegistryImageSchema(),
            images,
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
        # Children before parent: Image -> Namespace.
        GraphJob.from_node_schema(
            ScalewayContainerRegistryImageSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayContainerRegistryNamespaceSchema(), scoped_job_parameters
        ).run(neo4j_session)
