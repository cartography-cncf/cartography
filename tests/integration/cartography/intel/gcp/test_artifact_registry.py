from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry import sync
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.artifact import transform_maven_artifacts
from tests.data.gcp.artifact_registry import MOCK_DOCKER_IMAGES
from tests.data.gcp.artifact_registry import MOCK_HELM_CHARTS
from tests.data.gcp.artifact_registry import MOCK_MANIFEST_LIST
from tests.data.gcp.artifact_registry import MOCK_MAVEN_ARTIFACTS
from tests.data.gcp.artifact_registry import MOCK_REPOSITORIES
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
TEST_DOCKER_IMAGE_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123"
TEST_HELM_CHART_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-chart@sha256:xyz789"
TEST_MAVEN_ARTIFACT_ID = "projects/test-project/locations/us-central1/repositories/maven-repo/mavenArtifacts/com.example:my-lib:1.0.0"
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


async def _mock_get_all_manifests_async(
    credentials, docker_artifacts_raw, max_concurrent=50
):
    """Mock async manifest getting to return transformed manifests."""
    from cartography.intel.gcp.artifact_registry.manifest import transform_manifests

    # Find multi-arch images and transform their manifests
    all_manifests = []
    for artifact in docker_artifacts_raw:
        if artifact.get("mediaType") in {
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.oci.image.index.v1+json",
        }:
            artifact_name = artifact.get("name", "")
            project_id = "test-project"
            manifests = transform_manifests(
                MOCK_MANIFEST_LIST, artifact_name, project_id
            )
            all_manifests.extend(manifests)
    return all_manifests


@patch(
    "cartography.intel.gcp.artifact_registry.manifest.get_all_manifests_async",
    side_effect=_mock_get_all_manifests_async,
)
@patch(
    "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
    {
        "DOCKER": (_mock_get_docker_images, transform_docker_images),
        "MAVEN": (_mock_get_maven_artifacts, transform_maven_artifacts),
    },
)
@patch(
    "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_repositories",
    return_value=MOCK_REPOSITORIES,
)
def test_sync_artifact_registry(
    mock_get_repositories,
    mock_get_manifests,
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

    # Assert: Check repository nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryRepository", ["id"]) == {
        (TEST_DOCKER_REPO_ID,),
        (TEST_MAVEN_REPO_ID,),
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
