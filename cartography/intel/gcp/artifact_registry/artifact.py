import logging
from collections import Counter
from dataclasses import dataclass
from functools import partial
from urllib.parse import unquote

import neo4j
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from google.cloud.artifactregistry_v1.types import Package

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.util import apply_conditional_labels
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import (
    DEFAULT_ARTIFACT_REGISTRY_WORKERS,
)
from cartography.intel.gcp.artifact_registry.util import (
    fetch_artifact_registry_resources,
)
from cartography.intel.gcp.artifact_registry.util import (
    list_artifact_registry_resources,
)
from cartography.intel.gcp.artifact_registry.util import load_matchlinks_with_progress
from cartography.intel.gcp.artifact_registry.util import (
    load_nodes_without_relationships,
)
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.artifact_registry.artifact import (
    GCPArtifactRegistryGenericArtifactSchema,
)
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryContainerImageSchema,
)
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryProjectToContainerImageRel,
)
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryRepositoryToContainerImageRel,
)
from cartography.models.gcp.artifact_registry.helm_chart import (
    GCPArtifactRegistryHelmChartSchema,
)
from cartography.models.gcp.artifact_registry.language_package import (
    GCPArtifactRegistryLanguagePackageSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepositoryArtifactFetchResult:
    repository_name: str
    repository_format: str
    artifacts: list[dict]
    cleanup_safe: bool


@dataclass(frozen=True)
class ArtifactRegistryArtifactSyncResult:
    platform_images: list[dict]
    docker_images_raw: list[dict]
    cleanup_safe: bool


def _extract_package_name(package: Package) -> str:
    package_data = proto_message_to_dict(package)
    raw_name = package_data.get("displayName") or package_data.get("name", "")
    return unquote(raw_name.split("/packages/")[-1]) if raw_name else ""


def _list_package_versions(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict]:
    artifacts: list[dict] = []
    packages = list_artifact_registry_resources(
        lambda: client.list_packages(parent=repository_name)
    )
    for package in packages:
        package_name = _extract_package_name(package)
        try:
            versions = list_artifact_registry_resources(
                lambda: client.list_versions(parent=package.name)
            )
        except NotFound:
            logger.debug(
                "Package versions not found for package %s. The package may have been deleted during sync.",
                package.name,
            )
            continue
        for version in versions:
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
            for image in list_artifact_registry_resources(
                lambda: client.list_docker_images(parent=repository_name)
            )
        ]
    except NotFound:
        logger.debug(
            "Docker images not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Could not retrieve Docker images for repository %s due to permissions or auth error. Skipping. (%s)",
            repository_name,
            type(e).__name__,
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
            for artifact in list_artifact_registry_resources(
                lambda: client.list_maven_artifacts(parent=repository_name)
            )
        ]
    except NotFound:
        logger.debug(
            "Maven artifacts not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Could not retrieve Maven artifacts for repository %s due to permissions or auth error. Skipping. (%s)",
            repository_name,
            type(e).__name__,
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
            for package in list_artifact_registry_resources(
                lambda: client.list_npm_packages(parent=repository_name)
            )
        ]
    except NotFound:
        logger.debug(
            "npm packages not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Could not retrieve npm packages for repository %s due to permissions or auth error. Skipping. (%s)",
            repository_name,
            type(e).__name__,
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
            for package in list_artifact_registry_resources(
                lambda: client.list_python_packages(parent=repository_name)
            )
        ]
    except NotFound:
        logger.debug(
            "Python packages not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Could not retrieve Python packages for repository %s due to permissions or auth error. Skipping. (%s)",
            repository_name,
            type(e).__name__,
        )
        return None


