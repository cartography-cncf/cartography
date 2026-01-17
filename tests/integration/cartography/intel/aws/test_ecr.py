import datetime
import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr
import tests.data.aws.ecr
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session):
    repo_data = tests.data.aws.ecr.DESCRIBE_REPOSITORIES
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data["repositories"],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=tests.data.aws.ecr.DESCRIBE_REPOSITORIES["repositories"],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    side_effect=[
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
        ],
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository"
        ],
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository"
        ],
    ],
)
def test_sync_ecr(mock_get_images, mock_get_repos, neo4j_session):
    """
    Ensure that ECR repositories and images are properly synced and connected
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert ECR repositories exist
    assert check_nodes(neo4j_session, "ECRRepository", ["id", "name"]) == {
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "example-repository",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
            "sample-repository",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
            "test-repository",
        ),
    }

    # Assert ECR images exist (excluding those without digests)
    assert check_nodes(neo4j_session, "ECRImage", ["id", "digest"]) == {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000001",
            "sha256:0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000011",
            "sha256:0000000000000000000000000000000000000000000000000000000000000011",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000021",
            "sha256:0000000000000000000000000000000000000000000000000000000000000021",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000031",
            "sha256:0000000000000000000000000000000000000000000000000000000000000031",
        ),
    }

    # Assert ECR repository images exist
    assert check_nodes(
        neo4j_session,
        "ECRRepositoryImage",
        ["id", "tag", "image_size_bytes", "image_pushed_at"],
    ) == {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "1",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
            "latest",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:2",
            "2",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:1",
            "1",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:2",
            "2",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1234567890",
            "1234567890",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1",
            "1",
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            None,
            1024,
            "2025-01-01T00:00:00.000000-00:00",
        ),
    }

    # Assert repository to AWS account relationship
    assert check_rels(
        neo4j_session,
        "ECRRepository",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "000000000000",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
            "000000000000",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
            "000000000000",
        ),
    }

    # Assert repository to repository image relationship
    assert check_rels(
        neo4j_session,
        "ECRRepository",
        "uri",
        "ECRRepositoryImage",
        "id",
        "REPO_IMAGE",
        rel_direction_right=True,
    ) == {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:2",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:1",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:2",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1234567890",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
        ),
    }

    # Assert repository image to image relationship
    assert check_rels(
        neo4j_session,
        "ECRRepositoryImage",
        "id",
        "ECRImage",
        "id",
        "IMAGE",
        rel_direction_right=True,
    ) == {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:2",
            "sha256:0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:2",
            "sha256:0000000000000000000000000000000000000000000000000000000000000011",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1234567890",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000021",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            "sha256:0000000000000000000000000000000000000000000000000000000000000031",
        ),
    }

    # Clean up the database after the test
    neo4j_session.run("MATCH (n) detach delete n")


def test_load_ecr_repositories(neo4j_session):
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    expected_nodes = {
        "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ECRRepository) RETURN r.arn;
        """,
    )
    actual_nodes = {n["r.arn"] for n in nodes}
    assert actual_nodes == expected_nodes


