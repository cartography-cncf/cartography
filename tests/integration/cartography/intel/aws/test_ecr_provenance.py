from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

import cartography.intel.aws.ecr
import cartography.intel.aws.ecr_provenance
import tests.data.aws.ecr as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _load_example_ecr_images(neo4j_session):
    repository = test_data.DESCRIBE_REPOSITORIES["repositories"][0]
    repo_uri = repository["repositoryUri"]
    parent_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    child_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000001"
    )
    repo_data = {
        repo_uri: [
            {
                "imageDigest": parent_digest,
                "imageTag": "1",
            },
            {
                "imageDigest": child_digest,
                "imageTag": "2",
            },
        ],
    }

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        [repository],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    repo_images, ecr_images = cartography.intel.aws.ecr.transform_ecr_repository_images(
        repo_data
    )
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images,
        ecr_images,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    return parent_digest, child_digest


def test_loads_ecr_image_provenance_and_built_from_relationship(neo4j_session):
    parent_digest, child_digest = _load_example_ecr_images(neo4j_session)

    provenance_items = [
        {
            "imageDigest": child_digest,
            "parent_image_uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@1",
            "parent_image_digest": parent_digest,
            "source_uri": "https://github.com/example/repo",
            "source_revision": "abc123",
            "invocation_uri": "https://github.com/example/repo",
            "invocation_workflow": ".github/workflows/build.yaml",
            "invocation_run_number": "1001",
            "source_file": "Dockerfile",
            "from_attestation": True,
            "confidence": "explicit",
        },
    ]

    cartography.intel.aws.ecr_provenance.load_ecr_image_provenance(
        neo4j_session,
        provenance_items,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ecr_provenance.load_ecr_image_parent_relationships(
        neo4j_session,
        provenance_items,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "ECRImage",
        ["digest", "source_uri", "invocation_workflow"],
    ) >= {
        (
            child_digest,
            "https://github.com/example/repo",
            ".github/workflows/build.yaml",
        ),
    }
    assert check_rels(
        neo4j_session,
        "ECRImage",
        "id",
        "ECRImage",
        "id",
        "BUILT_FROM",
        rel_direction_right=True,
    ) >= {(child_digest, parent_digest)}


def test_cleanup_removes_stale_ecr_image_provenance(neo4j_session):
    parent_digest, child_digest = _load_example_ecr_images(neo4j_session)

    provenance_items = [
        {
            "imageDigest": child_digest,
            "parent_image_uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@1",
            "parent_image_digest": parent_digest,
            "source_uri": "https://github.com/example/repo",
            "source_revision": "abc123",
            "invocation_uri": "https://github.com/example/repo",
            "invocation_workflow": ".github/workflows/build.yaml",
            "invocation_run_number": "1001",
            "source_file": "Dockerfile",
            "from_attestation": True,
            "confidence": "explicit",
        },
    ]

    cartography.intel.aws.ecr_provenance.load_ecr_image_provenance(
        neo4j_session,
        provenance_items,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ecr_provenance.load_ecr_image_parent_relationships(
        neo4j_session,
        provenance_items,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.ecr_provenance.cleanup(
        neo4j_session,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
    )

    assert check_nodes(
        neo4j_session,
        "ECRImage",
        ["digest", "source_uri"],
    ) >= {
        (child_digest, None),
    }
    assert (
        child_digest,
        parent_digest,
    ) not in check_rels(
        neo4j_session,
        "ECRImage",
        "id",
        "ECRImage",
        "id",
        "BUILT_FROM",
        rel_direction_right=True,
    )


def test_transform_ecr_image_provenance_sorts_output():
    transformed = cartography.intel.aws.ecr_provenance.transform_ecr_image_provenance(
        {
            "sha256:b": {"source_uri": "https://github.com/example/b"},
            "sha256:a": {"source_uri": "https://github.com/example/a"},
        }
    )

    assert [item["imageDigest"] for item in transformed] == ["sha256:a", "sha256:b"]
    assert all(item["from_attestation"] is True for item in transformed)
    assert all(item["confidence"] == "explicit" for item in transformed)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parent_uri,parent_digest",
    [
        (
            "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-image@v1.0",
            "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        ),
        (
            "pkg:oci/myregistry.azurecr.io/base-image@v1.0",
            "sha256:abc123def456",
        ),
        (
            "oci://harbor.example.com/library/alpine@sha256:xyz789",
            "sha256:xyz789abc",
        ),
    ],
)
async def test_extract_provenance_from_attestation_uri_schemes(
    parent_uri, parent_digest
):
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
            ]
        },
        "application/vnd.oci.image.manifest.v1+json",
    )
    attestation_blob = {
        "predicate": {
            "materials": [
                {
                    "uri": parent_uri,
                    "digest": {"sha256": parent_digest.removeprefix("sha256:")},
                },
            ]
        }
    }

    original_batch_get_manifest = (
        cartography.intel.aws.ecr_provenance.batch_get_manifest
    )
    original_get_blob = cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned
    cartography.intel.aws.ecr_provenance.batch_get_manifest = AsyncMock(
        return_value=attestation_manifest
    )
    cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = AsyncMock(
        return_value=attestation_blob
    )

    try:
        result = await cartography.intel.aws.ecr_provenance._extract_provenance_from_attestation(
            mock_ecr_client,
            "test-repo",
            "sha256:attestation",
            mock_http_client,
        )
    finally:
        cartography.intel.aws.ecr_provenance.batch_get_manifest = (
            original_batch_get_manifest
        )
        cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = (
            original_get_blob
        )

    assert result is not None
    assert result["parent_image_uri"] == parent_uri
    assert result["parent_image_digest"] == parent_digest


