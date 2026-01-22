import json
from unittest.mock import mock_open
from unittest.mock import patch

import cartography.intel.gitlab.container_images
import cartography.intel.trivy
from cartography.intel.trivy import sync_trivy_from_dir
from tests.data.gitlab.container_registry import GET_CONTAINER_IMAGES_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_MANIFEST_LISTS_RESPONSE
from tests.data.gitlab.container_registry import TEST_ORG_URL
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_SAMPLE
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_gitlab_image_relationships,
)

TEST_UPDATE_TAG = 123456789


def _create_test_org(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (o:GitLabOrganization{id: $org_url})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $update_tag,
            o.name = 'myorg'
        """,
        org_url=TEST_ORG_URL,
        update_tag=TEST_UPDATE_TAG,
    )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GITLAB_SAMPLE),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan.json"},
)
@patch.object(
    cartography.intel.gitlab.container_images,
    "get_container_images",
    return_value=(GET_CONTAINER_IMAGES_RESPONSE, GET_CONTAINER_MANIFEST_LISTS_RESPONSE),
)
def test_sync_trivy_gitlab(
    mock_get_images,
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Ensure that Trivy scan results create relationships to GitLabContainerImage nodes.
    """
    # Arrange - create GitLab organization
    _create_test_org(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "org_url": TEST_ORG_URL,
    }

    # First sync GitLab container images
    cartography.intel.gitlab.container_images.sync_container_images(
        neo4j_session,
        "https://gitlab.example.com",
        "fake-token",
        TEST_ORG_URL,
        [],  # repositories - not used since we're mocking get_container_images
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

    # Assert - verify GitLab container image relationships
    expected_package_rels = {
        (
            "3.0.15-1~deb12u1|openssl",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "7.88.1-10+deb12u5|curl",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-99999",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "TIF|CVE-2024-88888",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }

    assert_trivy_gitlab_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )
