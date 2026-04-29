import logging

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials

from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.manifest import cleanup_manifests
from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.repository import (
    sync_artifact_registry_repositories,
)
from cartography.intel.gcp.artifact_registry.supply_chain import (
    sync as sync_supply_chain,
)
from cartography.intel.gcp.clients import build_artifact_registry_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: GoogleCredentials,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Artifact Registry resources for a project.

    This function orchestrates the sync of all Artifact Registry resources:
    1. Repositories
    2. Artifacts (Docker images, Maven, npm, Python, Go, APT, YUM)
    3. Image manifests (for multi-architecture Docker images, extracted from imageManifests field)
    4. Supply chain provenance (source repo + layer data from OCI image configs)

    :param neo4j_session: The Neo4j session.
    :param credentials: GCP credentials used to build the GAPIC Artifact Registry client
                        and for Docker Registry API calls (supply chain provenance).
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.info(f"Syncing Artifact Registry for project {project_id}.")
    artifact_registry_client = build_artifact_registry_client(credentials=credentials)

    # Sync repositories
    repository_result = sync_artifact_registry_repositories(
        neo4j_session,
        artifact_registry_client,
        project_id,
        update_tag,
        common_job_parameters,
    )

    # Sync artifacts for all repositories
    artifact_result = sync_artifact_registry_artifacts(
        neo4j_session,
        artifact_registry_client,
        repository_result.repositories,
        project_id,
        update_tag,
        common_job_parameters,
        cleanup_safe=repository_result.cleanup_safe,
    )

    # Load platform images (manifests) - no HTTP calls needed, data comes from dockerImages API
    if artifact_result.platform_images:
        load_manifests(
            neo4j_session,
            artifact_result.platform_images,
            project_id,
            update_tag,
        )

    if artifact_result.cleanup_safe:
        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_manifests(neo4j_session, cleanup_job_params)
    else:
        logger.warning(
            "Skipping Artifact Registry manifest cleanup for project %s because artifact discovery was incomplete.",
            project_id,
        )

    # Enrich images with build provenance and layer data from OCI configs
    if artifact_result.docker_images_raw:
        sync_supply_chain(
            neo4j_session,
            credentials,
            artifact_result.docker_images_raw,
            project_id,
            update_tag,
            common_job_parameters,
            cleanup_safe=artifact_result.cleanup_safe,
        )
