import logging

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations
from cartography.models.gcp.artifact_registry.repository import (
    GCPArtifactRegistryRepositorySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_artifact_registry_repositories(client: Resource, project_id: str) -> list[dict]:
    """
    Gets GCP Artifact Registry repositories for a project across all locations.
    """
    repositories: list[dict] = []

    locations = get_artifact_registry_locations(client, project_id)
    if not locations:
        return []

    for location in locations:
        try:
            parent = f"projects/{project_id}/locations/{location}"
            request = client.projects().locations().repositories().list(parent=parent)
            while request is not None:
                response = request.execute()
                repositories.extend(response.get("repositories", []))
                request = (
                    client.projects()
                    .locations()
                    .repositories()
                    .list_next(
                        previous_request=request,
                        previous_response=response,
                    )
                )
        except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
            logger.warning(
                f"Failed to get Artifact Registry repositories for project {project_id} "
                f"in location {location} due to permissions or auth error: {e}",
            )
            continue
        except HttpError as e:
            logger.debug(
                f"Failed to get Artifact Registry repositories for project {project_id} "
                f"in location {location}: {e}",
            )
            continue

    return repositories


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
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    """
    Syncs GCP Artifact Registry repositories and returns the raw repository data.
    """
    logger.info(f"Syncing Artifact Registry repositories for project {project_id}.")
    repositories_raw = get_artifact_registry_repositories(client, project_id)
    if not repositories_raw:
        logger.info(
            f"No Artifact Registry repositories found for project {project_id}."
        )

    repositories = transform_repositories(repositories_raw, project_id)
    load_repositories(neo4j_session, repositories, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_repositories(neo4j_session, cleanup_job_params)

    return repositories_raw
