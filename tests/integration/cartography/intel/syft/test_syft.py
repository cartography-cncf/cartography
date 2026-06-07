"""
Integration tests for cartography.intel.syft module.

These tests verify that Syft ingestion correctly creates SyftPackage nodes
with DEPENDS_ON relationships between them.
"""

import json
from unittest.mock import MagicMock

import cartography.intel.aws.ecr
from cartography.intel.syft import sync_single_syft
from cartography.intel.syft import sync_syft_from_dir
from cartography.intel.syft import sync_syft_from_s3
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGE_DEPENDENCIES
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGES
from tests.data.syft.syft_sample import SYFT_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_REPOSITORY_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/syft-test-repository"
)
TEST_REPOSITORY = {
    "repositoryArn": (
        "arn:aws:ecr:us-east-1:000000000000:repository/syft-test-repository"
    ),
    "registryId": TEST_ACCOUNT_ID,
    "repositoryName": "syft-test-repository",
    "repositoryUri": TEST_REPOSITORY_URI,
    "createdAt": "2025-01-01T00:00:00.000000-00:00",
}

SYFT_CURRENT_SOURCE_SAMPLE = {
    **SYFT_SAMPLE,
    "source": {
        "id": "sha256:source",
        "name": "alpine",
        "version": "3.19",
        "type": "image",
        "metadata": {
            "userInput": "alpine:3.19",
            "imageID": "sha256:image-config",
            "manifestDigest": "sha256:platform",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "tags": ["alpine:3.19"],
            "repoDigests": ["alpine@sha256:index"],
            "architecture": "arm64",
            "os": "linux",
        },
    },
}

SYFT_CURRENT_REPO_DIGEST_SOURCE_SAMPLE = {
    **SYFT_SAMPLE,
    "source": {
        "id": "sha256:source",
        "name": "alpine",
        "version": "sha256:platform",
        "type": "image",
        "metadata": {
            "userInput": "alpine@sha256:platform",
            "imageID": "sha256:image-config",
            "manifestDigest": "sha256:local-manifest",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "tags": [],
            "repoDigests": ["alpine@sha256:platform"],
            "architecture": "arm64",
            "os": "linux",
        },
    },
}

SYFT_NO_DIGEST_SOURCE_SAMPLE = {
    **SYFT_SAMPLE,
    "source": {
        "id": "sha256:source",
        "name": "alpine",
        "version": "3.19",
        "type": "image",
        "metadata": {},
    },
}


def _sync_ecr_repository_images(
    neo4j_session,
    image_details: list[dict],
) -> None:
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        [TEST_REPOSITORY],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    repo_images_list, ecr_images_list = (
        cartography.intel.aws.ecr.transform_ecr_repository_images(
            {TEST_REPOSITORY_URI: image_details},
        )
    )
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        ecr_images_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _sync_single_platform_image(
    neo4j_session,
    image_digest: str,
) -> None:
    _sync_ecr_repository_images(
        neo4j_session,
        [
            {
                "imageDigest": image_digest,
                "imageTag": "latest",
                "repositoryName": "syft-test-repository",
                "imageManifestMediaType": (
                    "application/vnd.docker.distribution.manifest.v2+json"
                ),
            },
        ],
    )


def _sync_manifest_list_with_platform_image(
    neo4j_session,
    manifest_list_digest: str,
    platform_image_digest: str,
) -> None:
    _sync_ecr_repository_images(
        neo4j_session,
        [
            {
                "imageDigest": manifest_list_digest,
                "imageTag": "latest",
                "repositoryName": "syft-test-repository",
                "imageManifestMediaType": "application/vnd.oci.image.index.v1+json",
                "_manifest_images": [
                    {
                        "digest": platform_image_digest,
                        "type": "image",
                        "architecture": "arm64",
                        "os": "linux",
                        "variant": None,
                        "media_type": (
                            "application/vnd.docker.distribution.manifest.v2+json"
                        ),
                    },
                ],
            },
        ],
    )


