"""Integration tests for GitLab container registry module."""

import base64
import json
from unittest.mock import patch

from cartography.intel.gitlab.container_image_attestations import (
    AttestationDiscoverySummary,
)
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
TEST_ATTESTATION_BLOB = {
    "payload": base64.b64encode(
        json.dumps(
            {
                "predicate": {
                    "materials": [
                        {
                            "uri": "pkg:docker/registry.gitlab.example.com/base-images/python@3.12",
                            "digest": {
                                "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
                            },
                        },
                    ],
                    "metadata": {
                        "https://mobyproject.org/buildkit@v1#metadata": {
                            "vcs": {
                                "source": "https://gitlab.example.com/myorg/awesome-project.git",
                                "revision": "deadbeefcafebabe",
                                "localdir:dockerfile": "docker",
                            },
                        },
                    },
                    "buildDefinition": {
                        "externalParameters": {
                            "configSource": {
                                "path": "Dockerfile",
                            },
                        },
                    },
                },
            }
        ).encode("utf-8")
    ).decode("utf-8"),
}


def _create_test_org(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (o:GitLabOrganization{id: $org_id})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $update_tag,
            o.name = 'myorg',
            o.web_url = $org_url,
            o.gitlab_url = $gitlab_url
        """,
        org_id=TEST_ORG_ID,
        org_url=TEST_ORG_URL,
        gitlab_url=TEST_GITLAB_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _create_test_parent_image(neo4j_session):
    """Create a base image node so BUILT_FROM can resolve."""
    neo4j_session.run(
        """
        MERGE (img:GitLabContainerImage {id: $digest})
        ON CREATE SET img.firstseen = timestamp()
        SET img.digest = $digest,
            img.type = 'image',
            img.lastupdated = $update_tag
        """,
        digest="sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        update_tag=TEST_UPDATE_TAG,
    )


@patch(
    "cartography.intel.gitlab.container_image_attestations.get_container_image_attestations",
    return_value=(
        GET_CONTAINER_IMAGE_ATTESTATIONS_RESPONSE,
        AttestationDiscoverySummary(
            attempted=2,
            discovered=len(GET_CONTAINER_IMAGE_ATTESTATIONS_RESPONSE),
            failed=0,
        ),
    ),
)
@patch(
    "cartography.intel.gitlab.container_images.get_container_images",
    return_value=(GET_CONTAINER_IMAGES_RESPONSE, GET_CONTAINER_MANIFEST_LISTS_RESPONSE),
)
@patch(
    "cartography.intel.gitlab.container_image_attestations.fetch_registry_blob",
    return_value=TEST_ATTESTATION_BLOB,
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
    mock_fetch_registry_blob,
    mock_get_images,
    mock_get_attestations,
    neo4j_session,
):
    """Test that all container registry nodes and relationships are created correctly."""
    # Clear database
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create test organization
    _create_test_org(neo4j_session)
    _create_test_parent_image(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORGANIZATION_ID": TEST_ORG_ID,
        "org_id": TEST_ORG_ID,
        "gitlab_url": TEST_GITLAB_URL,
    }

    # Run all sync functions in correct order
    # Note: images must be synced before tags since tags have REFERENCES relationship to images
    raw_repositories = sync_container_repositories(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_ID,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    raw_manifests, manifest_lists = sync_container_images(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_ID,
        raw_repositories,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_container_repository_tags(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_ID,
        raw_repositories,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_container_image_attestations(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_ORG_ID,
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
        (TEST_ORG_ID, "registry.gitlab.example.com/myorg/awesome-project/app"),
        (TEST_ORG_ID, "registry.gitlab.example.com/myorg/awesome-project/worker"),
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
        >= expected_images
    )

    # Verify container image RESOURCE relationships
    expected_image_rels = {
        (
            TEST_ORG_ID,
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            TEST_ORG_ID,
            "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_ID,
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_ID,
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
        (
            TEST_ORG_ID,
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
        (TEST_ORG_ID, "registry.gitlab.example.com/myorg/awesome-project/app:latest"),
        (TEST_ORG_ID, "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0"),
        (
            TEST_ORG_ID,
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

    # Verify generic REPO_IMAGE relationships (repository -> tag)
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerRepository",
            "id",
            "GitLabContainerRepositoryTag",
            "id",
            "REPO_IMAGE",
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

    # Verify generic IMAGE relationships (tag -> image)
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerRepositoryTag",
            "id",
            "GitLabContainerImage",
            "id",
            "IMAGE",
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
            TEST_ORG_ID,
            "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            TEST_ORG_ID,
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

    # Verify container image layer nodes
    # Note: First image has 3 layers forming a chain, others have empty arrays
    expected_layers = {
        ("sha256:diff1111222333444555666777888999000aaabbbcccdddeeefff000111222",),
        ("sha256:diff2222333444555666777888999000aaabbbcccdddeeefff000111222333",),
        ("sha256:diff3333444555666777888999000aaabbbcccdddeeefff000111222333444",),
    }
    assert (
        check_nodes(neo4j_session, "GitLabContainerImageLayer", ["id"])
        == expected_layers
    )

    # Verify layer RESOURCE relationships
    expected_layer_rels = {
        (
            TEST_ORG_ID,
            "sha256:diff1111222333444555666777888999000aaabbbcccdddeeefff000111222",
        ),
        (
            TEST_ORG_ID,
            "sha256:diff2222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            TEST_ORG_ID,
            "sha256:diff3333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabContainerImageLayer",
            "id",
            "RESOURCE",
        )
        == expected_layer_rels
    )

    # Verify HAS_LAYER relationships (image -> layer)
    # Only the first image has layers in the mock data (3 layers)
    expected_has_layer_rels = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff1111222333444555666777888999000aaabbbcccdddeeefff000111222",
        ),
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff2222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff3333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImage",
            "id",
            "GitLabContainerImageLayer",
            "id",
            "HAS_LAYER",
        )
        == expected_has_layer_rels
    )

    # Verify NEXT relationships (layer chain: layer1 -> layer2 -> layer3)
    expected_next_rels = {
        (
            "sha256:diff1111222333444555666777888999000aaabbbcccdddeeefff000111222",
            "sha256:diff2222333444555666777888999000aaabbbcccdddeeefff000111222333",
        ),
        (
            "sha256:diff2222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff3333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImageLayer",
            "id",
            "GitLabContainerImageLayer",
            "id",
            "NEXT",
        )
        == expected_next_rels
    )

    # Verify HEAD relationship (image -> first layer)
    expected_head_rels = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff1111222333444555666777888999000aaabbbcccdddeeefff000111222",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImage",
            "id",
            "GitLabContainerImageLayer",
            "id",
            "HEAD",
        )
        == expected_head_rels
    )

    # Verify TAIL relationship (image -> last layer)
    expected_tail_rels = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:diff3333444555666777888999000aaabbbcccdddeeefff000111222333444",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImage",
            "id",
            "GitLabContainerImageLayer",
            "id",
            "TAIL",
        )
        == expected_tail_rels
    )

    # Verify provenance was loaded onto the image node
    expected_provenance = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "https://gitlab.example.com/myorg/awesome-project",
            "docker/Dockerfile",
            "pkg:docker/registry.gitlab.example.com/base-images/python@3.12",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabContainerImage",
            ["id", "source_uri", "source_file", "parent_image_uri"],
        )
        >= expected_provenance
    )

    expected_built_from_rels = {
        (
            "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabContainerImage",
            "id",
            "GitLabContainerImage",
            "id",
            "BUILT_FROM",
        )
        >= expected_built_from_rels
    )
