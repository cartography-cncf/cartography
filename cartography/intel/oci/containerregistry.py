# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Container Registry (OCIR) API-centric functions
# https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm
# https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryconcepts.htm
#
# Covers:
#   - Container Repositories
#   - Container Images
#   - Repository → Image relationships
#   - Compartment → Repository relationships
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.artifacts

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ============================================================
# Container Repositories
# ============================================================

def get_container_repository_list_data(
    artifacts_client: oci.artifacts.ArtifactsClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all container repositories in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/registry/latest/ContainerRepository/ListContainerRepositories
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            artifacts_client.list_container_repositories,
            compartment_id=compartment_id,
        )
        # list_container_repositories returns a ContainerRepositoryCollection
        # with an 'items' attribute containing the list of repositories
        data = response.data
        if hasattr(data, 'items'):
            return {'Repositories': utils.oci_object_to_json(f"[{data}]")[0].get("items", [])}
        return {'Repositories': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve container repositories for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Repositories': []}


def get_container_repository_details(
    artifacts_client: oci.artifacts.ArtifactsClient,
    repository_id: str,
) -> Dict[str, Any]:
    """
    Get full details of a container repository.
    See https://docs.oracle.com/en-us/iaas/api/#/en/registry/latest/ContainerRepository/GetContainerRepository
    """
    try:
        response = artifacts_client.get_container_repository(repository_id=repository_id)
        return utils.oci_single_object_to_json(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve container repository details for '%s': %s",
            repository_id, e.message,
        )
        return {}


def load_container_repositories(
    neo4j_session: neo4j.Session,
    repositories: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Container Repository data into Neo4j.
    """
    ingest_repo = """
    MERGE (repo:OCIContainerRepository{ocid: $OCID})
    ON CREATE SET repo.firstseen = timestamp(),
    repo.createdate = $TIME_CREATED
    SET repo.display_name = $DISPLAY_NAME,
    repo.compartment_id = $COMPARTMENT_ID,
    repo.resource_type = 'oci-containerregistry-repository',
    repo.image_count = $IMAGE_COUNT,
    repo.is_immutable = $IS_IMMUTABLE,
    repo.is_public = $IS_PUBLIC,
    repo.layer_count = $LAYER_COUNT,
    repo.layers_size_in_bytes = $LAYERS_SIZE_IN_BYTES,
    repo.lifecycle_state = $LIFECYCLE_STATE,
    repo.namespace = $NAMESPACE,
    repo.billable_size_in_gbs = $BILLABLE_SIZE_IN_GBS,
    repo.region = $REGION,
    repo.lastupdated = $oci_update_tag
    WITH repo
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(repo)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for repo in repositories:
        neo4j_session.run(
            ingest_repo,
            OCID=repo.get("id"),
            DISPLAY_NAME=repo.get("display-name", ""),
            COMPARTMENT_ID=repo.get("compartment-id", compartment_id),
            IMAGE_COUNT=repo.get("image-count", 0),
            IS_IMMUTABLE=repo.get("is-immutable", False),
            IS_PUBLIC=repo.get("is-public", False),
            LAYER_COUNT=repo.get("layer-count", 0),
            LAYERS_SIZE_IN_BYTES=repo.get("layers-size-in-bytes", 0),
            LIFECYCLE_STATE=repo.get("lifecycle-state", ""),
            NAMESPACE=repo.get("namespace", ""),
            BILLABLE_SIZE_IN_GBS=repo.get("billable-size-in-gbs", 0),
            REGION=region,
            TIME_CREATED=str(repo.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_container_repositories(
    neo4j_session: neo4j.Session,
    artifacts_client: oci.artifacts.ArtifactsClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """Sync all container repositories across compartments."""
    logger.debug(
        "Syncing OCI container repositories for tenancy '%s', region '%s'.",
        tenancy_id, region,
    )
    for compartment in compartments:
        data = get_container_repository_list_data(artifacts_client, compartment["ocid"])
        if data["Repositories"]:
            load_container_repositories(
                neo4j_session, data["Repositories"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Container Images
# ============================================================

def get_container_image_list_data(
    artifacts_client: oci.artifacts.ArtifactsClient,
    compartment_id: str,
    repository_id: str = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all container images in a compartment, optionally filtered by repository.
    See https://docs.oracle.com/en-us/iaas/api/#/en/registry/latest/ContainerImage/ListContainerImages
    """
    try:
        kwargs = {"compartment_id": compartment_id}
        if repository_id:
            kwargs["repository_id"] = repository_id
        response = oci.pagination.list_call_get_all_results(
            artifacts_client.list_container_images,
            **kwargs,
        )
        data = response.data
        if hasattr(data, 'items'):
            return {'Images': utils.oci_object_to_json(f"[{data}]")[0].get("items", [])}
        return {'Images': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve container images for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Images': []}


def load_container_images(
    neo4j_session: neo4j.Session,
    images: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Container Image data into Neo4j and link to repository.
    """
    ingest_image = """
    MERGE (img:OCIContainerImage{ocid: $OCID})
    ON CREATE SET img.firstseen = timestamp(),
    img.createdate = $TIME_CREATED
    SET img.display_name = $DISPLAY_NAME,
    img.compartment_id = $COMPARTMENT_ID,
    img.resource_type = 'oci-containerregistry-image',
    img.digest = $DIGEST,
    img.lifecycle_state = $LIFECYCLE_STATE,
    img.repository_id = $REPOSITORY_ID,
    img.repository_name = $REPOSITORY_NAME,
    img.version = $VERSION,
    img.versions_count = $VERSIONS_COUNT,
    img.layers_size_in_bytes = $LAYERS_SIZE_IN_BYTES,
    img.time_last_pushed = $TIME_LAST_PUSHED,
    img.region = $REGION,
    img.lastupdated = $oci_update_tag
    WITH img
    MATCH (repo:OCIContainerRepository{ocid: $REPOSITORY_ID})
    MERGE (repo)-[r:OCI_CONTAINER_IMAGE]->(img)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for image in images:
        neo4j_session.run(
            ingest_image,
            OCID=image.get("id"),
            DISPLAY_NAME=image.get("display-name", image.get("repository-name", "")),
            COMPARTMENT_ID=image.get("compartment-id", compartment_id),
            DIGEST=image.get("digest", ""),
            LIFECYCLE_STATE=image.get("lifecycle-state", ""),
            REPOSITORY_ID=image.get("repository-id", ""),
            REPOSITORY_NAME=image.get("repository-name", ""),
            VERSION=image.get("version", ""),
            VERSIONS_COUNT=image.get("versions-count", 0),
            LAYERS_SIZE_IN_BYTES=image.get("layers-size-in-bytes", 0),
            TIME_LAST_PUSHED=str(image.get("time-last-pushed", "")),
            REGION=region,
            TIME_CREATED=str(image.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_container_images(
    neo4j_session: neo4j.Session,
    artifacts_client: oci.artifacts.ArtifactsClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """Sync all container images across compartments."""
    logger.debug(
        "Syncing OCI container images for tenancy '%s', region '%s'.",
        tenancy_id, region,
    )
    for compartment in compartments:
        data = get_container_image_list_data(artifacts_client, compartment["ocid"])
        if data["Images"]:
            load_container_images(
                neo4j_session, data["Images"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Top-level sync function
# ============================================================

def sync(
    neo4j_session: neo4j.Session,
    artifacts: oci.artifacts.ArtifactsClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Container Registry resources: Container Repositories and
    Container Images.
    """
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Container Registry for compartment '%s'.", compartment_ocid)

    compartments = [
        {"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id},
    ]

    if not regions:
        regions = [artifacts.base_client.region or ""]

    for region in regions:
        logger.info(
            "Syncing OCI Container Registry in region '%s' for compartment '%s'.",
            region, compartment_ocid,
        )
        artifacts.base_client.set_region(region)

        # Sync container repositories first (parent of images)
        sync_container_repositories(
            neo4j_session, artifacts, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync container images (linked to repositories)
        sync_container_images(
            neo4j_session, artifacts, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale container registry nodes
    run_cleanup_job(
        'oci_import_containerregistry_cleanup.json', neo4j_session, common_job_parameters,
    )