def test_sync_single_syft_creates_syft_package_nodes(neo4j_session):
    """
    Test that sync_single_syft creates SyftPackage nodes with correct properties.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")

    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
    )

    # Check SyftPackage nodes exist with expected IDs
    actual_nodes = check_nodes(neo4j_session, "SyftPackage", ["id"])
    expected_nodes = {(pkg_id,) for pkg_id in EXPECTED_SYFT_PACKAGES}
    assert actual_nodes == expected_nodes

    # Verify a specific node has all expected properties
    result = neo4j_session.run(
        """
        MATCH (p:SyftPackage {id: 'npm|express|4.18.2'})
        RETURN p.name AS name, p.version AS version, p.type AS type,
               p.purl AS purl, p.language AS language, p.found_by AS found_by,
               p.normalized_id AS normalized_id, p.lastupdated AS lastupdated
        """,
    ).single()

    assert result["name"] == "express"
    assert result["version"] == "4.18.2"
    assert result["type"] == "npm"
    assert result["purl"] == "pkg:npm/express@4.18.2"
    assert result["language"] == "javascript"
    assert result["found_by"] == "javascript-package-cataloger"
    assert result["normalized_id"] == "npm|express|4.18.2"
    assert result["lastupdated"] == TEST_UPDATE_TAG


def test_sync_single_syft_creates_depends_on(neo4j_session):
    """
    Test that sync_single_syft creates DEPENDS_ON between SyftPackage nodes.
    """
    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "SyftPackage",
        "id",
        "DEPENDS_ON",
        rel_direction_right=True,
    )

    assert actual_rels == EXPECTED_SYFT_PACKAGE_DEPENDENCIES


def test_sync_single_syft_creates_deployed_to_image(neo4j_session):
    """
    Test that sync_single_syft creates DEPLOYED relationships to ontology Image nodes.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")
    _sync_single_platform_image(
        neo4j_session,
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )

    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "Image",
        "_ont_digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    expected_rels = {
        (
            pkg_id,
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )
        for pkg_id in EXPECTED_SYFT_PACKAGES
    }
    assert actual_rels == expected_rels


def test_sync_single_syft_creates_deployed_to_current_source_image_digest(
    neo4j_session,
):
    """
    Test that current Syft source.metadata digests link to Image, not ImageManifestList.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")
    _sync_manifest_list_with_platform_image(
        neo4j_session, "sha256:index", "sha256:platform"
    )

    assert check_nodes(neo4j_session, "Image", ["_ont_digest"]) >= {
        ("sha256:platform",),
    }
    assert check_nodes(neo4j_session, "ImageManifestList", ["_ont_digest"]) >= {
        ("sha256:index",),
    }

    sync_single_syft(
        neo4j_session,
        SYFT_CURRENT_SOURCE_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "Image",
        "_ont_digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    expected_rels = {(pkg_id, "sha256:platform") for pkg_id in EXPECTED_SYFT_PACKAGES}
    assert actual_rels == expected_rels


def test_sync_single_syft_creates_deployed_from_repo_digest_candidate(
    neo4j_session,
):
    """
    Test current Syft repoDigests can link to the scanned platform Image.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")
    _sync_single_platform_image(neo4j_session, "sha256:platform")

    sync_single_syft(
        neo4j_session,
        SYFT_CURRENT_REPO_DIGEST_SOURCE_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "Image",
        "_ont_digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    expected_rels = {(pkg_id, "sha256:platform") for pkg_id in EXPECTED_SYFT_PACKAGES}
    assert actual_rels == expected_rels


def test_sync_single_syft_skips_deployed_without_image_digest_candidates(
    neo4j_session,
):
    """
    Test malformed Syft image metadata does not create package-to-image links.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")
    _sync_single_platform_image(neo4j_session, "sha256:platform")

    sync_single_syft(
        neo4j_session,
        SYFT_NO_DIGEST_SOURCE_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "Image",
        "_ont_digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    assert actual_rels == set()


def test_sync_syft_from_dir(
    tmp_path,
    neo4j_session,
):
    """
    Test sync_syft_from_dir reads files and creates SyftPackage nodes.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }
    report_path = tmp_path / "syft.json"
    report_path.write_text(json.dumps(SYFT_SAMPLE), encoding="utf-8")

    sync_syft_from_dir(
        neo4j_session,
        str(tmp_path),
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: SyftPackage nodes should exist
    actual_nodes = check_nodes(neo4j_session, "SyftPackage", ["id"])
    assert len(actual_nodes) == 5

    # Assert: DEPENDS_ON relationships should exist
    result = neo4j_session.run(
        """
        MATCH (:SyftPackage)-[r:DEPENDS_ON]->(:SyftPackage)
        RETURN count(r) AS count
        """
    ).single()

    assert result["count"] == 3


def test_sync_syft_from_s3(
    neo4j_session,
):
    """
    Test sync_syft_from_s3 reads bucket objects and creates SyftPackage nodes.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")

    boto3_session = MagicMock()
    s3_client = boto3_session.client.return_value
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "reports/syft.json"}]},
    ]
    s3_client.get_object.return_value = {
        "Body": MagicMock(
            read=MagicMock(return_value=json.dumps(SYFT_SAMPLE).encode("utf-8"))
        ),
    }

    sync_syft_from_s3(
        neo4j_session,
        "example-bucket",
        "reports/",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        boto3_session,
    )

    actual_nodes = check_nodes(neo4j_session, "SyftPackage", ["id"])
    assert len(actual_nodes) == 5
