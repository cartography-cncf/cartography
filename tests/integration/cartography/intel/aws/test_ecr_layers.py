from contextlib import nullcontext
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

import cartography.intel.aws.ecr
import cartography.intel.aws.ecr_image_layers as ecr_layers
import cartography.intel.github.repos
import cartography.intel.github.supply_chain
import tests.data.aws.ecr as test_data
import tests.data.github.repos as github_test_data
from cartography.intel.aws.ecr_image_layers import sync as sync_ecr_layers
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


class _FakeAsyncEcrClientContext:
    def __init__(self, ecr_client):
        self.ecr_client = ecr_client

    async def __aenter__(self):
        return self.ecr_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class _FakeHttpResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json_data


class _FakeAsyncHttpClient:
    def __init__(self, json_data):
        self._json_data = json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def get(self, url, timeout):
        return _FakeHttpResponse(self._json_data)


def _load_example_ecr_image(neo4j_session, mocker):
    # Credential-recovery tests must exercise the registry fetch path even if a
    # previous test left a complete layer closure for this shared image digest.
    mocker.patch.object(
        ecr_layers,
        "get_complete_layer_digests",
        return_value=set(),
    )
    mocker.patch.object(
        cartography.intel.aws.ecr,
        "get_ecr_repositories",
        return_value=test_data.DESCRIBE_REPOSITORIES["repositories"][:1],
    )
    mocker.patch.object(
        cartography.intel.aws.ecr,
        "get_ecr_repository_images",
        return_value=test_data.LIST_REPOSITORY_IMAGES[
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
        ][:1],
    )
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )


def _synthetic_client_error(error_code):
    return ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "Synthetic AWS client error",
            },
        },
        "AssumeRole",
    )


def test_sync_recreates_session_after_credential_refresh_failure(
    mocker,
    neo4j_session,
):
    # Arrange
    _load_example_ecr_image(neo4j_session, mocker)
    stale_session = MagicMock(name="stale_session")
    fresh_session = MagicMock(name="fresh_session")
    session_factory = MagicMock(return_value=fresh_session)

    stale_client = AsyncMock()
    stale_client.batch_get_image.side_effect = _synthetic_client_error(
        "InvalidClientTokenId",
    )
    fresh_client = AsyncMock()
    fresh_client.batch_get_image.return_value = test_data.BATCH_GET_IMAGE_RESPONSE
    create_client = mocker.patch.object(
        ecr_layers,
        "create_aioboto3_client",
        side_effect=[
            _FakeAsyncEcrClientContext(stale_client),
            _FakeAsyncEcrClientContext(fresh_client),
        ],
    )
    mocker.patch.object(
        ecr_layers,
        "get_blob_json_via_presigned",
        new=AsyncMock(return_value=test_data.SAMPLE_CONFIG_BLOB),
    )

    # Act
    sync_ecr_layers(
        neo4j_session,
        stale_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        aioboto3_session_factory=session_factory,
    )

    # Assert
    session_factory.assert_called_once_with()
    assert [client_call.args[0] for client_call in create_client.call_args_list] == [
        stale_session,
        fresh_session,
    ]
    assert check_nodes(neo4j_session, "AWSECRImageLayer", ["id"])


@pytest.mark.parametrize(
    ("error_code", "use_session_factory", "expected_attempts", "propagates"),
    [
        ("InvalidClientTokenId", True, 2, True),
        ("InvalidClientTokenId", False, 1, True),
        ("AccessDeniedException", True, 1, False),
        ("RepositoryNotFoundException", True, 1, True),
    ],
)
def test_sync_bounds_credential_retry_and_preserves_other_errors(
    error_code,
    use_session_factory,
    expected_attempts,
    propagates,
    mocker,
    neo4j_session,
):
    # Arrange
    _load_example_ecr_image(neo4j_session, mocker)
    client_error = _synthetic_client_error(error_code)
    sessions = [
        MagicMock(name=f"session_{index}") for index in range(expected_attempts)
    ]
    session_factory = MagicMock(return_value=sessions[-1])
    clients = [AsyncMock() for _ in range(expected_attempts)]
    for client in clients:
        client.batch_get_image.side_effect = client_error
    create_client = mocker.patch.object(
        ecr_layers,
        "create_aioboto3_client",
        side_effect=[_FakeAsyncEcrClientContext(client) for client in clients],
    )
    sync_kwargs = (
        {"aioboto3_session_factory": session_factory} if use_session_factory else {}
    )

    # Act
    expectation = pytest.raises(ClientError) if propagates else nullcontext()
    with expectation as exc_info:
        sync_ecr_layers(
            neo4j_session,
            sessions[0],
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
            **sync_kwargs,
        )

    # Assert
    if propagates:
        assert exc_info.value is client_error
    assert create_client.call_count == expected_attempts
    assert session_factory.call_count == expected_attempts - 1


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=test_data.DESCRIBE_REPOSITORIES["repositories"][:1],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=test_data.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    ][:1],
)
@patch("cartography.client.aws.ecr.get_ecr_images")
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
@patch("cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned")
def test_sync_with_layers(
    mock_get_blob,
    mock_batch_get_manifest,
    mock_get_ecr_images,
    mock_get_repo_images,
    mock_get_repos,
    neo4j_session,
):
    """Test ECR sync with image layer support"""
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Mock images from graph
    mock_get_ecr_images.return_value = {
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "example-repository",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )
    }

    # Mock manifest retrieval
    mock_batch_get_manifest.return_value = (
        test_data.SAMPLE_MANIFEST,
        "application/vnd.docker.distribution.manifest.v2+json",
    )

    # Mock config blob retrieval
    mock_get_blob.return_value = test_data.SAMPLE_CONFIG_BLOB

    # Create mock boto3 session
    boto3_session = MagicMock()
    boto3_session.client.return_value.batch_get_image.return_value = (
        test_data.BATCH_GET_IMAGE_RESPONSE
    )
    boto3_session.client.return_value.get_download_url_for_layer.return_value = (
        test_data.GET_DOWNLOAD_URL_RESPONSE
    )

    # Act
    # Run sync with layer support
    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    # Check that AWSECRImage nodes were created
    expected_ecr_images = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            TEST_REGION,
        ),
    }
    assert (
        check_nodes(neo4j_session, "AWSECRImage", ["id", "region"])
        == expected_ecr_images
    )

    # Check that AWSECRImageLayer nodes were created
    expected_layers = {
        ("sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",),
        ("sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",),
        ("sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",),
    }
    assert check_nodes(neo4j_session, "AWSECRImageLayer", ["id"]) == expected_layers
    # Also verify they have the ImageLayer extra label
    assert check_nodes(neo4j_session, "ImageLayer", ["id"]) == expected_layers

    # Check NEXT relationships between layers
    expected_next_rels = {
        (
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ),
        (
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSECRImageLayer",
            "id",
            "AWSECRImageLayer",
            "id",
            "NEXT",
            rel_direction_right=True,
        )
        == expected_next_rels
    )

    expected_has_layer_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSECRImage",
            "id",
            "AWSECRImageLayer",
            "id",
            "HAS_LAYER",
            rel_direction_right=True,
        )
        == expected_has_layer_rels
    )

    sequence_record = neo4j_session.run(
        """
        MATCH (img:AWSECRImage {id: $digest})
        RETURN img.layer_diff_ids AS layer_diff_ids
        """,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    ).single()
    assert sequence_record
    assert sequence_record["layer_diff_ids"] == [
        "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
    ]

    path_rows = neo4j_session.run(
        """
        MATCH (img:AWSECRImage {id: $digest})-[:HEAD]->(head:AWSECRImageLayer)
        MATCH (img)-[:TAIL]->(tail:AWSECRImageLayer)
        MATCH path = (head)-[:NEXT*0..]->(tail)
        WHERE ALL(layer IN nodes(path) WHERE (img)-[:HAS_LAYER]->(layer))
        WITH path
        ORDER BY length(path) DESC
        LIMIT 1
        UNWIND range(0, length(path)) AS idx
        RETURN nodes(path)[idx].diff_id AS diff_id
        ORDER BY idx
        """,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )
    path_layers = [record["diff_id"] for record in path_rows]
    assert path_layers == sequence_record["layer_diff_ids"]

    # Check HEAD relationship from AWSECRImage to first layer
    expected_head_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSECRImage",
            "id",
            "ImageLayer",
            "id",
            "HEAD",
            rel_direction_right=True,
        )
        == expected_head_rels
    )

    # Check TAIL relationship from AWSECRImage to last layer
    expected_tail_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSECRImage",
            "id",
            "ImageLayer",
            "id",
            "TAIL",
            rel_direction_right=True,
        )
        == expected_tail_rels
    )

    # A second inventory pass observes the same immutable digest. Layer sync
    # must refresh the existing closure without another ECR manifest/config pull.
    second_update_tag = TEST_UPDATE_TAG + 1
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        second_update_tag,
        {"UPDATE_TAG": second_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )
    manifest_fetch_count = mock_batch_get_manifest.call_count
    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        second_update_tag,
        {"UPDATE_TAG": second_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert mock_batch_get_manifest.call_count == manifest_fetch_count
    stale_rows = neo4j_session.run(
        """
        MATCH (img:AWSECRImage {id: $digest})-[rel:HAS_LAYER|HEAD|TAIL]->(layer)
        WHERE img.lastupdated <> $update_tag
           OR rel.lastupdated <> $update_tag
           OR layer.lastupdated <> $update_tag
        RETURN img, rel, layer
        """,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        update_tag=second_update_tag,
    ).data()
    assert stale_rows == []


def test_layer_cleanup_does_not_delete_stale_inventory_images(neo4j_session):
    # Arrange
    account_id = "layer-cleanup-account"
    image_digest = "sha256:layer-cleanup-image"
    layer_diff_id = "sha256:layer-cleanup-layer"
    neo4j_session.run(
        """
        MERGE (account:AWSAccount {id: $account_id})
        MERGE (image:AWSECRImage {id: $image_digest})
        SET image.digest = $image_digest, image.lastupdated = 1
        MERGE (account)-[image_resource:RESOURCE]->(image)
        SET image_resource.lastupdated = 1
        MERGE (layer:AWSECRImageLayer {id: $layer_diff_id})
        SET layer.diff_id = $layer_diff_id, layer.lastupdated = 1
        MERGE (account)-[layer_resource:RESOURCE]->(layer)
        SET layer_resource.lastupdated = 1
        MERGE (image)-[has_layer:HAS_LAYER]->(layer)
        SET has_layer.lastupdated = 1
        """,
        account_id=account_id,
        image_digest=image_digest,
        layer_diff_id=layer_diff_id,
    ).consume()

    # Act
    ecr_layers.cleanup(
        neo4j_session,
        {"AWS_ID": account_id, "UPDATE_TAG": 2},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSECRImage", ["id"]) >= {(image_digest,)}
    relationship_count = neo4j_session.run(
        """
        MATCH (:AWSECRImage {id: $image_digest})-[relationship:HAS_LAYER]->()
        RETURN count(relationship) AS count
        """,
        image_digest=image_digest,
    ).single(strict=True)["count"]
    assert relationship_count == 0


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=test_data.DESCRIBE_REPOSITORIES["repositories"][:1],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=test_data.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    ][:2],
)
@patch("cartography.intel.aws.ecr_image_layers.fetch_image_layers_async")
@patch("cartography.client.aws.ecr.get_ecr_images")
def test_sync_built_from_relationship(
    mock_get_ecr_images,
    mock_fetch_layers,
    mock_get_repo_images,
    mock_get_repos,
    neo4j_session,
):
    """Test that BUILT_FROM relationship is created between AWSECRImage nodes."""
    parent_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    child_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000001"
    )

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    neo4j_session.run(
        """
        MATCH (img:AWSECRImage)
        WHERE img.digest IN $digests
        REMOVE img.layer_diff_ids
        """,
        digests=[parent_digest, child_digest],
    ).consume()

    mock_get_ecr_images.return_value = {
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "example-repository",
            parent_digest,
        ),
        (
            "us-east-1",
            "2",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
            "example-repository",
            child_digest,
        ),
    }

    mock_fetch_layers.return_value = (
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": {
                "linux/amd64": test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
            },
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": {
                "linux/amd64": test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
            },
        },
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": parent_digest,
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": child_digest,
        },
        {},  # history_by_diff_id
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": {
                "parent_image_uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@1",
                "parent_image_digest": parent_digest,
            }
        },
        True,
    )

    sync_ecr_layers(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_rels(
        neo4j_session,
        "AWSECRImage",
        "id",
        "AWSECRImage",
        "id",
        "BUILT_FROM",
        rel_direction_right=True,
    ) >= {(child_digest, parent_digest)}


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=test_data.DESCRIBE_REPOSITORIES["repositories"][:1],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=test_data.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    ][:1],
)
# The test repo data carries no privileged fields, so the GitHub sync reaches out for
# them. Stub the fetch: unpatched it calls the real api.github.com and burns ~30s in
# retry backoff before the sync swallows the error.
@patch.object(
    cartography.intel.github.repos,
    "get_repo_security_and_analysis_by_url",
    return_value={},
)
@patch.object(
    cartography.intel.github.repos,
    "get_repo_privileged_details_by_url",
    return_value={},
)
@patch.object(cartography.intel.github.repos, "_get_dep_manifests_for_repos")
@patch.object(
    cartography.intel.github.repos, "_get_repo_collaborators_for_multiple_repos"
)
@patch.object(cartography.intel.github.repos, "get")
@patch("cartography.intel.aws.ecr_image_layers.httpx.AsyncClient")
@patch("cartography.intel.aws.ecr_image_layers.create_aioboto3_client")
def test_sync_circleci_label_provenance_links_github_repository(
    mock_create_aioboto3_client,
    mock_async_http_client,
    mock_get_github_repos,
    mock_get_repo_collaborators,
    mock_get_dep_manifests,
    mock_get_privileged_details,
    mock_get_security_and_analysis,
    mock_get_ecr_repo_images,
    mock_get_ecr_repos,
    neo4j_session,
):
    image_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    repo_url = "https://github.com/exampleorg/service"
    ecr_client = MagicMock()
    ecr_client.batch_get_image = AsyncMock(
        return_value=test_data.BATCH_GET_IMAGE_RESPONSE,
    )
    ecr_client.get_download_url_for_layer = AsyncMock(
        return_value=test_data.GET_DOWNLOAD_URL_RESPONSE,
    )
    mock_create_aioboto3_client.return_value = _FakeAsyncEcrClientContext(ecr_client)
    mock_async_http_client.return_value = _FakeAsyncHttpClient(
        test_data.SAMPLE_CONFIG_BLOB_WITH_CIRCLECI_LABELS,
    )
    mock_get_github_repos.return_value = github_test_data.GET_REPOS_CIRCLECI_PROVENANCE
    mock_get_repo_collaborators.return_value = {}
    mock_get_dep_manifests.return_value = ({}, True)

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    neo4j_session.run(
        """
        MATCH (img:AWSECRImage {digest: $digest})
        REMOVE img.layer_diff_ids
        """,
        digest=image_digest,
    ).consume()

    sync_ecr_layers(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    enriched = neo4j_session.run(
        """
        MATCH (img:AWSECRImage {digest: $digest})
        RETURN img.source_uri AS source_uri,
               img.source_revision AS source_revision,
               img.source_file AS source_file
        """,
        digest=image_digest,
    ).single()
    assert enriched["source_uri"] == repo_url
    assert enriched["source_revision"] == "abcdef0123456789abcdef0123456789abcdef01"
    assert enriched["source_file"] == "deploy/Dockerfile"

    cartography.intel.github.repos.sync(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "token",
        "https://api.github.com/graphql",
        "exampleorg",
    )
    assert check_nodes(neo4j_session, "GitHubRepository", ["id"]) == {(repo_url,)}

    cartography.intel.github.supply_chain.sync(
        neo4j_session,
        "token",
        "https://api.github.com/graphql",
        "exampleorg",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        [{"url": repo_url}],
        workflows=None,
    )

    packaged_from = neo4j_session.run(
        """
        MATCH (img:AWSECRImage {digest: $digest})-[r:PACKAGED_FROM]->(repo:GitHubRepository)
        RETURN repo.id AS repo_url, r.match_method AS match_method, r.dockerfile_path AS dockerfile_path
        """,
        digest=image_digest,
    ).single()
    assert packaged_from["repo_url"] == repo_url
    assert packaged_from["match_method"] == "provenance"
    assert packaged_from["dockerfile_path"] == "deploy/Dockerfile"


@patch("cartography.client.aws.ecr.get_ecr_images")
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
def test_sync_multi_region_event_loop_preserved(
    mock_batch_get_manifest,
    mock_get_ecr_images,
    neo4j_session,
):
    """Test that event loop is preserved across multiple region iterations."""
    from unittest.mock import MagicMock

    # Mock empty ECR images (no actual processing needed for this test)
    mock_get_ecr_images.return_value = set()
    mock_batch_get_manifest.return_value = ({}, "")

    # Create mock boto3 session
    boto3_session = MagicMock()

    try:
        sync_ecr_layers(
            neo4j_session,
            boto3_session,
            ["us-east-1", "us-west-2"],  # Multiple regions
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )
        # If we reach here without RuntimeError, our loop management is working
        assert True
    except RuntimeError as e:
        if "no current event loop" in str(e).lower():
            pytest.fail("Event loop was torn down between regions - fix needed")
        else:
            raise


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=[
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/multi-arch-repository",
            "registryId": "000000000000",
            "repositoryName": "multi-arch-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository",
            "createdAt": test_data.DESCRIBE_REPOSITORIES["repositories"][0][
                "createdAt"
            ],
        }
    ],
)
@patch("cartography.intel.aws.ecr_image_layers.fetch_image_layers_async")
def test_sync_layers_preserves_multi_arch_image_properties(
    mock_fetch_layers,
    mock_get_repos,
    neo4j_session,
):
    """
    Regression test for bug where ecr_image_layers sync would overwrite AWSECRImage properties to NULL.

    This test ensures that when layer sync runs after ECR sync, it preserves the type, architecture,
    os, variant, and other fields that were set during the initial ECR sync for multi-arch images.
    """
    # Clean up from previous tests
    neo4j_session.run("MATCH (n) DETACH DELETE n;")

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
                    "imageDigest": test_data.MANIFEST_LIST_DIGEST,
                    "imageTag": "v1.0",
                }
            ]
        }
    ]

    # Mock describe_images paginator
    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [test_data.MULTI_ARCH_IMAGE_DETAILS]}
    ]

    # Configure get_paginator
    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        elif name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator
    mock_client.batch_get_image.return_value = (
        test_data.BATCH_GET_MANIFEST_LIST_RESPONSE
    )
    boto3_session.client.return_value = mock_client

    # Act 1: Run ECR sync to populate AWSECRImage nodes with multi-arch properties
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert 1: Verify AWSECRImage nodes have type, architecture, os, variant set
    assert check_nodes(
        neo4j_session, "AWSECRImage", ["digest", "type", "architecture"]
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, "manifest_list", None),
        (test_data.MANIFEST_LIST_AMD64_DIGEST, "image", "amd64"),
        (test_data.MANIFEST_LIST_ARM64_DIGEST, "image", "arm64"),
        (test_data.MANIFEST_LIST_ATTESTATION_DIGEST, "attestation", "unknown"),
    }

    # Act 2: Run ECR layers sync
    # Mock fetch_image_layers_async to return layer data for platform-specific images only
    # (NOT manifest list or attestations - they're filtered out before fetching)
    mock_fetch_layers.return_value = (
        # image_layers_data - keyed by the platform-specific image URIs
        {
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_AMD64_DIGEST}": {
                "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            },
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_ARM64_DIGEST}": {
                "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"][
                    "diff_ids"
                ],
            },
        },
        # image_digest_map
        {
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_AMD64_DIGEST}": test_data.MANIFEST_LIST_AMD64_DIGEST,
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_ARM64_DIGEST}": test_data.MANIFEST_LIST_ARM64_DIGEST,
        },
        # history_by_diff_id (empty)
        {},
        # image_attestation_map (empty)
        {},
        True,
    )

    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert 2: Verify AWSECRImage properties are PRESERVED after layer sync (not overwritten to NULL)
    assert check_nodes(
        neo4j_session, "AWSECRImage", ["digest", "type", "architecture"]
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, "manifest_list", None),
        (test_data.MANIFEST_LIST_AMD64_DIGEST, "image", "amd64"),
        (test_data.MANIFEST_LIST_ARM64_DIGEST, "image", "arm64"),
        (test_data.MANIFEST_LIST_ATTESTATION_DIGEST, "attestation", "unknown"),
    }, "AWSECRImage properties were overwritten after layer sync!"

    # Verify layer relationships: only platform images (type="image") should have HAS_LAYER relationships
    # Manifest lists and attestations should NOT have any layer relationships
    has_layer_rels = check_rels(
        neo4j_session,
        "AWSECRImage",
        "digest",
        "AWSECRImageLayer",
        "diff_id",
        "HAS_LAYER",
        rel_direction_right=True,
    )

    # Get all AWSECRImage digests that have HAS_LAYER relationships
    images_with_layers = {img_digest for (img_digest, _) in has_layer_rels}

    # Only AMD64 and ARM64 platform images should have layers
    assert images_with_layers == {
        test_data.MANIFEST_LIST_AMD64_DIGEST,
        test_data.MANIFEST_LIST_ARM64_DIGEST,
    }, "Only platform-specific images should have layer relationships!"

    # Manifest list and attestations should NOT be in this set
    assert test_data.MANIFEST_LIST_DIGEST not in images_with_layers
    assert test_data.MANIFEST_LIST_ATTESTATION_DIGEST not in images_with_layers

    # Verify CONTAINS_IMAGE relationships from manifest list to platform images
    assert check_rels(
        neo4j_session,
        "AWSECRImage",
        "digest",
        "AWSECRImage",
        "digest",
        "CONTAINS_IMAGE",
        rel_direction_right=True,
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, test_data.MANIFEST_LIST_AMD64_DIGEST),
        (test_data.MANIFEST_LIST_DIGEST, test_data.MANIFEST_LIST_ARM64_DIGEST),
    }

    # Verify ATTESTS relationships from attestations to images they validate
    attests_rels = check_rels(
        neo4j_session,
        "AWSECRImage",
        "digest",
        "AWSECRImage",
        "digest",
        "ATTESTS",
        rel_direction_right=True,
    )
    # Attestation should point to the AMD64 image (as defined in test data)
    assert (
        test_data.MANIFEST_LIST_ATTESTATION_DIGEST,
        test_data.MANIFEST_LIST_AMD64_DIGEST,
    ) in attests_rels