@pytest.mark.asyncio
async def test_extract_provenance_from_attestation_with_source_info():
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
            ]
        },
        "application/vnd.oci.image.manifest.v1+json",
    )
    attestation_blob = {
        "predicate": {
            "materials": [
                {
                    "uri": "pkg:docker/base-image@v1.0",
                    "digest": {"sha256": "parentdigest123"},
                },
            ],
            "invocation": {
                "environment": {
                    "github_repository": "exampleco/example-repo",
                    "github_workflow_ref": "exampleco/example-repo/.github/workflows/build.yaml@refs/heads/main",
                    "github_run_number": "1001",
                }
            },
            "metadata": {
                "https://mobyproject.org/buildkit@v1#metadata": {
                    "vcs": {
                        "source": "https://github.com/exampleco/example-repo",
                        "revision": "abc123def456",
                    }
                }
            },
        }
    }

    original_batch_get_manifest = (
        cartography.intel.aws.ecr_provenance.batch_get_manifest
    )
    original_get_blob = cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned
    cartography.intel.aws.ecr_provenance.batch_get_manifest = AsyncMock(
        return_value=attestation_manifest
    )
    cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = AsyncMock(
        return_value=attestation_blob
    )

    try:
        result = await cartography.intel.aws.ecr_provenance._extract_provenance_from_attestation(
            mock_ecr_client,
            "test-repo",
            "sha256:attestation",
            mock_http_client,
        )
    finally:
        cartography.intel.aws.ecr_provenance.batch_get_manifest = (
            original_batch_get_manifest
        )
        cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = (
            original_get_blob
        )

    assert result is not None
    assert result["parent_image_uri"] == "pkg:docker/base-image@v1.0"
    assert result["parent_image_digest"] == "sha256:parentdigest123"
    assert result["source_uri"] == "https://github.com/exampleco/example-repo"
    assert result["source_revision"] == "abc123def456"
    assert result["invocation_uri"] == "https://github.com/exampleco/example-repo"
    assert result["invocation_workflow"] == ".github/workflows/build.yaml"
    assert result["invocation_run_number"] == "1001"
    assert result["source_file"] == "Dockerfile"


