import logging

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource

from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.manifest import cleanup_manifests
from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.repository import (
    sync_artifact_registry_repositories,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Resource,
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

    :param neo4j_session: The Neo4j session.
    :param client: The Artifact Registry API client.
    :param credentials: GCP credentials (unused but kept for API compatibility).
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.info(f"Syncing Artifact Registry for project {project_id}.")

    # Sync repositories
    repositories_raw = sync_artifact_registry_repositories(
        neo4j_session,
        client,
        project_id,
        update_tag,
        common_job_parameters,
    )

    # Sync artifacts for all repositories
    # This now returns transformed platform images from the imageManifests field
    platform_images = sync_artifact_registry_artifacts(
        neo4j_session,
        client,
        repositories_raw,
        project_id,
        update_tag,
        common_job_parameters,
    )

    # Load platform images (manifests) - no HTTP calls needed, data comes from dockerImages API
    if platform_images:
        load_manifests(neo4j_session, platform_images, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_manifests(neo4j_session, cleanup_job_params)
