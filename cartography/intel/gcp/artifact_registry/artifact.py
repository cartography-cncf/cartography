import logging

import neo4j
from google.api_core.exceptions import GoogleAPICallError
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.util import (
    artifact_registry_message_to_dict,
)
from cartography.intel.gcp.artifact_registry.util import (
    classify_artifact_registry_error,
)
from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import get_error_reason
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.intel.gcp.util import is_billing_disabled_error
from cartography.models.gcp.artifact_registry.artifact import (
    GCPArtifactRegistryGenericArtifactSchema,
)
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryContainerImageSchema,
)
from cartography.models.gcp.artifact_registry.helm_chart import (
    GCPArtifactRegistryHelmChartSchema,
)
from cartography.models.gcp.artifact_registry.language_package import (
    GCPArtifactRegistryLanguagePackageSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _log_skipped_artifact_kind(repository_name: str, artifact_kind: str) -> None:
    logger.warning(
        "Skipping %s enumeration for Artifact Registry repository %s due to access or service state.",
        artifact_kind,
        repository_name,
    )


def _handle_artifact_registry_list_error(
    exc: Exception, repository_name: str, artifact_kind: str
) -> list[dict] | None:
    classification = classify_artifact_registry_error(exc)
    if classification is None:
        raise exc

    _log_skipped_artifact_kind(repository_name, artifact_kind)
    return None


def _list_generated_resources(
    client: ArtifactRegistryClient,
    repository_name: str,
    list_method_name: str,
    artifact_kind: str,
) -> list[dict] | None:
    try:
        pager = getattr(client, list_method_name)(parent=repository_name)
        return [artifact_registry_message_to_dict(item) for item in pager]
    except (GoogleAPICallError, DefaultCredentialsError, RefreshError) as exc:
        return _handle_artifact_registry_list_error(exc, repository_name, artifact_kind)


@timeit
def get_docker_images(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets Docker images for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Docker image dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises HttpError: For errors other than API disabled or permission denied.
    """
    return _list_generated_resources(
        client,
        repository_name,
        "list_docker_images",
        "Docker images",
    )


@timeit
def get_maven_artifacts(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets Maven artifacts for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Maven artifact dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises HttpError: For errors other than API disabled or permission denied.
    """
    return _list_generated_resources(
        client,
        repository_name,
        "list_maven_artifacts",
        "Maven artifacts",
    )


@timeit
def get_npm_packages(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets npm packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of npm package dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises HttpError: For errors other than API disabled or permission denied.
    """
    return _list_generated_resources(
        client,
        repository_name,
        "list_npm_packages",
        "npm packages",
    )


@timeit
def get_python_packages(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets Python packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Python package dicts from the API, or None if API is not enabled.
    :raises HttpError: For errors other than API disabled or permission denied.
    """
    return _list_generated_resources(
        client,
        repository_name,
        "list_python_packages",
        "Python packages",
    )


@timeit
def get_go_modules(client: Resource, repository_name: str) -> list[dict] | None:
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
            response = gcp_api_execute_with_retry(request)
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
    except HttpError as exc:
        if is_api_disabled_error(exc) or is_billing_disabled_error(exc):
            _log_skipped_artifact_kind(repository_name, "Go modules")
            return None
        if get_error_reason(exc) in {
            "forbidden",
            "insufficientPermissions",
            "IAM_PERMISSION_DENIED",
        }:
            _log_skipped_artifact_kind(repository_name, "Go modules")
            return None
        raise
    except (GoogleAPICallError, DefaultCredentialsError, RefreshError) as exc:
        return _handle_artifact_registry_list_error(exc, repository_name, "Go modules")


@timeit
def get_apt_artifacts(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets APT package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of APT package-version dicts from the API.
    """
    try:
        artifacts: list[dict] = []
        for package in client.list_packages(parent=repository_name):
            package_dict = artifact_registry_message_to_dict(package)
            package_name = (
                package_dict.get("displayName")
                or package_dict.get("name", "").split("/packages/")[-1]
            )
            for version in client.list_versions(parent=package_dict.get("name")):
                version_dict = artifact_registry_message_to_dict(version)
                version_dict["packageName"] = package_name
                artifacts.append(version_dict)
        return artifacts
    except (GoogleAPICallError, DefaultCredentialsError, RefreshError) as exc:
        return _handle_artifact_registry_list_error(
            exc, repository_name, "APT package versions"
        )


@timeit
def get_yum_artifacts(
    client: ArtifactRegistryClient, repository_name: str
) -> list[dict] | None:
    """
    Gets YUM package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of YUM package-version dicts from the API.
    """
    try:
        artifacts: list[dict] = []
        for package in client.list_packages(parent=repository_name):
            package_dict = artifact_registry_message_to_dict(package)
            package_name = (
                package_dict.get("displayName")
                or package_dict.get("name", "").split("/packages/")[-1]
            )
            for version in client.list_versions(parent=package_dict.get("name")):
                version_dict = artifact_registry_message_to_dict(version)
                version_dict["packageName"] = package_name
                artifacts.append(version_dict)
        return artifacts
    except (GoogleAPICallError, DefaultCredentialsError, RefreshError) as exc:
        return _handle_artifact_registry_list_error(
            exc, repository_name, "YUM package versions"
        )


def transform_docker_images(
    images_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Docker images to the GCPArtifactRegistryContainerImage node format.
    """
    transformed: list[dict] = []
    for image in images_data:
        name = image.get("name", "")
        uri = image.get("uri", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "uri": uri,
                "digest": uri.split("@")[-1] if "@" in uri else None,
                "tags": image.get("tags"),
                "image_size_bytes": image.get("imageSizeBytes"),
                "media_type": image.get("mediaType"),
                "upload_time": image.get("uploadTime"),
                "build_time": image.get("buildTime"),
                "update_time": image.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
            }
        )
    return transformed


def transform_helm_charts(
    charts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Helm charts to the GCPArtifactRegistryHelmChart node format.

    Helm charts are stored as OCI artifacts in Docker-format repositories,
    so they share a similar structure with Docker images.
    """
    transformed: list[dict] = []
    for chart in charts_data:
        name = chart.get("name", "")
        uri = chart.get("uri", "")
        # Extract version from tags if available, otherwise from URI
        tags = chart.get("tags", [])
        version = tags[0] if tags else None

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "uri": uri,
                "version": version,
                "create_time": chart.get("uploadTime"),
                "update_time": chart.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
            }
        )
    return transformed


def transform_maven_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Maven artifacts to the GCPArtifactRegistryLanguagePackage node format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")
        group_id = artifact.get("groupId", "")
        artifact_id = artifact.get("artifactId", "")
        package_name = f"{group_id}:{artifact_id}" if group_id and artifact_id else None

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "MAVEN",
                "uri": artifact.get("pomUri"),
                "version": artifact.get("version"),
                "package_name": package_name,
                "create_time": artifact.get("createTime"),
                "update_time": artifact.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Maven-specific
                "group_id": group_id if group_id else None,
                "artifact_id": artifact_id if artifact_id else None,
                # NPM-specific (not applicable)
                "tags": None,
            }
        )
    return transformed


def transform_npm_packages(
    packages_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms npm packages to the GCPArtifactRegistryLanguagePackage node format.
    """
    transformed: list[dict] = []
    for package in packages_data:
        name = package.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "NPM",
                "uri": package.get("uri"),
                "version": package.get("version"),
                "package_name": package.get("packageName"),
                "create_time": package.get("createTime"),
                "update_time": package.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Maven-specific (not applicable)
                "group_id": None,
                "artifact_id": None,
                # NPM-specific
                "tags": package.get("tags"),
            }
        )
    return transformed


def transform_python_packages(
    packages_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Python packages to the GCPArtifactRegistryLanguagePackage node format.
    """
    transformed: list[dict] = []
    for package in packages_data:
        name = package.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "PYTHON",
                "uri": package.get("uri"),
                "version": package.get("version"),
                "package_name": package.get("packageName"),
                "create_time": package.get("createTime"),
                "update_time": package.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Maven-specific (not applicable)
                "group_id": None,
                "artifact_id": None,
                # NPM-specific (not applicable)
                "tags": None,
            }
        )
    return transformed


def transform_go_modules(
    modules_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms Go modules to the GCPArtifactRegistryLanguagePackage node format.
    """
    transformed: list[dict] = []
    for module in modules_data:
        name = module.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "GO",
                "uri": None,
                "version": module.get("version"),
                "package_name": None,
                "create_time": module.get("createTime"),
                "update_time": module.get("updateTime"),
                "repository_id": repository_id,
                "project_id": project_id,
                # Maven-specific (not applicable)
                "group_id": None,
                "artifact_id": None,
                # NPM-specific (not applicable)
                "tags": None,
            }
        )
    return transformed


def transform_apt_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms APT artifacts to the GCPArtifactRegistryGenericArtifact node format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "APT",
                "package_name": artifact.get("packageName"),
                "repository_id": repository_id,
                "project_id": project_id,
            }
        )
    return transformed


