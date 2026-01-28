import json
from unittest.mock import mock_open
from unittest.mock import patch

import cartography.intel.gitlab.container_images
import cartography.intel.gitlab.container_repository_tags
import cartography.intel.trivy
from cartography.intel.trivy import sync_trivy_from_dir
from tests.data.gitlab.container_registry import GET_CONTAINER_IMAGES_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_MANIFEST_LISTS_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_REPOSITORY_TAGS_RESPONSE
from tests.data.gitlab.container_registry import TEST_ORG_URL
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_MULTI_REPO_DIGESTS
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_MULTIARCH_CHILD_AMD64
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_MULTIARCH_CHILD_ARM64
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_MULTIARCH_MANIFEST_LIST
from tests.data.trivy.trivy_gitlab_sample import TRIVY_GITLAB_SAMPLE
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_finding_extended_fields,
)
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_gitlab_image_relationships,
)
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_package_extended_fields,
)

TEST_UPDATE_TAG = 123456789


def _cleanup_trivy_data(neo4j_session):
    """Clean up all Trivy-related nodes before test runs."""
    neo4j_session.run("MATCH (n:TrivyImageFinding) DETACH DELETE n")
    neo4j_session.run("MATCH (n:Package) DETACH DELETE n")
    neo4j_session.run("MATCH (n:TrivyFix) DETACH DELETE n")


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
    cartography.intel.gitlab.container_repository_tags,
    "get_all_container_repository_tags",
    return_value=GET_CONTAINER_REPOSITORY_TAGS_RESPONSE,
)
@patch.object(
    cartography.intel.gitlab.container_images,
    "get_container_images",
    return_value=(GET_CONTAINER_IMAGES_RESPONSE, GET_CONTAINER_MANIFEST_LISTS_RESPONSE),
)
def test_sync_trivy_gitlab(
    mock_get_images,
    mock_get_tags,
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Ensure that Trivy scan results create relationships to GitLabContainerImage nodes.
    Tests both tag-based matching (RepoTags) and digest-based matching (RepoDigests).
    """
    # Arrange - clean up and create GitLab organization
    _cleanup_trivy_data(neo4j_session)
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

    # Sync GitLab container repository tags to enable tag-based matching
    cartography.intel.gitlab.container_repository_tags.sync_container_repository_tags(
        neo4j_session,
        "https://gitlab.example.com",
        "fake-token",
        TEST_ORG_URL,
        [],  # repositories - not used since we're mocking get_all_container_repository_tags
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

    # Assert extended fields are populated
    assert_trivy_finding_extended_fields(neo4j_session)
    assert_trivy_package_extended_fields(neo4j_session)


def _sync_gitlab_data(neo4j_session, update_tag=TEST_UPDATE_TAG):
    """Helper to sync GitLab container images and tags for tests."""
    _cleanup_trivy_data(neo4j_session)
    _create_test_org(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "org_url": TEST_ORG_URL,
    }

    # Sync GitLab container images
    with patch.object(
        cartography.intel.gitlab.container_images,
        "get_container_images",
        return_value=(
            GET_CONTAINER_IMAGES_RESPONSE,
            GET_CONTAINER_MANIFEST_LISTS_RESPONSE,
        ),
    ):
        cartography.intel.gitlab.container_images.sync_container_images(
            neo4j_session,
            "https://gitlab.example.com",
            "fake-token",
            TEST_ORG_URL,
            [],
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Sync GitLab container repository tags
    with patch.object(
        cartography.intel.gitlab.container_repository_tags,
        "get_all_container_repository_tags",
        return_value=GET_CONTAINER_REPOSITORY_TAGS_RESPONSE,
    ):
        cartography.intel.gitlab.container_repository_tags.sync_container_repository_tags(
            neo4j_session,
            "https://gitlab.example.com",
            "fake-token",
            TEST_ORG_URL,
            [],
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    return common_job_parameters


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GITLAB_MULTIARCH_MANIFEST_LIST),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan-manifest-list.json"},
)
def test_sync_trivy_gitlab_multiarch_manifest_list(
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Test Trivy scan of a multi-arch manifest list.

    Verifies that findings link to the manifest_list type image node,
    not to the platform-specific children.
    """
    common_job_parameters = _sync_gitlab_data(neo4j_session)

    # Act - sync Trivy results for manifest list
    sync_trivy_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - verify findings link to manifest list digest
    expected_package_rels = {
        (
            "3.7.9-2+deb12u3|libgnutls30",
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-77777",
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    assert_trivy_gitlab_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )

    # Verify the image node is of type manifest_list
    result = neo4j_session.run(
        """
        MATCH (img:GitLabContainerImage {digest: $digest})
        RETURN img.type AS type
        """,
        digest="sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
    ).single()
    assert result is not None
    assert result["type"] == "manifest_list"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GITLAB_MULTIARCH_CHILD_AMD64),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan-amd64.json"},
)
def test_sync_trivy_gitlab_multiarch_child_amd64(
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Test Trivy scan of a platform-specific child image (linux/amd64).

    Verifies that findings link to the child image digest,
    and that the child is correctly related to its parent manifest list.
    """
    common_job_parameters = _sync_gitlab_data(neo4j_session)

    # Act - sync Trivy results for amd64 child
    sync_trivy_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - verify findings link to amd64 child digest
    expected_package_rels = {
        (
            "1:1.2.13.dfsg-1|zlib1g",
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-66666",
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    assert_trivy_gitlab_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )

    # Verify the child image is linked to parent manifest list
    result = neo4j_session.run(
        """
        MATCH (parent:GitLabContainerImage {type: 'manifest_list'})
              -[:CONTAINS_IMAGE]->(child:GitLabContainerImage {digest: $child_digest})
        RETURN parent.digest AS parent_digest, child.architecture AS arch
        """,
        child_digest="sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
    ).single()
    assert result is not None
    assert (
        result["parent_digest"]
        == "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444"
    )
    assert result["arch"] == "amd64"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GITLAB_MULTIARCH_CHILD_ARM64),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan-arm64.json"},
)
def test_sync_trivy_gitlab_multiarch_child_arm64(
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Test Trivy scan of a platform-specific child image (linux/arm64).

    Verifies that findings link to the arm64 child image digest,
    demonstrating platform-specific vulnerability tracking.
    """
    common_job_parameters = _sync_gitlab_data(neo4j_session)

    # Act - sync Trivy results for arm64 child
    sync_trivy_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - verify findings link to arm64 child digest
    expected_package_rels = {
        (
            "2.36-9+deb12u4|libc6",
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-55555",
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }

    assert_trivy_gitlab_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )

    # Verify the child image has correct architecture and variant
    result = neo4j_session.run(
        """
        MATCH (child:GitLabContainerImage {digest: $child_digest})
        RETURN child.architecture AS arch, child.variant AS variant
        """,
        child_digest="sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
    ).single()
    assert result is not None
    assert result["arch"] == "arm64"
    assert result["variant"] == "v8"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_GITLAB_MULTI_REPO_DIGESTS),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan-multi-digests.json"},
)
def test_sync_trivy_gitlab_multi_repo_digests(
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Test Trivy scan with multiple RepoDigests entries.

    Verifies that the first RepoDigests entry is selected for digest extraction,
    ensuring consistent behavior when images are pushed to multiple registries.
    """
    common_job_parameters = _sync_gitlab_data(neo4j_session)

    # Act - sync Trivy results with multiple RepoDigests
    sync_trivy_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - verify findings link to the image using first RepoDigests entry
    expected_package_rels = {
        (
            "5.2.15-2+b2|bash",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }

    expected_finding_rels = {
        (
            "TIF|CVE-2024-44444",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }

    assert_trivy_gitlab_image_relationships(
        neo4j_session,
        expected_package_rels,
        expected_finding_rels,
    )