@pytest.mark.asyncio
async def test_extract_provenance_source_file_with_config_source():
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
            ]
        },
        "application/vnd.oci.image.manifest.v1+json",
    )
    attestation_blob = {
        "predicate": {
            "invocation": {
                "configSource": {
                    "entryPoint": "Dockerfile.prod",
                },
                "environment": {
                    "github_repository": "myorg/myrepo",
                    "github_workflow_ref": "myorg/myrepo/.github/workflows/build.yaml@refs/heads/main",
                },
            },
            "metadata": {
                "https://mobyproject.org/buildkit@v1#metadata": {
                    "vcs": {
                        "source": "https://github.com/myorg/myrepo",
                        "localdir:dockerfile": "./deploy",
                    }
                }
            },
        }
    }

    original_batch_get_manifest = (
        cartography.intel.aws.ecr_provenance.batch_get_manifest
    )
    original_get_blob = cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned
    cartography.intel.aws.ecr_provenance.batch_get_manifest = AsyncMock(
        return_value=attestation_manifest
    )
    cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = AsyncMock(
        return_value=attestation_blob
    )

    try:
        result = await cartography.intel.aws.ecr_provenance._extract_provenance_from_attestation(
            mock_ecr_client,
            "test-repo",
            "sha256:attestation",
            mock_http_client,
        )
    finally:
        cartography.intel.aws.ecr_provenance.batch_get_manifest = (
            original_batch_get_manifest
        )
        cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = (
            original_get_blob
        )

    assert result is not None
    assert result["source_uri"] == "https://github.com/myorg/myrepo"
    assert result["source_file"] == "deploy/Dockerfile.prod"


@pytest.mark.asyncio
async def test_extract_provenance_slsa_v1_format():
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
            ]
        },
        "application/vnd.oci.image.manifest.v1+json",
    )
    attestation_blob = {
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "resolvedDependencies": [
                    {
                        "uri": "pkg:docker/111111111111.dkr.ecr.us-east-1.amazonaws.com/base-images@examplebase?platform=linux%2Famd64",
                        "digest": {
                            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                        },
                    },
                    {
                        "uri": "pkg:docker/docker/dockerfile@1.7",
                        "digest": {
                            "sha256": "a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e"
                        },
                    },
                ],
                "externalParameters": {
                    "configSource": {"path": "Dockerfile"},
                },
            },
            "runDetails": {
                "builder": {
                    "id": "https://github.com/exampleco/example-repo/actions/runs/123456789/attempts/1",
                },
                "metadata": {
                    "buildkit_metadata": {
                        "vcs": {
                            "source": "https://github.com/exampleco/example-repo",
                            "revision": "abcdef0123456789abcdef0123456789abcdef01",
                            "localdir:context": "example-service",
                            "localdir:dockerfile": "example-service",
                        },
                    },
                },
            },
        },
    }

    original_batch_get_manifest = (
        cartography.intel.aws.ecr_provenance.batch_get_manifest
    )
    original_get_blob = cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned
    cartography.intel.aws.ecr_provenance.batch_get_manifest = AsyncMock(
        return_value=attestation_manifest
    )
    cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = AsyncMock(
        return_value=attestation_blob
    )

    try:
        result = await cartography.intel.aws.ecr_provenance._extract_provenance_from_attestation(
            mock_ecr_client,
            "example-service",
            "sha256:attestation",
            mock_http_client,
        )
    finally:
        cartography.intel.aws.ecr_provenance.batch_get_manifest = (
            original_batch_get_manifest
        )
        cartography.intel.aws.ecr_provenance.get_blob_json_via_presigned = (
            original_get_blob
        )

    assert result is not None
    assert (
        result["parent_image_uri"]
        == "pkg:docker/111111111111.dkr.ecr.us-east-1.amazonaws.com/base-images@examplebase?platform=linux%2Famd64"
    )
    assert (
        result["parent_image_digest"]
        == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert result["source_uri"] == "https://github.com/exampleco/example-repo"
    assert result["source_revision"] == "abcdef0123456789abcdef0123456789abcdef01"
    assert result["invocation_uri"] == "https://github.com/exampleco/example-repo"
    assert result["source_file"] == "example-service/Dockerfile"