def test_cleanup_repositories(neo4j_session):
    """
    Ensure that after the cleanup job runs, all ECRRepository nodes
    with a different UPDATE_TAG are removed from the AWSAccount node.
    We load 100 additional nodes, because the cleanup job is configured
    to run iteratively, processing 100 nodes at a time. So this test also ensures
    that iterative cleanups do work.
    """
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    repo_data = {**tests.data.aws.ecr.DESCRIBE_REPOSITORIES}
    # add additional repository noes, for a total of 103, since
    cleanup_jobs = json.load(
        open("./cartography/data/jobs/cleanup/aws_import_ecr_cleanup.json"),
    )
    iter_size = cleanup_jobs["statements"][-1]["iterationsize"]
    repo_data["repositories"].extend(
        [
            {
                "repositoryArn": f"arn:aws:ecr:us-east-1:000000000000:repository/test-repository{i}",
                "registryId": "000000000000",
                "repositoryName": f"test-repository{i}",
                "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
                "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
            }
            for i in range(iter_size)
        ],
    )

    # Act
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data["repositories"],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    common_job_params = {
        "AWS_ID": TEST_ACCOUNT_ID,
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }
    nodes = neo4j_session.run(
        f"""
        MATCH (a:AWSAccount{{id:'{TEST_ACCOUNT_ID}'}})--(repo:ECRRepository)
        RETURN count(repo)
        """,
    )
    # there should be 103 nodes
    expected_nodes = {
        len(repo_data["repositories"]),
    }
    actual_nodes = {(n["count(repo)"]) for n in nodes}
    # Assert
    assert expected_nodes == actual_nodes

    # Arrange
    additional_repo_data = {
        "repositories": [
            {
                "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/test-repositoryX",
                "registryId": "000000000000",
                "repositoryName": "test-repositoryX",
                "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
                "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
            },
        ],
    }
    additional_update_tag = 2
    common_job_params["UPDATE_TAG"] = additional_update_tag
    # Act
    # load an additional node with a different update_tag
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        additional_repo_data["repositories"],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        additional_update_tag,
    )
    # run the cleanup job
    cartography.intel.aws.ecr.cleanup(neo4j_session, common_job_params)
    nodes = neo4j_session.run(
        f"""
        MATCH (a:AWSAccount{{id:'{TEST_ACCOUNT_ID}'}})--(repo:ECRRepository)
        RETURN repo.arn, repo.lastupdated
        """,
    )
    actual_nodes = {(n["repo.arn"], n["repo.lastupdated"]) for n in nodes}
    # there should be just one remaining node with the new update_tag
    expected_nodes = {
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/test-repositoryX",
            additional_update_tag,
        ),
    }

    # Assert
    assert expected_nodes == actual_nodes


