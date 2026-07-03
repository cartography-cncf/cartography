import logging
from typing import Any

import neo4j
import scaleway
from scaleway.registry.v1 import Image
from scaleway.registry.v1 import Namespace
from scaleway.registry.v1 import RegistryV1API
from scaleway.registry.v1 import Tag
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_REGIONS
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from cartography.models.scaleway.container_registry.image_tag import (
    ScalewayContainerRegistryImageTagSchema,
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
) -> dict[str, str]:
    namespaces, images, tags = get(client, org_id)
    namespaces_by_project, images_by_project, tags_by_project = transform_namespaces(
        namespaces, images, tags
    )
    load_namespaces(
        neo4j_session,
        namespaces_by_project,
        images_by_project,
        tags_by_project,
        update_tag,
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)
    # Return the tag URI -> digest map so downstream syncs (e.g. serverless
    # containers) can resolve a `registry_image` pull URI to its digest and
    # declare a HAS_IMAGE relationship to the Image node.
    return {
        tag["uri"]: tag["digest"]
        for tags in tags_by_project.values()
        for tag in tags
        if tag.get("uri") and tag.get("digest")
    }


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Namespace], list[Image], list[Tag]]:
    api = RegistryV1API(client)
    namespaces = list_all_regions(api.list_namespaces_all, organization_id=org_id)
    # Images and tags are region-scoped and tags can only be listed per-image
    # (image_id is required), so fan out over regions and query each image's
    # tags in the region it was found in. The "named image" (list_images) is
    # only used here to enumerate images and carry name/visibility onto their
    # tags; it is not persisted as its own node (Scaleway's namespace is the
    # registry, mirroring GCP's Artifact Registry repository).
    images: list[Image] = []
    tags: list[Tag] = []
    for region in DEFAULT_REGIONS:
        try:
            region_images = api.list_images_all(region=region, organization_id=org_id)
        except ScalewayException as exc:
            if "unknown service" in str(exc).lower():
                logger.info(
                    "Scaleway Container Registry not available in region %s, skipping.",
                    region,
                )
                continue
            raise
        images.extend(region_images)
        for image in region_images:
            tags.extend(api.list_tags_all(image_id=image.id, region=region))
    return namespaces, images, tags


def transform_namespaces(
    namespaces: list[Namespace],
    images: list[Image],
    tags: list[Tag],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    namespaces_by_project: dict[str, list[dict[str, Any]]] = {}
    # Digest-addressed image content, deduplicated by digest per project.
    images_by_project: dict[str, list[dict[str, Any]]] = {}
    tags_by_project: dict[str, list[dict[str, Any]]] = {}

    project_by_namespace_id = {ns.id: ns.project_id for ns in namespaces}
    endpoint_by_namespace_id = {ns.id: ns.endpoint for ns in namespaces}

    for namespace in namespaces:
        namespaces_by_project.setdefault(namespace.project_id, []).append(
            scaleway_obj_to_dict(namespace)
        )

    # Resolve each named image to the project/namespace/name/visibility we
    # denormalize onto its tags. The named image is not loaded as a node.
    image_meta: dict[str, dict[str, Any]] = {}
    for image in images:
        project_id = project_by_namespace_id.get(image.namespace_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway Container Registry image %s: unknown parent namespace %s.",
                image.id,
                image.namespace_id,
            )
            continue
        image_dict = scaleway_obj_to_dict(image)
        image_meta[image.id] = {
            "project_id": project_id,
            "namespace_id": image.namespace_id,
            "name": image_dict.get("name"),
            "visibility": image_dict.get("visibility"),
            "endpoint": endpoint_by_namespace_id.get(image.namespace_id),
        }

    seen_digests: dict[str, set[str]] = {}
    for tag in tags:
        meta = image_meta.get(tag.image_id)
        if meta is None:
            logger.warning(
                "Skipping Scaleway Container Registry tag %s: unknown parent image %s.",
                tag.id,
                tag.image_id,
            )
            continue
        project_id = meta["project_id"]
        row = scaleway_obj_to_dict(tag)
        row["image_name"] = meta["name"]
        row["visibility"] = meta["visibility"]
        row["namespace_id"] = meta["namespace_id"]
        if meta["endpoint"] and meta["name"]:
            row["uri"] = f"{meta['endpoint']}/{meta['name']}:{tag.name}"
        else:
            row["uri"] = None
        tags_by_project.setdefault(project_id, []).append(row)

        if tag.digest:
            project_digests = seen_digests.setdefault(project_id, set())
            if tag.digest not in project_digests:
                project_digests.add(tag.digest)
                images_by_project.setdefault(project_id, []).append(
                    {"digest": tag.digest}
                )

    return namespaces_by_project, images_by_project, tags_by_project


@timeit
def load_namespaces(
    neo4j_session: neo4j.Session,
    namespaces_by_project: dict[str, list[dict[str, Any]]],
    images_by_project: dict[str, list[dict[str, Any]]],
    tags_by_project: dict[str, list[dict[str, Any]]],
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
    # Digest images before tags so the tag -> IMAGE -> image edge resolves at
    # load time.
    for project_id, images in images_by_project.items():
        load(
            neo4j_session,
            ScalewayContainerRegistryImageSchema(),
            images,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, tags in tags_by_project.items():
        load(
            neo4j_session,
            ScalewayContainerRegistryImageTagSchema(),
            tags,
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
        # Children before parents: Tag -> Image -> Namespace.
        GraphJob.from_node_schema(
            ScalewayContainerRegistryImageTagSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayContainerRegistryImageSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayContainerRegistryNamespaceSchema(), scoped_job_parameters
        ).run(neo4j_session)