@timeit
def get_go_modules(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets Go modules for a repository.

    The Artifact Registry v1 API does not expose a ``goModules.list`` method;
    Go modules are enumerated via the generic ``packages``/``versions`` endpoints.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of Go module version dicts, each enriched with ``packageName``.
    """
    try:
        return _list_package_versions(client, repository_name)
    except NotFound:
        logger.debug(
            "Go modules not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get Go modules for repository %s due to permissions or auth error. (%s)",
            repository_name,
            type(e).__name__,
        )
        return None


@timeit
def get_apt_artifacts(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets APT package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of APT package-version dicts from the API.
    """
    try:
        return _list_package_versions(client, repository_name)
    except NotFound:
        logger.debug(
            "APT package versions not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get APT package versions for repository %s due to permissions or auth error. (%s)",
            repository_name,
            type(e).__name__,
        )
        return None


@timeit
def get_yum_artifacts(
    client: ArtifactRegistryClient,
    repository_name: str,
) -> list[dict] | None:
    """
    Gets YUM package versions for a repository.

    :param client: The Artifact Registry API client.
    :param repository_name: The full repository resource name.
    :return: List of YUM package-version dicts from the API.
    """
    try:
        return _list_package_versions(client, repository_name)
    except NotFound:
        logger.debug(
            "YUM package versions not found for repository %s. The repository may have been deleted during sync.",
            repository_name,
        )
        return []
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get YUM package versions for repository %s due to permissions or auth error. (%s)",
            repository_name,
            type(e).__name__,
        )
        return None


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


def _transform_generic_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
    format_label: str,
) -> list[dict]:
    transformed: list[dict] = []
    for artifact in artifacts_data:
        name = artifact.get("name", "")

        transformed.append(
            {
                "id": name,
                "name": name.split("/")[-1] if name else None,
                "format": format_label,
                "package_name": artifact.get("packageName"),
                "repository_id": repository_id,
                "project_id": project_id,
            }
        )
    return transformed


def transform_apt_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    return _transform_generic_artifacts(
        artifacts_data, repository_id, project_id, "APT"
    )


