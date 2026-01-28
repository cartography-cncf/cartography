import json
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry import sync
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.trivy import sync_trivy_from_dir
from tests.data.gcp.artifact_registry import MOCK_DOCKER_IMAGES
from tests.data.gcp.artifact_registry import MOCK_PLATFORM_IMAGES
from tests.data.gcp.artifact_registry import MOCK_REPOSITORIES
from tests.data.trivy.trivy_gcp_sample import TRIVY_GCP_SAMPLE
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_gcp_image_relationships,
)

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"


def _create_test_project(neo4j_session):
    """Create test GCPProject node."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id: $project_id})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _mock_get_docker_images(client, repo_name):
    return MOCK_DOCKER_IMAGES


async def _mock_get_all_manifests_async(
    credentials, docker_artifacts_raw, max_concurrent=50
):
    """Mock async manifest getting to return platform images for multi-arch test."""
    return MOCK_PLATFORM_IMAGES


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GCP_SAMPLE),
)
@patch(
    "cartography.intel.trivy.get_json_files_in_dir",
    return_value={"/tmp/scan.json"},
)
@patch(
    "cartography.intel.gcp.artifact_registry.manifest.get_all_manifests_async",
    side_effect=_mock_get_all_manifests_async,
)
@patch(
    "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
    {
        "DOCKER": (_mock_get_docker_images, transform_docker_images),
    },
)
@patch(
    "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_repositories",
    return_value=MOCK_REPOSITORIES,
)
def test_sync_trivy_gcp(
    mock_get_repositories,
    mock_get_manifests,
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Ensure that Trivy scan results create relationships to GCPArtifactRegistryPlatformImage nodes
    for multi-arch images. The test uses:
    - ContainerImage with manifest list digest: sha256:abc123
    - PlatformImage with platform-specific digest: sha256:def456 (linux/amd64)
    - Trivy reports the platform-specific digest: sha256:def456
    - Relationships should be created to the PlatformImage, not ContainerImage
    """
    # Arrange - create GCP project
    _create_test_project(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # First sync GCP Artifact Registry container images and platform images
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

    # Act - sync Trivy results
    sync_trivy_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - verify GCP platform image relationships
    # Note: Trivy reports sha256:def456 (platform digest), not sha256:abc123 (manifest list digest)
    expected_package_rels = {
        (
            "3.0.15-1~deb12u1|openssl",
            "sha256:def456",  # Platform-specific digest
        ),
        (
            "7.88.1-10+deb12u5|curl",
            "sha256:def456",  # Platform-specific digest
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-77777",
            "sha256:def456",  # Platform-specific digest
        ),
        (
            "TIF|CVE-2024-66666",
            "sha256:def456",  # Platform-specific digest
        ),
    }

    assert_trivy_gcp_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )
