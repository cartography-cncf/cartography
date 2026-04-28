import logging
from dataclasses import dataclass
from functools import partial

import neo4j
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import (
    DEFAULT_ARTIFACT_REGISTRY_WORKERS,
)
from cartography.intel.gcp.artifact_registry.util import (
    fetch_artifact_registry_resources,
)
from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations
from cartography.intel.gcp.artifact_registry.util import (
    list_artifact_registry_resources,
)
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.artifact_registry.repository import (
    GCPArtifactRegistryRepositorySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArtifactRegistryRepositorySyncResult:
    repositories: list[dict]
    cleanup_safe: bool


@dataclass(frozen=True)
class LocationRepositoryFetchResult:
    location: str
    repositories: list[dict]
    cleanup_safe: bool


def _list_repositories_for_location(
    client: ArtifactRegistryClient,
    project_id: str,
    location: str,
) -> LocationRepositoryFetchResult:
    try:
        parent = f"projects/{project_id}/locations/{location}"
        repositories = [
            proto_message_to_dict(repository)
            for repository in list_artifact_registry_resources(
                lambda: client.list_repositories(parent=parent)
            )
        ]
        return LocationRepositoryFetchResult(location, repositories, True)
    except PermissionDenied as e:
        logger.warning(
            "Failed to get Artifact Registry repositories for project %s in location %s "
            "due to permissions. Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            location,
            type(e).__name__,
        )
        return LocationRepositoryFetchResult(location, [], False)
    except (DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get Artifact Registry repositories for project %s in location %s "
            "due to auth error. Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            location,
            type(e).__name__,
        )
        return LocationRepositoryFetchResult(location, [], False)
    except GoogleAPICallError:
        logger.error(
            "Unexpected error getting Artifact Registry repositories for project %s in location %s.",
            project_id,
            location,
            exc_info=True,
        )
        raise


@timeit
def get_artifact_registry_repositories(
    client: ArtifactRegistryClient,
    project_id: str,
    max_workers: int = DEFAULT_ARTIFACT_REGISTRY_WORKERS,
) -> ArtifactRegistryRepositorySyncResult:
    """
    Gets GCP Artifact Registry repositories for a project across all locations.
    """
    locations = get_artifact_registry_locations(client, project_id)
    if locations is None:
        return ArtifactRegistryRepositorySyncResult([], False)
    if not locations:
        return ArtifactRegistryRepositorySyncResult([], True)

    fetch_for_location = partial(_list_repositories_for_location, client, project_id)
    location_results = fetch_artifact_registry_resources(
        items=locations,
        fetch_for_item=fetch_for_location,
        resource_type="repositories by location",
        project_id=project_id,
        max_workers=max_workers,
    )

    repositories: list[dict] = []
    nonempty_locations = 0
    cleanup_safe = True
    for result in location_results:
        cleanup_safe = cleanup_safe and result.cleanup_safe
        if result.repositories:
            nonempty_locations += 1
            repositories.extend(result.repositories)

    logger.info(
        "Collected %d Artifact Registry repositories across %d/%d queried locations for project %s.",
        len(repositories),
        nonempty_locations,
        len(locations),
        project_id,
    )
    return ArtifactRegistryRepositorySyncResult(repositories, cleanup_safe)


def transform_repositories(
    repositories_data: list[dict], project_id: str
) -> list[dict]:
    """
    Transforms the list of repository dicts for ingestion.
    """
    transformed: list[dict] = []
    for repo in repositories_data:
        # Extract location from the resource name
        # Format: projects/{project}/locations/{location}/repositories/{repository}
        name_parts = repo.get("name", "").split("/")
        location = name_parts[3] if len(name_parts) > 3 else None
        repo_name = name_parts[-1] if name_parts else None

        # Build the registry URI for Docker format repositories
        registry_uri = None
        if repo.get("format") == "DOCKER" and location:
            registry_uri = f"{location}-docker.pkg.dev/{project_id}/{repo_name}"

        # Check vulnerability scanning config
        vulnerability_scanning_enabled = False
        vuln_config = repo.get("vulnerabilityScanningConfig", {})
        if vuln_config.get("enablementState") == "ENABLED":
            vulnerability_scanning_enabled = True

        # Check cleanup policy dry run mode
        cleanup_policy_dry_run = repo.get("cleanupPolicyDryRun", False)

        transformed.append(
            {
                "id": repo.get("name"),
                "name": repo_name,
                "format": repo.get("format"),
                "mode": repo.get("mode"),
                "description": repo.get("description"),
                "location": location,
                "registry_uri": registry_uri,
                "size_bytes": repo.get("sizeBytes"),
                "kms_key_name": repo.get("kmsKeyName"),
                "create_time": repo.get("createTime"),
                "update_time": repo.get("updateTime"),
                "cleanup_policy_dry_run": cleanup_policy_dry_run,
                "vulnerability_scanning_enabled": vulnerability_scanning_enabled,
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryRepository nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryRepositorySchema(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_repositories(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Artifact Registry repositories.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryRepositorySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_artifact_registry_repositories(
    neo4j_session: neo4j.Session,
    client: ArtifactRegistryClient,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> ArtifactRegistryRepositorySyncResult:
    """
    Syncs GCP Artifact Registry repositories and returns the raw repository data.
    """
    logger.info(f"Syncing Artifact Registry repositories for project {project_id}.")
    result = get_artifact_registry_repositories(client, project_id)
    repositories_raw = result.repositories
    if not repositories_raw:
        if result.cleanup_safe:
            logger.info(
                "No Artifact Registry repositories found for project %s.",
                project_id,
            )
        else:
            logger.warning(
                "Artifact Registry repository discovery incomplete for project %s; no repositories will be loaded and cleanup will be skipped.",
                project_id,
            )

    repositories = transform_repositories(repositories_raw, project_id)
    load_repositories(neo4j_session, repositories, project_id, update_tag)

    if result.cleanup_safe:
        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_repositories(neo4j_session, cleanup_job_params)
    else:
        logger.warning(
            "Skipping Artifact Registry repository cleanup for project %s because repository discovery was incomplete.",
            project_id,
        )

    return result