def transform_yum_artifacts(
    artifacts_data: list[dict],
    repository_id: str,
    project_id: str,
) -> list[dict]:
    return _transform_generic_artifacts(
        artifacts_data, repository_id, project_id, "YUM"
    )


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
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
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
    if not data:
        return

    schema = GCPArtifactRegistryContainerImageSchema()
    load_nodes_without_relationships(
        neo4j_session,
        schema,
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        apply_labels=False,
        progress_description=(
            f"Artifact Registry container image nodes for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    # Container image conditional labels are scoped through the project RESOURCE
    # relationship, so apply them once after nodes and that relationship exist.
    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryProjectToContainerImageRel(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            "Artifact Registry container image project RESOURCE relationships "
            f"for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )
    apply_conditional_labels(
        neo4j_session,
        schema,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )

    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryRepositoryToContainerImageRel(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            "Artifact Registry container image repository CONTAINS relationships "
            f"for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
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
    # The split write path attaches these relationships with MatchLinks, so
    # clean them explicitly after node cleanup has used the project RESOURCE
    # edge to scope stale node deletion.
    GraphJob.from_matchlink(
        GCPArtifactRegistryProjectToContainerImageRel(),
        "GCPProject",
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        GCPArtifactRegistryRepositoryToContainerImageRel(),
        "GCPProject",
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
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
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
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
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
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
    repository: tuple[str, str],
) -> RepositoryArtifactFetchResult:
    repo_name, repo_format = repository
    handlers = FORMAT_HANDLERS.get(repo_format)
    if handlers is None:
        logger.debug(
            "No artifact handler for format %s in repository %s",
            repo_format,
            repo_name,
        )
        return RepositoryArtifactFetchResult(repo_name, repo_format, [], True)

    get_func, _ = handlers
    artifacts = get_func(client, repo_name)
    if artifacts is None:
        return RepositoryArtifactFetchResult(repo_name, repo_format, [], False)
    return RepositoryArtifactFetchResult(repo_name, repo_format, artifacts, True)


@timeit
def sync_artifact_registry_artifacts(
    neo4j_session: neo4j.Session,
    client: ArtifactRegistryClient,
    repositories: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    cleanup_safe: bool = True,
    max_workers: int = DEFAULT_ARTIFACT_REGISTRY_WORKERS,
) -> ArtifactRegistryArtifactSyncResult:
    """
    Syncs GCP Artifact Registry artifacts for all repositories.

    :param neo4j_session: The Neo4j session.
    :param client: The Artifact Registry API client.
    :param repositories: List of raw repository data from the API.
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    :return: Artifact sync result containing platform images, raw docker images, and cleanup-safety state.
    """
    logger.info(f"Syncing Artifact Registry artifacts for project {project_id}.")

    docker_images_raw: list[dict] = []
    docker_images_transformed: list[dict] = []
    helm_charts_transformed: list[dict] = []
    language_packages_transformed: list[dict] = []
    other_artifacts_transformed: list[dict] = []
    candidate_repositories: list[tuple[str, str]] = []

    for repo in repositories:
        repo_name = repo.get("name")
        repo_format = repo.get("format")

        if not isinstance(repo_name, str) or not isinstance(repo_format, str):
            continue
        candidate_repositories.append((repo_name, repo_format))

    format_counts = Counter(repo_format for _, repo_format in candidate_repositories)
    logger.info(
        "Artifact Registry project %s has %d candidate repositories by format: %s",
        project_id,
        len(candidate_repositories),
        dict(sorted(format_counts.items())),
    )

    fetch_repository_artifacts = partial(_get_repository_artifacts, client)
    repository_results = fetch_artifact_registry_resources(
        items=candidate_repositories,
        fetch_for_item=fetch_repository_artifacts,
        resource_type="artifacts by repository",
        project_id=project_id,
        max_workers=max_workers,
    )

    artifact_cleanup_safe = cleanup_safe
    nonempty_repositories = 0
    for result in repository_results:
        artifact_cleanup_safe = artifact_cleanup_safe and result.cleanup_safe
        if not result.artifacts:
            continue

        nonempty_repositories += 1
        repo_name = result.repository_name
        repo_format = result.repository_format
        artifacts_raw = result.artifacts

        if repo_format == "DOCKER":
            helm_artifacts: list[dict] = []
            docker_artifacts: list[dict] = []
            for artifact in artifacts_raw:
                artifact_type = artifact.get("artifactType", "").lower()
                media_type = artifact.get("mediaType", "").lower()
                if (
                    HELM_MEDIA_TYPE_IDENTIFIER in artifact_type
                    or HELM_MEDIA_TYPE_IDENTIFIER in media_type
                ):
                    helm_artifacts.append(artifact)
                else:
                    docker_artifacts.append(artifact)
            docker_images_raw.extend(docker_artifacts)
            helm_charts_transformed.extend(
                transform_helm_charts(helm_artifacts, repo_name, project_id)
            )
            docker_images_transformed.extend(
                transform_docker_images(docker_artifacts, repo_name, project_id)
            )
        elif repo_format in LANGUAGE_PACKAGE_FORMATS:
            _, transform_func = FORMAT_HANDLERS[repo_format]
            language_packages_transformed.extend(
                transform_func(artifacts_raw, repo_name, project_id)
            )
        else:
            _, transform_func = FORMAT_HANDLERS[repo_format]
            other_artifacts_transformed.extend(
                transform_func(artifacts_raw, repo_name, project_id)
            )

    logger.info(
        "Collected Artifact Registry artifacts for project %s from %d/%d non-empty repositories: "
        "docker_images=%d, helm_charts=%d, language_packages=%d, generic_artifacts=%d.",
        project_id,
        nonempty_repositories,
        len(candidate_repositories),
        len(docker_images_transformed),
        len(helm_charts_transformed),
        len(language_packages_transformed),
        len(other_artifacts_transformed),
    )

    if docker_images_transformed:
        load_docker_images(
            neo4j_session, docker_images_transformed, project_id, update_tag
        )

    if helm_charts_transformed:
        load_helm_charts(neo4j_session, helm_charts_transformed, project_id, update_tag)

    if language_packages_transformed:
        load_language_packages(
            neo4j_session, language_packages_transformed, project_id, update_tag
        )

    if other_artifacts_transformed:
        load_generic_artifacts(
            neo4j_session, other_artifacts_transformed, project_id, update_tag
        )

    if artifact_cleanup_safe:
        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_docker_images(neo4j_session, cleanup_job_params)
        cleanup_helm_charts(neo4j_session, cleanup_job_params)
        cleanup_language_packages(neo4j_session, cleanup_job_params)
        cleanup_generic_artifacts(neo4j_session, cleanup_job_params)
    else:
        logger.warning(
            "Skipping Artifact Registry artifact cleanup for project %s because artifact discovery was incomplete.",
            project_id,
        )

    platform_images = transform_image_manifests(docker_images_raw, project_id)
    return ArtifactRegistryArtifactSyncResult(
        platform_images,
        docker_images_raw,
        artifact_cleanup_safe,
    )
