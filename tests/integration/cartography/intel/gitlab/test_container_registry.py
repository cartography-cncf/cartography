"""Integration tests for GitLab container registry module."""

from unittest.mock import patch

from cartography.intel.gitlab.container_image_attestations import (
    sync_container_image_attestations,
)
from cartography.intel.gitlab.container_images import sync_container_images
from cartography.intel.gitlab.container_repositories import sync_container_repositories
from cartography.intel.gitlab.container_repository_tags import (
    sync_container_repository_tags,
)
from tests.data.gitlab.container_registry import (
    GET_CONTAINER_IMAGE_ATTESTATIONS_RESPONSE,
)
from tests.data.gitlab.container_registry import GET_CONTAINER_IMAGES_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_MANIFEST_LISTS_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_REPOSITORIES_RESPONSE
from tests.data.gitlab.container_registry import GET_CONTAINER_REPOSITORY_TAGS_RESPONSE
from tests.data.gitlab.container_registry import TEST_GITLAB_URL
from tests.data.gitlab.container_registry import TEST_ORG_URL
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 12345


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
    "cartography.intel.gitlab.container_image_attestations.get_container_image_attestations",
    return_value=GET_CONTAINER_IMAGE_ATTESTATIONS_RESPONSE,
)
@patch(
    "cartography.intel.gitlab.container_images.get_container_images",
    return_value=(GET_CONTAINER_IMAGES_RESPONSE, GET_CONTAINER_MANIFEST_LISTS_RESPONSE),
)
@patch(
    "cartography.intel.gitlab.container_repository_tags.get_all_container_repository_tags",
    return_value=GET_CONTAINER_REPOSITORY_TAGS_RESPONSE,
)
@patch(
    "cartography.intel.gitlab.container_repositories.get_container_repositories",
    return_value=GET_CONTAINER_REPOSITORIES_RESPONSE,
)
def test_sync_container_registry(
    mock_get_repos,
    mock_get_tags,
    mock_get_images,
    mock_get_attestations,
    neo4j_session,
):
    """Test that all container registry nodes and relationships are created correctly."""
    # Clear database
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create test organization
    _create_test_org(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORGANIZATION_ID": TEST_ORG_ID,
        "org_url": TEST_ORG_URL,
    }

    # Run all sync functions in correct order
    # Note: images must be synced before tags since tags have REFERENCES relationship to images
    raw_repositories = sync_container_repositories(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_URL,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    raw_manifests, manifest_lists = sync_container_images(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_URL,
        raw_repositories,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_container_repository_tags(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_URL,
        raw_repositories,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_container_image_attestations(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_URL,
        raw_manifests,
        manifest_lists,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Verify container repository nodes
    expected_repos = {
        ("registry.gitlab.example.com/myorg/awesome-project/app", "app"),
        ("registry.gitlab.example.com/myorg/awesome-project/worker", "worker"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabContainerRepository", ["id", "name"])
        == expected_repos
    )

    # Verify container repository RESOURCE relationships
    expected_repo_rels = {
        (TEST_ORG_URL, "registry.gitlab.example.com/myorg/awesome-project/app"),
        (TEST_ORG_URL, "registry.gitlab.example.com/myorg/awesome-project/worker"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabContainerRepository",
            "id",
            "RESOURCE",
        )
        == expected_repo_rels
    )

    # Verify container image nodes
    expected_images = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "image",
        ),
        (
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
            "manifest_list",
        ),
        (
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
            "image",
        ),
        (
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
            "image",
        ),
        (
            "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
            "image",
        ),
    }
    assert (
        check_nodes(neo4j_session, "GitLabContainerImage", ["id", "type"])
        == expected_images
    )

    # Verify container image RESOURCE relationships
    expected_image_rels = {
        (
            TEST_ORG_URL,
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            TEST_ORG_URL,
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_URL,
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_URL,
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_URL,
            "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabContainerImage",
            "id",
            "RESOURCE",
        )
        == expected_image_rels
    )

    # Verify CONTAINS_IMAGE relationships (manifest list -> child images)
    expected_contains_rels = {
        (
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImage",
            "id",
            "GitLabContainerImage",
            "id",
            "CONTAINS_IMAGE",
        )
        == expected_contains_rels
    )

    # Verify container repository tag nodes
    expected_tags = {
        ("registry.gitlab.example.com/myorg/awesome-project/app:latest", "latest"),
        ("registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0", "v1.0.0"),
        ("registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0", "v0.9.0"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabContainerRepositoryTag", ["id", "name"])
        == expected_tags
    )

    # Verify tag RESOURCE relationships
    expected_tag_rels = {
        (TEST_ORG_URL, "registry.gitlab.example.com/myorg/awesome-project/app:latest"),
        (TEST_ORG_URL, "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0"),
        (
            TEST_ORG_URL,
            "registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabContainerRepositoryTag",
            "id",
            "RESOURCE",
        )
        == expected_tag_rels
    )

    # Verify HAS_TAG relationships (repository -> tag)
    expected_has_tag_rels = {
        (
            "registry.gitlab.example.com/myorg/awesome-project/app",
            "registry.gitlab.example.com/myorg/awesome-project/app:latest",
        ),
        (
            "registry.gitlab.example.com/myorg/awesome-project/app",
            "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0",
        ),
        (
            "registry.gitlab.example.com/myorg/awesome-project/worker",
            "registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerRepository",
            "id",
            "GitLabContainerRepositoryTag",
            "id",
            "HAS_TAG",
        )
        == expected_has_tag_rels
    )

    # Verify tag REFERENCES relationships (tag -> image)
    expected_references_rels = {
        (
            "registry.gitlab.example.com/myorg/awesome-project/app:latest",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0",
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            "registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0",
            "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerRepositoryTag",
            "id",
            "GitLabContainerImage",
            "id",
            "REFERENCES",
        )
        == expected_references_rels
    )

    # Verify attestation nodes
    expected_attestations = {
        (
            "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sig",
        ),
        (
            "sha256:att111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "att",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "GitLabContainerImageAttestation", ["id", "attestation_type"]
        )
        == expected_attestations
    )

    # Verify attestation RESOURCE relationships
    expected_attestation_rels = {
        (
            TEST_ORG_URL,
            "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            TEST_ORG_URL,
            "sha256:att111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabContainerImageAttestation",
            "id",
            "RESOURCE",
        )
        == expected_attestation_rels
    )

    # Verify ATTESTS relationships (attestation -> image)
    expected_attests_rels = {
        (
            "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "sha256:att111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImageAttestation",
            "id",
            "GitLabContainerImage",
            "id",
            "ATTESTS",
        )
        == expected_attests_rels
    )
