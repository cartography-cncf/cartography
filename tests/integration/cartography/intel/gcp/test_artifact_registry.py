from typing import Any
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry import sync
from cartography.intel.gcp.artifact_registry.artifact import transform_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.artifact import transform_maven_artifacts
from cartography.intel.gcp.artifact_registry.artifact import transform_yum_artifacts
from cartography.intel.gcp.artifact_registry.repository import (
    ArtifactRegistryRepositorySyncResult,
)
from tests.data.gcp.artifact_registry import MOCK_APT_ARTIFACTS
from tests.data.gcp.artifact_registry import MOCK_DOCKER_IMAGES
from tests.data.gcp.artifact_registry import MOCK_HELM_CHARTS
from tests.data.gcp.artifact_registry import MOCK_MAVEN_ARTIFACTS
from tests.data.gcp.artifact_registry import MOCK_REPOSITORIES
from tests.data.gcp.artifact_registry import MOCK_YUM_ARTIFACTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_DOCKER_REPO_ID = (
    "projects/test-project/locations/us-central1/repositories/docker-repo"
)
TEST_MAVEN_REPO_ID = (
    "projects/test-project/locations/us-central1/repositories/maven-repo"
)
TEST_APT_REPO_ID = "projects/test-project/locations/us-east1/repositories/apt-repo"
TEST_YUM_REPO_ID = "projects/test-project/locations/us-east1/repositories/yum-repo"
TEST_DOCKER_IMAGE_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123"
TEST_HELM_CHART_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-chart@sha256:xyz789"
TEST_MAVEN_ARTIFACT_ID = "projects/test-project/locations/us-central1/repositories/maven-repo/mavenArtifacts/com.example:my-lib:1.0.0"
TEST_APT_ARTIFACT_ID = "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl/versions/7.88.1"
TEST_YUM_ARTIFACT_ID = "projects/test-project/locations/us-east1/repositories/yum-repo/packages/bash/versions/5.2.26"
TEST_PLATFORM_IMAGE_AMD64_ID = f"{TEST_DOCKER_IMAGE_ID}@sha256:def456"
TEST_PLATFORM_IMAGE_ARM64_ID = f"{TEST_DOCKER_IMAGE_ID}@sha256:ghi789"


def _create_prerequisite_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


def _mock_get_docker_images(client, repo_name):
    return MOCK_DOCKER_IMAGES + MOCK_HELM_CHARTS


def _mock_get_maven_artifacts(client, repo_name):
    return MOCK_MAVEN_ARTIFACTS


def _mock_get_apt_artifacts(client, repo_name):
    return MOCK_APT_ARTIFACTS


def _mock_get_yum_artifacts(client, repo_name):
    return MOCK_YUM_ARTIFACTS


@patch(
    "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
    {
        "DOCKER": (_mock_get_docker_images, transform_docker_images),
        "MAVEN": (_mock_get_maven_artifacts, transform_maven_artifacts),
        "APT": (_mock_get_apt_artifacts, transform_apt_artifacts),
        "YUM": (_mock_get_yum_artifacts, transform_yum_artifacts),
    },
)
@patch(
    "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_repositories",
    return_value=ArtifactRegistryRepositorySyncResult(
        cast(list[dict[str, Any]], MOCK_REPOSITORIES),
        True,
    ),
)
@patch(
    "cartography.intel.gcp.artifact_registry.build_artifact_registry_client",
    return_value=MagicMock(name="artifact-registry-client"),
)
def test_sync_artifact_registry(
    mock_build_artifact_registry_client,
    mock_get_repositories,
    neo4j_session,
):
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_client = MagicMock()
    mock_credentials = MagicMock()

    sync(
        neo4j_session,
        mock_client,
        mock_credentials,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    mock_build_artifact_registry_client.assert_called_once_with(
        credentials=mock_credentials,
    )

    # Assert: Check repository nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryRepository", ["id"]) == {
        (TEST_DOCKER_REPO_ID,),
        (TEST_MAVEN_REPO_ID,),
        (TEST_APT_REPO_ID,),
        (TEST_YUM_REPO_ID,),
    }

    # Assert: Check container image nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryContainerImage", ["id"]) == {
        (TEST_DOCKER_IMAGE_ID,),
    }

    # Assert: Check Helm chart nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryHelmChart", ["id"]) == {
        (TEST_HELM_CHART_ID,),
    }

    # Assert: Check language package nodes (Maven artifact)
    assert check_nodes(neo4j_session, "GCPArtifactRegistryLanguagePackage", ["id"]) == {
        (TEST_MAVEN_ARTIFACT_ID,),
    }

    # Assert: Check generic artifact nodes (APT and YUM artifacts)
    assert check_nodes(neo4j_session, "GCPArtifactRegistryGenericArtifact", ["id"]) == {
        (TEST_APT_ARTIFACT_ID,),
        (TEST_YUM_ARTIFACT_ID,),
    }

    # Assert: Check platform image nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryPlatformImage", ["id"]) == {
        (TEST_PLATFORM_IMAGE_AMD64_ID,),
        (TEST_PLATFORM_IMAGE_ARM64_ID,),
    }

    # Assert: Check GCPProject -> GCPArtifactRegistryRepository relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryRepository",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, TEST_DOCKER_REPO_ID),
        (TEST_PROJECT_ID, TEST_MAVEN_REPO_ID),
        (TEST_PROJECT_ID, TEST_APT_REPO_ID),
        (TEST_PROJECT_ID, TEST_YUM_REPO_ID),
    }

    # Assert: Check GCPProject -> GCPArtifactRegistryContainerImage relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryContainerImage",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_DOCKER_IMAGE_ID)}

    # Assert: Check GCPProject -> GCPArtifactRegistryHelmChart relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryHelmChart",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_HELM_CHART_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryContainerImage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryContainerImage",
        "id",
        "CONTAINS",
    ) == {(TEST_DOCKER_REPO_ID, TEST_DOCKER_IMAGE_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryHelmChart relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryHelmChart",
        "id",
        "CONTAINS",
    ) == {(TEST_DOCKER_REPO_ID, TEST_HELM_CHART_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryLanguagePackage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryLanguagePackage",
        "id",
        "CONTAINS",
    ) == {(TEST_MAVEN_REPO_ID, TEST_MAVEN_ARTIFACT_ID)}

    # Assert: Check GCPProject -> GCPArtifactRegistryGenericArtifact relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryGenericArtifact",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, TEST_APT_ARTIFACT_ID),
        (TEST_PROJECT_ID, TEST_YUM_ARTIFACT_ID),
    }

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryGenericArtifact relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryGenericArtifact",
        "id",
        "CONTAINS",
    ) == {
        (TEST_APT_REPO_ID, TEST_APT_ARTIFACT_ID),
        (TEST_YUM_REPO_ID, TEST_YUM_ARTIFACT_ID),
    }

    # Assert: Check GCPArtifactRegistryContainerImage -> GCPArtifactRegistryPlatformImage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryContainerImage",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "id",
        "HAS_MANIFEST",
    ) == {
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_AMD64_ID),
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_ARM64_ID),
    }