def transform_yum_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms YUM artifacts to the GCPArtifactRegistryGenericArtifact node format.
    """
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "YUM",
                "package_name": artifact.get("packageName"),
                "repository_id": repository_id,
                "project_id": project_id,
            }
        )
    return transformed


# Mapping of repository format to get and transform functions
FORMAT_HANDLERS = {
    "DOCKER": (get_docker_images, transform_docker_images),
    "MAVEN": (get_maven_artifacts, transform_maven_artifacts),
    "NPM": (get_npm_packages, transform_npm_packages),
    "PYTHON": (get_python_packages, transform_python_packages),
    "GO": (None, transform_go_modules),
    "APT": (get_apt_artifacts, transform_apt_artifacts),
    "YUM": (get_yum_artifacts, transform_yum_artifacts),
}


@timeit
def load_generic_artifacts(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryGenericArtifact nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryGenericArtifactSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_generic_artifacts(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale generic artifact nodes.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryGenericArtifactSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def load_docker_images(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryContainerImage nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryContainerImageSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_docker_images(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Docker image nodes.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryContainerImageSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def load_language_packages(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryLanguagePackage nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryLanguagePackageSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_language_packages(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale language package nodes.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryLanguagePackageSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def load_helm_charts(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryHelmChart nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryHelmChartSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_helm_charts(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Helm chart nodes.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryHelmChartSchema(), common_job_parameters
    ).run(neo4j_session)


# Helm chart media type identifier
HELM_MEDIA_TYPE_IDENTIFIER = "helm"

# Language package formats (Maven, NPM, Python, Go)
LANGUAGE_PACKAGE_FORMATS = {"MAVEN", "NPM", "PYTHON", "GO"}


def transform_image_manifests(
    docker_images_raw: list[dict],
    project_id: str,
) -> list[dict]:
    """
    Transforms image manifests from dockerImages API response to platform image format.

    :param docker_images_raw: List of raw Docker image data from the API.
    :param project_id: The GCP project ID.
    :return: List of transformed platform image dicts.
    """
    from cartography.intel.gcp.artifact_registry.manifest import transform_manifests

    all_manifests: list[dict] = []

    for artifact in docker_images_raw:
        artifact_name = artifact.get("name", "")
        # imageManifests field is returned by the API for multi-arch images
        image_manifests = artifact.get("imageManifests", [])

        if image_manifests:
            # Transform the manifests using the existing transform function
            manifests = transform_manifests(image_manifests, artifact_name, project_id)
            all_manifests.extend(manifests)

    return all_manifests


@timeit
def sync_artifact_registry_artifacts(
    neo4j_session: neo4j.Session,
    client: ArtifactRegistryClient,
    repositories: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: GoogleCredentials,
) -> list[dict]:
    """
    Syncs GCP Artifact Registry artifacts for all repositories.

    :param neo4j_session: The Neo4j session.
    :param client: The Artifact Registry API client.
    :param repositories: List of raw repository data from the API.
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    :return: List of transformed platform image data (from imageManifests field).
    """
    logger.info(f"Syncing Artifact Registry artifacts for project {project_id}.")

    # Separate collections for different artifact types
    docker_images_raw: list[dict] = []
    docker_images_transformed: list[dict] = []
    helm_charts_transformed: list[dict] = []
    language_packages_transformed: list[dict] = []
    other_artifacts_transformed: list[dict] = []
    legacy_go_client: Resource | None = None

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

        if repo_format == "GO":
            if legacy_go_client is None:
                legacy_go_client = build_client(
                    "artifactregistry",
                    "v1",
                    credentials=credentials,
                )
            artifacts_raw = get_go_modules(legacy_go_client, repo_name)
        else:
            get_func, _ = handlers
            artifacts_raw = get_func(client, repo_name) if get_func else None
        if artifacts_raw is None:
            # Skip this repository if API is not enabled or access denied
            continue
        if not artifacts_raw:
            continue

        # Route to appropriate collection based on format
        if repo_format == "DOCKER":
            # Split Docker format artifacts by artifact type
            # Helm charts are stored as OCI artifacts and identified via artifactType or mediaType
            for artifact in artifacts_raw:
                artifact_type = artifact.get("artifactType", "")
                media_type = artifact.get("mediaType", "")
                if (
                    HELM_MEDIA_TYPE_IDENTIFIER in artifact_type.lower()
                    or HELM_MEDIA_TYPE_IDENTIFIER in media_type.lower()
                ):
                    helm_charts_transformed.extend(
                        transform_helm_charts([artifact], repo_name, project_id)
                    )
                else:
                    # Actual Docker images - collect raw for manifest extraction
                    docker_images_raw.append(artifact)
                    docker_images_transformed.extend(
                        transform_docker_images([artifact], repo_name, project_id)
                    )
        elif repo_format in LANGUAGE_PACKAGE_FORMATS:
            # Use the format-specific transformer from FORMAT_HANDLERS
            _, transform_func = handlers
            language_packages_transformed.extend(
                transform_func(artifacts_raw, repo_name, project_id)
            )
        else:
            # APT, YUM, and any other formats use the unified schema
            _, transform_func = handlers
            other_artifacts_transformed.extend(
                transform_func(artifacts_raw, repo_name, project_id)
            )

    # Load Docker images with the dedicated schema
    if docker_images_transformed:
        load_docker_images(
            neo4j_session, docker_images_transformed, project_id, update_tag
        )

    # Load Helm charts with the dedicated schema
    if helm_charts_transformed:
        load_helm_charts(neo4j_session, helm_charts_transformed, project_id, update_tag)

    # Load language packages with the dedicated schema
    if language_packages_transformed:
        load_language_packages(
            neo4j_session, language_packages_transformed, project_id, update_tag
        )

    # Load generic artifacts (APT, YUM) with the dedicated schema
    if other_artifacts_transformed:
        load_generic_artifacts(
            neo4j_session, other_artifacts_transformed, project_id, update_tag
        )

    # Cleanup all node types
    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_docker_images(neo4j_session, cleanup_job_params)
    cleanup_helm_charts(neo4j_session, cleanup_job_params)
    cleanup_language_packages(neo4j_session, cleanup_job_params)
    cleanup_generic_artifacts(neo4j_session, cleanup_job_params)

    # Extract and transform platform images from imageManifests field (no HTTP calls needed)
    platform_images = transform_image_manifests(docker_images_raw, project_id)
    return platform_images
