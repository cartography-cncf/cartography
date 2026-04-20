import logging
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote

import neo4j
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from google.cloud.artifactregistry_v1.types import Package

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import proto_message_to_dict
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

_DEFAULT_ARTIFACT_REGISTRY_REPOSITORY_WORKERS = 10


@timeit
def build_artifact_registry_client(
    credentials: GoogleCredentials,
) -> ArtifactRegistryClient:
    return ArtifactRegistryClient(credentials=credentials)


def _extract_package_name(package: Package) -> str:
    package_dict = proto_message_to_dict(package)
    raw_name = package_dict.get("displayName") or package_dict.get("name", "")
    return unquote(raw_name.split("/packages/")[-1]) if raw_name else ""


def _list_package_versions(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict]:
    artifacts: list[dict] = []
    for package in client.list_packages(parent=repository_name):
        package_name = _extract_package_name(package)
        for version in client.list_versions(parent=package.name):
            version_data = proto_message_to_dict(version)
            version_data["packageName"] = package_name
            artifacts.append(version_data)
    return artifacts


@timeit
def get_docker_images(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets Docker images for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Docker image dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises GoogleAPICallError: For errors other than permission denied.
    """
    try:
        return [
            proto_message_to_dict(image)
            for image in client.list_docker_images(parent=repository_name)
        ]
    except PermissionDenied:
        logger.warning(
            "Could not retrieve Docker images for repository %s due to permissions issues. Skipping.",
            repository_name,
        )
        return None


@timeit
def get_maven_artifacts(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets Maven artifacts for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Maven artifact dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises GoogleAPICallError: For errors other than permission denied.
    """
    try:
        return [
            proto_message_to_dict(artifact)
            for artifact in client.list_maven_artifacts(parent=repository_name)
        ]
    except PermissionDenied:
        logger.warning(
            "Could not retrieve Maven artifacts for repository %s due to permissions issues. Skipping.",
            repository_name,
        )
        return None


@timeit
def get_npm_packages(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets npm packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of npm package dicts from the API, or None if the Artifact Registry API
             is not enabled or access is denied.
    :raises GoogleAPICallError: For errors other than permission denied.
    """
    try:
        return [
            proto_message_to_dict(package)
            for package in client.list_npm_packages(parent=repository_name)
        ]
    except PermissionDenied:
        logger.warning(
            "Could not retrieve npm packages for repository %s due to permissions issues. Skipping.",
            repository_name,
        )
        return None


@timeit
def get_python_packages(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets Python packages for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Python package dicts from the API, or None if API is not enabled.
    :raises GoogleAPICallError: For errors other than permission denied.
    """
    try:
        return [
            proto_message_to_dict(package)
            for package in client.list_python_packages(parent=repository_name)
        ]
    except PermissionDenied:
        logger.warning(
            "Could not retrieve Python packages for repository %s due to permissions issues. Skipping.",
            repository_name,
        )
        return None


@timeit
def get_go_modules(client: ArtifactRegistryClient, repository_name: str) -> list[dict]:
    """
    Gets Go modules for a repository.

    The Artifact Registry v1 API does not expose a ``goModules.list`` method;
    Go modules are enumerated via the generic ``packages``/``versions`` endpoints.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Go module version dicts, each enriched with ``packageName``.
    """
    modules: list[dict] = []
    try:
        for version in _list_package_versions(client, repository_name):
            modules.append(
                {
                    "name": version.get("name"),
                    "version": version.get("name", "").split("/versions/")[-1],
                    "createTime": version.get("createTime"),
                    "updateTime": version.get("updateTime"),
                    "packageName": version.get("packageName"),
                }
            )
        return modules
    except (
        GoogleAPICallError,
        PermissionDenied,
        DefaultCredentialsError,
        RefreshError,
    ) as e:
        logger.warning(
            f"Failed to get Go modules for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_apt_artifacts(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict]:
    """
    Gets APT package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of APT package-version dicts from the API.
    """
    try:
        return _list_package_versions(client, repository_name)
    except (
        GoogleAPICallError,
        PermissionDenied,
        DefaultCredentialsError,
        RefreshError,
    ) as e:
        logger.warning(
            f"Failed to get APT package versions for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


@timeit
def get_yum_artifacts(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict]:
    """
    Gets YUM package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of YUM package-version dicts from the API.
    """
    try:
        return _list_package_versions(client, repository_name)
    except (
        GoogleAPICallError,
        PermissionDenied,
        DefaultCredentialsError,
        RefreshError,
    ) as e:
        logger.warning(
            f"Failed to get YUM package versions for repository {repository_name} "
            f"due to permissions or auth error: {e}",
        )
        return []


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
    Transforms Go module versions to the GCPArtifactRegistryLanguagePackage node format.

    Each input entry is a version resource (from ``packages.versions.list``)
    enriched with a ``packageName`` field identifying the parent module.
    """
    transformed: list[dict] = []
    for module in modules_data:
        name = module.get("name", "")
        version = name.split("/versions/")[-1] if "/versions/" in name else None

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": "GO",
                "uri": None,
                "version": version,
                "package_name": module.get("packageName"),
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
    "GO": (get_go_modules, transform_go_modules),
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


def _get_repository_artifacts(
    client: ArtifactRegistryClient,
    repo_name: str,
    repo_format: str,
) -> tuple[str, str, list[dict] | None]:
    handlers = FORMAT_HANDLERS.get(repo_format)
    if handlers is None:
        logger.debug(
            f"No artifact handler for format {repo_format} in repository {repo_name}"
        )
        return repo_name, repo_format, []

    get_func, _ = handlers
    return repo_name, repo_format, get_func(client, repo_name)


@timeit
def sync_artifact_registry_artifacts(
    neo4j_session: neo4j.Session,
    client: ArtifactRegistryClient,
    repositories: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    max_workers: int = _DEFAULT_ARTIFACT_REGISTRY_REPOSITORY_WORKERS,
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

    candidate_repositories: list[tuple[str, str]] = []
    for repo in repositories:
        repo_name = repo.get("name")
        repo_format = repo.get("format")
        if isinstance(repo_name, str) and isinstance(repo_format, str):
            candidate_repositories.append((repo_name, repo_format))

    if candidate_repositories:
        with ThreadPoolExecutor(
            max_workers=min(max_workers, len(candidate_repositories)),
        ) as executor:
            futures = {
                executor.submit(
                    _get_repository_artifacts,
                    client,
                    repo_name,
                    repo_format,
                ): (repo_name, repo_format)
                for repo_name, repo_format in candidate_repositories
            }
            for future in as_completed(futures):
                repo_name, repo_format, artifacts_raw = future.result()
                if artifacts_raw is None:
                    continue
                if not artifacts_raw:
                    continue

                handlers = FORMAT_HANDLERS.get(repo_format)
                if handlers is None:
                    continue

                if repo_format == "DOCKER":
                    for artifact in artifacts_raw:
                        artifact_type = artifact.get("artifactType", "")
                        media_type = artifact.get("mediaType", "")
                        if (
                            HELM_MEDIA_TYPE_IDENTIFIER in artifact_type.lower()
                            or HELM_MEDIA_TYPE_IDENTIFIER in media_type.lower()
                        ):
                            helm_charts_transformed.extend(
                                transform_helm_charts(
                                    [artifact],
                                    repo_name,
                                    project_id,
                                )
                            )
                        else:
                            docker_images_raw.append(artifact)
                            docker_images_transformed.extend(
                                transform_docker_images(
                                    [artifact],
                                    repo_name,
                                    project_id,
                                )
                            )
                elif repo_format in LANGUAGE_PACKAGE_FORMATS:
                    _, transform_func = handlers
                    language_packages_transformed.extend(
                        transform_func(artifacts_raw, repo_name, project_id)
                    )
                else:
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