def test_load_ecr_repository_images(neo4j_session):
    """
    Ensure the connection (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage) exists.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list, ecr_images_list = (
        cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    )
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        ecr_images_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo ARN, image tag)
    expected_nodes = {
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "1",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "latest",
        ),
        (
            "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "2",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo:ECRRepository{id:"arn:aws:ecr:us-east-1:000000000000:repository/example-repository"})
        -[:REPO_IMAGE]->(image:ECRRepositoryImage)
        RETURN repo.arn, image.tag;
        """,
    )
    actual_nodes = {(n["repo.arn"], n["image.tag"]) for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_ecr_images(neo4j_session):
    """
    Ensure the connection (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage) exists.
    A single ECRImage may be referenced by many ECRRepositoryImages.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list, ecr_images_list = (
        cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    )
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        ecr_images_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo image ARN, image SHA)
    expected_nodes = {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository:1234567890",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo_image:ECRRepositoryImage)-[:IMAGE]->
        (image:ECRImage{digest:"sha256:0000000000000000000000000000000000000000000000000000000000000000"})
        RETURN repo_image.id, image.digest;
        """,
    )
    actual_nodes = {(n["repo_image.id"], n["image.digest"]) for n in nodes}
    assert actual_nodes == expected_nodes


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=[
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/multi-arch-repository",
            "registryId": "000000000000",
            "repositoryName": "multi-arch-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository",
            "createdAt": datetime.datetime(2025, 1, 1, 0, 0, 1),
        }
    ],
)
def test_sync_manifest_list(mock_get_repos, neo4j_session):
    """
    Ensure that manifest lists are properly handled:
    - ECRRepositoryImage points to manifest list, platform-specific, and attestation ECRImages
    - ECRImage nodes have correct type, architecture, os, variant fields
    - Attestations are included as type="attestation"
    """

    # Remove everything previously put in the test graph since the fixture scope is set to module and not function.
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n;
        """,
    )
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mock_client = MagicMock()

    # Mock list_images paginator
    mock_list_paginator = MagicMock()
    mock_list_paginator.paginate.return_value = [
        {
            "imageIds": [
                {
                    "imageDigest": tests.data.aws.ecr.MANIFEST_LIST_DIGEST,
                    "imageTag": "v1.0",
                }
            ]
        }
    ]

    # Mock describe_images paginator
    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [tests.data.aws.ecr.MULTI_ARCH_IMAGE_DETAILS]}
    ]

    # Configure get_paginator to return the appropriate paginator
    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        elif name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator

    # Mock batch_get_image to return the manifest list
    mock_client.batch_get_image.return_value = (
        tests.data.aws.ecr.BATCH_GET_MANIFEST_LIST_RESPONSE
    )

    boto3_session.client.return_value = mock_client

    # Act
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Check that 4 ECRImage nodes were created (manifest list + 2 platform-specific + 1 attestation for the AMD64 image)
    ecr_images = neo4j_session.run(
        """
        MATCH (img:ECRImage)
        RETURN img.digest AS digest, img.type AS type, img.architecture AS architecture,
               img.os AS os, img.variant AS variant, img.attestation_type AS attestation_type,
               img.attests_digest AS attests_digest, img.media_type AS media_type,
               img.artifact_media_type AS artifact_media_type
        ORDER BY img.digest
        """
    ).data()

    assert len(ecr_images) == 4

    # Manifest list image
    manifest_list_img = next(
        img
        for img in ecr_images
        if img["digest"] == tests.data.aws.ecr.MANIFEST_LIST_DIGEST
    )
    assert manifest_list_img["type"] == "manifest_list"
    assert manifest_list_img["architecture"] is None
    assert manifest_list_img["os"] is None
    assert manifest_list_img["variant"] is None

    # AMD64 platform image
    amd64_img = next(
        img
        for img in ecr_images
        if img["digest"] == tests.data.aws.ecr.MANIFEST_LIST_AMD64_DIGEST
    )
    assert amd64_img["type"] == "image"
    assert amd64_img["architecture"] == "amd64"
    assert amd64_img["os"] == "linux"
    assert amd64_img["variant"] is None
    assert amd64_img["media_type"] == "application/vnd.oci.image.manifest.v1+json"

    # ARM64 platform image
    arm64_img = next(
        img
        for img in ecr_images
        if img["digest"] == tests.data.aws.ecr.MANIFEST_LIST_ARM64_DIGEST
    )
    assert arm64_img["type"] == "image"
    assert arm64_img["architecture"] == "arm64"
    assert arm64_img["os"] == "linux"
    assert arm64_img["variant"] == "v8"
    assert arm64_img["media_type"] == "application/vnd.oci.image.manifest.v1+json"

    # Attestation image
    attestation_img = next(
        img
        for img in ecr_images
        if img["digest"] == tests.data.aws.ecr.MANIFEST_LIST_ATTESTATION_DIGEST
    )
    assert attestation_img["type"] == "attestation"
    assert attestation_img["architecture"] == "unknown"
    assert attestation_img["os"] == "unknown"
    assert attestation_img["variant"] is None
    assert attestation_img["attestation_type"] == "attestation-manifest"
    assert (
        attestation_img["attests_digest"]
        == tests.data.aws.ecr.MANIFEST_LIST_AMD64_DIGEST
    )
    assert attestation_img["media_type"] == "application/vnd.oci.image.manifest.v1+json"

    # Assert - Check that ECRRepositoryImage has relationships to all 4 images
    all_rels = check_rels(
        neo4j_session,
        "ECRRepositoryImage",
        "id",
        "ECRImage",
        "digest",
        "IMAGE",
        rel_direction_right=True,
    )

    # Filter to only relationships from our specific repository image
    repo_image_id = (
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository:v1.0"
    )
    image_digests = {
        img_digest for (repo_id, img_digest) in all_rels if repo_id == repo_image_id
    }

    assert len(image_digests) == 4
    assert image_digests == {
        tests.data.aws.ecr.MANIFEST_LIST_DIGEST,
        tests.data.aws.ecr.MANIFEST_LIST_AMD64_DIGEST,
        tests.data.aws.ecr.MANIFEST_LIST_ARM64_DIGEST,
        tests.data.aws.ecr.MANIFEST_LIST_ATTESTATION_DIGEST,
    }

    # Assert - Check that manifest list has CONTAINS_IMAGE relationships to platform images (not attestations)
    contains_rels = check_rels(
        neo4j_session,
        "ECRImage",
        "digest",
        "ECRImage",
        "digest",
        "CONTAINS_IMAGE",
        rel_direction_right=True,
    )

    manifest_list_contains = {
        img_digest
        for (ml_digest, img_digest) in contains_rels
        if ml_digest == tests.data.aws.ecr.MANIFEST_LIST_DIGEST
    }

    # Manifest list should point to platform images (AMD64, ARM64) but NOT attestations
    assert manifest_list_contains == {
        tests.data.aws.ecr.MANIFEST_LIST_AMD64_DIGEST,
        tests.data.aws.ecr.MANIFEST_LIST_ARM64_DIGEST,
    }

    # Assert - Check that attestation has ATTESTS relationship to the image it validates
    attests_rels = check_rels(
        neo4j_session,
        "ECRImage",
        "digest",
        "ECRImage",
        "digest",
        "ATTESTS",
        rel_direction_right=True,
    )

    # Attestation should point to the AMD64 image
    assert (
        tests.data.aws.ecr.MANIFEST_LIST_ATTESTATION_DIGEST,
        tests.data.aws.ecr.MANIFEST_LIST_AMD64_DIGEST,
    ) in attests_rels


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=[
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/single-platform-repository",
            "registryId": "000000000000",
            "repositoryName": "single-platform-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository",
            "createdAt": datetime.datetime(2025, 1, 1, 0, 0, 1),
        }
    ],
)
def test_sync_single_platform_image_marked_as_manifest_list(
    mock_get_repos, neo4j_session
):
    """
    Test that single-platform images incorrectly marked as manifest lists are handled gracefully.

    This tests the bug fix where AWS ECR's describe_images API reports a manifest list media type,
    but batch_get_image with restrictive acceptedMediaTypes returns empty results because the
    image is actually a single-platform image.

    The fix ensures we return empty results instead of raising ValueError, allowing the image
    to be treated as a regular single-platform image.
    """

    # Remove everything previously put in the test graph since the fixture scope is set to module and not function.
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n;
        """,
    )
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mock_client = MagicMock()

    # Mock list_images paginator
    mock_list_paginator = MagicMock()
    mock_list_paginator.paginate.return_value = [
        {
            "imageIds": [
                {
                    "imageDigest": tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST,
                    "imageTag": "latest",
                }
            ]
        }
    ]

    # Mock describe_images paginator
    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [tests.data.aws.ecr.SINGLE_PLATFORM_IMAGE_DETAILS]}
    ]

    # Configure get_paginator to return the appropriate paginator
    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        elif name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator

    # Mock batch_get_image to return empty results (simulating the bug scenario)
    # This happens when describe_images reports manifest list media type but the image
    # is actually single-platform, causing batch_get_image with restrictive acceptedMediaTypes
    # to return empty results
    mock_client.batch_get_image.return_value = (
        tests.data.aws.ecr.BATCH_GET_MANIFEST_LIST_EMPTY_RESPONSE
    )

    boto3_session.client.return_value = mock_client

    # Act - This should NOT raise ValueError with the fix
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Check that the image was created as a regular single-platform image
    ecr_images = neo4j_session.run(
        """
        MATCH (img:ECRImage)
        RETURN img.digest AS digest, img.type AS type, img.architecture AS architecture,
               img.os AS os, img.variant AS variant
        ORDER BY img.digest
        """
    ).data()

    # Should have exactly 1 image node (treated as regular image, not manifest list)
    assert len(ecr_images) == 1

    # Verify it's the single-platform image
    single_platform_img = ecr_images[0]
    assert single_platform_img["digest"] == tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST
    assert (
        single_platform_img["type"] == "image"
    )  # Should be "image", not "manifest_list"
    assert (
        single_platform_img["architecture"] is None
    )  # No platform info since not a real manifest list
    assert single_platform_img["os"] is None
    assert single_platform_img["variant"] is None

    # Assert - Check that ECRRepositoryImage was created and points to the image
    repo_images = neo4j_session.run(
        """
        MATCH (repo_img:ECRRepositoryImage)
        RETURN repo_img.id AS id, repo_img.uri AS uri
        """
    ).data()

    assert len(repo_images) == 1
    assert repo_images[0]["uri"] == (
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository:latest"
    )

    # Assert - Check that ECRRepositoryImage has IMAGE relationship to ECRImage
    all_rels = check_rels(
        neo4j_session,
        "ECRRepositoryImage",
        "id",
        "ECRImage",
        "digest",
        "IMAGE",
        rel_direction_right=True,
    )

    # Should have relationship from repo image to the single image digest
    repo_image_id = (
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository:latest"
    )
    image_digests = {
        img_digest for (repo_id, img_digest) in all_rels if repo_id == repo_image_id
    }

    assert len(image_digests) == 1
    assert tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST in image_digests
