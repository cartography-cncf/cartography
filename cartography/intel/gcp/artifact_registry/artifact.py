import logging

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.artifact_registry.artifact import (
    GCPArtifactRegistryArtifactSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_docker_images(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets Docker images for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Docker image dicts from the API.
    """
    images: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .dockerImages()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            images.extend(response.get("dockerImages", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .dockerImages()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return images
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Docker images for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_maven_artifacts(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets Maven artifacts for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Maven artifact dicts from the API.
    """
    artifacts: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .mavenArtifacts()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            artifacts.extend(response.get("mavenArtifacts", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .mavenArtifacts()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return artifacts
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Maven artifacts for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_npm_packages(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets npm packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of npm package dicts from the API.
    """
    packages: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .npmPackages()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            packages.extend(response.get("npmPackages", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .npmPackages()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return packages
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get npm packages for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_python_packages(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets Python packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Python package dicts from the API.
    """
    packages: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .pythonPackages()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            packages.extend(response.get("pythonPackages", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .pythonPackages()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return packages
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Python packages for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_go_modules(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets Go modules for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Go module dicts from the API.
    """
    modules: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .goModules()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            modules.extend(response.get("goModules", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .goModules()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return modules
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Go modules for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_apt_artifacts(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets APT artifacts for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of APT artifact dicts from the API.
    """
    artifacts: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .aptArtifacts()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            artifacts.extend(response.get("aptArtifacts", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .aptArtifacts()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return artifacts
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get APT artifacts for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_yum_artifacts(client: Resource, repository_name: str) -> list[dict]:
    """
    Gets YUM artifacts for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of YUM artifact dicts from the API.
    """
    artifacts: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .repositories()
            .yumArtifacts()
            .list(parent=repository_name)
        )
        while request is not None:
            response = request.execute()
            artifacts.extend(response.get("yumArtifacts", []))
            request = (
                client.projects()
                .locations()
                .repositories()
                .yumArtifacts()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return artifacts
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get YUM artifacts for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


def transform_docker_images(
    images_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Docker images to the unified artifact format.
    """
    transformed: list[dict] = []
    for image in images_data:
        name = image.get("name", "")
        uri = image.get("uri", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "DOCKER",
                "uri": uri,
                "create_time": image.get("uploadTime"),
                "update_time": image.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties
                "digest": uri.split("@")[-1] if "@" in uri else None,
                "tags": image.get("tags"),
                "image_size_bytes": image.get("imageSizeBytes"),
                "media_type": image.get("mediaType"),
                "artifact_type": None,
                "upload_time": image.get("uploadTime"),
                "build_time": image.get("buildTime"),
                # Package-specific properties (not applicable)
                "version": None,
                "display_name": None,
                "annotations": None,
            }
        )
    return transformed


def transform_maven_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Maven artifacts to the unified artifact format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")
        # Build display name from groupId:artifactId
        group_id = artifact.get("groupId", "")
        artifact_id = artifact.get("artifactId", "")
        display_name = f"{group_id}:{artifact_id}" if group_id and artifact_id else None

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "MAVEN",
                "uri": artifact.get("pomUri"),
                "create_time": artifact.get("createTime"),
                "update_time": artifact.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": None,
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": artifact.get("version"),
                "display_name": display_name,
                "annotations": None,
            }
        )
    return transformed


def transform_npm_packages(
    packages_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms npm packages to the unified artifact format.
    """
    transformed: list[dict] = []
    for package in packages_data:
        name = package.get("name", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "NPM",
                "uri": package.get("uri"),
                "create_time": package.get("createTime"),
                "update_time": package.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": package.get("tags"),
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": package.get("version"),
                "display_name": package.get("packageName"),
                "annotations": None,
            }
        )
    return transformed


def transform_python_packages(
    packages_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Python packages to the unified artifact format.
    """
    transformed: list[dict] = []
    for package in packages_data:
        name = package.get("name", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "PYTHON",
                "uri": package.get("uri"),
                "create_time": package.get("createTime"),
                "update_time": package.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": None,
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": package.get("version"),
                "display_name": package.get("packageName"),
                "annotations": None,
            }
        )
    return transformed


def transform_go_modules(
    modules_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Go modules to the unified artifact format.
    """
    transformed: list[dict] = []
    for module in modules_data:
        name = module.get("name", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "GO",
                "uri": None,
                "create_time": module.get("createTime"),
                "update_time": module.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": None,
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": module.get("version"),
                "display_name": None,
                "annotations": None,
            }
        )
    return transformed


def transform_apt_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms APT artifacts to the unified artifact format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "APT",
                "uri": None,
                "create_time": None,
                "update_time": None,
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": None,
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": None,
                "display_name": artifact.get("packageName"),
                "annotations": None,
            }
        )
    return transformed


def transform_yum_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms YUM artifacts to the unified artifact format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")

        transformed.append(
            {
                # Common properties
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "YUM",
                "uri": None,
                "create_time": None,
                "update_time": None,
                "repository_id": repository_id,
                "project_id": project_id,
                # Docker-specific properties (not applicable)
                "digest": None,
                "tags": None,
                "image_size_bytes": None,
                "media_type": None,
                "artifact_type": None,
                "upload_time": None,
                "build_time": None,
                # Package-specific properties
                "version": None,
                "display_name": artifact.get("packageName"),
                "annotations": None,
            }
        )
    return transformed


# Mapping of repository format to get and transform functions
FORMAT_HANDLERS = {
    "DOCKER": (get_docker_images, transform_docker_images),
    "MAVEN": (get_maven_artifacts, transform_maven_artifacts),
    "NPM": (get_npm_packages, transform_npm_packages),
    "PYTHON": (get_python_packages, transform_python_packages),
    "GO": (get_go_modules, transform_go_modules),
    "APT": (get_apt_artifacts, transform_apt_artifacts),
    "YUM": (get_yum_artifacts, transform_yum_artifacts),
}


@timeit
def load_artifacts(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryArtifact nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryArtifactSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_artifacts(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Artifact Registry artifacts.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryArtifactSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_artifact_registry_artifacts(
    neo4j_session: neo4j.Session,
    client: Resource,
    repositories: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    """
    Syncs GCP Artifact Registry artifacts for all repositories.

    :param neo4j_session: The Neo4j session.
    :param client: The Artifact Registry API client.
    :param repositories: List of raw repository data from the API.
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    :return: List of all raw artifact data from the API.
    """
    logger.info(f"Syncing Artifact Registry artifacts for project {project_id}.")

    all_artifacts_raw: list[dict] = []
    all_artifacts_transformed: list[dict] = []

    for repo in repositories:
        repo_name = repo.get("name")
        repo_format = repo.get("format")

        if not repo_name or not repo_format:
            continue

        handlers = FORMAT_HANDLERS.get(repo_format)
        if handlers is None:
            logger.debug(
                f"No artifact handler for format {repo_format} in repository {repo_name}"
            )
            continue

        get_func, transform_func = handlers

        try:
            artifacts_raw = get_func(client, repo_name)
            if artifacts_raw:
                all_artifacts_raw.extend(artifacts_raw)
                artifacts_transformed = transform_func(
                    artifacts_raw, repo_name, project_id
                )
                all_artifacts_transformed.extend(artifacts_transformed)
        except (PermissionDenied, DefaultCredentialsError, RefreshError, HttpError):
            # Already logged in the individual get functions
            continue

    if not all_artifacts_transformed:
        logger.info(f"No Artifact Registry artifacts found for project {project_id}.")
    else:
        load_artifacts(neo4j_session, all_artifacts_transformed, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_artifacts(neo4j_session, cleanup_job_params)

    return all_artifacts_raw
