import asyncio
import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pytest
from botocore.exceptions import ClientError

import cartography.intel.aws.ecr_image_layers as ecr_layers
import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr_image_layers import batch_get_manifest
from cartography.intel.aws.ecr_image_layers import ECRLayerFetchTransientError
from cartography.intel.aws.ecr_image_layers import extract_repo_uri_from_image_uri
from cartography.intel.aws.ecr_image_layers import fetch_image_layers_async
from cartography.intel.aws.ecr_image_layers import get_blob_json_via_presigned
from cartography.intel.aws.ecr_image_layers import transform_ecr_image_layers
from cartography.intel.supply_chain import extract_workflow_path_from_ref


def test_load_ecr_image_layers_flattens_relationships(monkeypatch):
    load_mock = MagicMock()
    monkeypatch.setattr(ecr_layers, "load", load_mock)

    layers = [
        {
            "diff_id": "sha256:layer-1",
            "is_empty": False,
            "next_diff_ids": ["sha256:layer-2", "sha256:layer-3"],
            "head_image_ids": ["sha256:image-1"],
            "tail_image_ids": ["sha256:image-2"],
        },
        {
            "diff_id": "sha256:layer-2",
            "is_empty": False,
        },
    ]

    ecr_layers.load_ecr_image_layers(
        MagicMock(),
        layers,
        "us-east-1",
        "123456789012",
        123,
    )

    node_call, next_call, head_call, tail_call = load_mock.call_args_list
    assert node_call.args[1].__class__.__name__ == "ECRImageLayerNodeSchema"
    assert node_call.kwargs["batch_size"] == ecr_layers.ECR_LAYER_BATCH_SIZE
    assert next_call.args[1].__class__.__name__ == "ECRImageLayerNextRelSchema"
    assert next_call.args[2] == [
        {"diff_id": "sha256:layer-1", "next_diff_ids": ["sha256:layer-2"]},
        {"diff_id": "sha256:layer-1", "next_diff_ids": ["sha256:layer-3"]},
    ]
    assert head_call.args[1].__class__.__name__ == "ECRImageLayerHeadRelSchema"
    assert head_call.args[2] == [
        {"head_image_ids": ["sha256:image-1"], "diff_id": "sha256:layer-1"},
    ]
    assert tail_call.args[1].__class__.__name__ == "ECRImageLayerTailRelSchema"
    assert tail_call.args[2] == [
        {"tail_image_ids": ["sha256:image-2"], "diff_id": "sha256:layer-1"},
    ]
    assert all(
        call.kwargs["batch_size"] == ecr_layers.ECR_LAYER_REL_BATCH_SIZE
        for call in load_mock.call_args_list[1:]
    )


def test_load_ecr_image_layer_memberships_flattens_has_layer(monkeypatch):
    load_mock = MagicMock()
    monkeypatch.setattr(ecr_layers, "load", load_mock)

    memberships = [
        {
            "imageDigest": "sha256:image-1",
            "layer_diff_ids": ["sha256:layer-1", "sha256:layer-2"],
        },
        {
            "imageDigest": "sha256:image-2",
            "layer_diff_ids": ["sha256:layer-3"],
        },
    ]

    ecr_layers.load_ecr_image_layer_memberships(
        MagicMock(),
        memberships,
        "us-east-1",
        "123456789012",
        123,
    )

    enrichment_call = load_mock.call_args_list[0]
    has_layer_call = load_mock.call_args_list[1]
    assert enrichment_call.args[1].__class__.__name__ == "ECRImageLayerEnrichmentSchema"
    assert enrichment_call.kwargs["batch_size"] == ecr_layers.ECR_LAYER_BATCH_SIZE
    assert has_layer_call.args[1].__class__.__name__ == "ECRImageHasLayerRelSchema"
    assert has_layer_call.args[2] == [
        {"imageDigest": "sha256:image-1", "layer_diff_ids": ["sha256:layer-1"]},
        {"imageDigest": "sha256:image-1", "layer_diff_ids": ["sha256:layer-2"]},
        {"imageDigest": "sha256:image-2", "layer_diff_ids": ["sha256:layer-3"]},
    ]
    assert has_layer_call.kwargs["batch_size"] == ecr_layers.ECR_LAYER_REL_BATCH_SIZE


def test_cleanup_runs_layer_cleanup_job(monkeypatch):
    from_node_schema_mock = MagicMock(return_value=MagicMock())
    run_write_query_mock = MagicMock()
    monkeypatch.setattr(
        ecr_layers.GraphJob,
        "from_node_schema",
        from_node_schema_mock,
    )
    monkeypatch.setattr(ecr_layers, "run_write_query", run_write_query_mock)

    neo4j_session = MagicMock()
    ecr_layers.cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": 123,
            "AWS_ID": "123456789012",
        },
    )

    assert from_node_schema_mock.call_args.args[0].__class__.__name__ == (
        "ECRImageLayerSchema"
    )
    assert from_node_schema_mock.return_value.run.call_count == 1
    relationship_cleanup_query = run_write_query_mock.call_args.args[1]
    assert "HAS_LAYER|BUILT_FROM" in relationship_cleanup_query
    assert "DELETE relationship" in relationship_cleanup_query
    assert "DETACH DELETE" not in relationship_cleanup_query


def test_cleanup_skips_all_writes_when_fetch_incomplete(monkeypatch):
    from_node_schema_mock = MagicMock()
    run_write_query_mock = MagicMock()
    monkeypatch.setattr(
        ecr_layers.GraphJob,
        "from_node_schema",
        from_node_schema_mock,
    )
    monkeypatch.setattr(ecr_layers, "run_write_query", run_write_query_mock)

    ecr_layers.cleanup(
        MagicMock(),
        {"UPDATE_TAG": 123, "AWS_ID": "123456789012"},
        fetch_complete=False,
    )

    run_write_query_mock.assert_not_called()
    from_node_schema_mock.assert_not_called()


def test_extract_circleci_label_provenance_normalizes_namespaced_labels():
    config_json = {
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/service.git",
                "com.example.CIRCLE_SHA1": "abcdef0123456789abcdef0123456789abcdef01",
                "com.example.DOCKERFILE": "deploy/Dockerfile",
            }
        }
    }

    assert ecr_layers._extract_circleci_label_provenance(config_json) == {
        "source_uri": "https://github.com/ExampleOrg/service",
        "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
        "source_file": "deploy/Dockerfile",
    }


def test_extract_ci_label_provenance_reads_codebuild_variables():
    config_json = {
        "config": {
            "Labels": {
                "CODEBUILD_SOURCE_REPO_URL": "https://github.com/ExampleOrg/service.git",
                "CODEBUILD_RESOLVED_SOURCE_VERSION": "abcdef0123456789abcdef0123456789abcdef01",
            }
        }
    }

    assert ecr_layers._extract_ci_label_provenance(config_json) == {
        "source_uri": "https://github.com/ExampleOrg/service",
        "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
    }


def test_extract_ci_label_provenance_prefers_circleci_labels():
    config_json = {
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/service.git",
                "CODEBUILD_SOURCE_REPO_URL": "https://github.com/ExampleOrg/other.git",
            }
        }
    }

    assert ecr_layers._extract_ci_label_provenance(config_json) == {
        "source_uri": "https://github.com/ExampleOrg/service",
    }


def test_extract_circleci_label_provenance_ignores_empty_or_missing_labels():
    config_json = {
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "",
                "com.example.CIRCLE_SHA1": "   ",
                "com.example.UNRELATED": "value",
            }
        }
    }

    assert ecr_layers._extract_circleci_label_provenance(config_json) == {}


def test_extract_circleci_label_provenance_skips_ambiguous_suffix_labels(caplog):
    config_json = {
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/service.git",
                "io.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/other.git",
                "com.example.CIRCLE_SHA1": "abcdef0123456789abcdef0123456789abcdef01",
            }
        }
    }

    with caplog.at_level(logging.WARNING):
        assert ecr_layers._extract_circleci_label_provenance(config_json) == {
            "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
        }

    assert "multiple label keys matched by suffix" in caplog.text


def test_extract_circleci_label_provenance_ignores_empty_duplicate_suffix_labels():
    config_json = {
        "config": {
            "Labels": {
                "com.example.CIRCLE_SHA1": "",
                "io.example.CIRCLE_SHA1": "abcdef0123456789abcdef0123456789abcdef01",
            }
        }
    }

    assert ecr_layers._extract_circleci_label_provenance(config_json) == {
        "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
    }


def test_extract_circleci_label_provenance_ignores_dockerfile_without_circleci_signal():
    config_json = {
        "config": {
            "Labels": {
                "com.example.DOCKERFILE": "deploy/Dockerfile",
            }
        }
    }

    assert ecr_layers._extract_circleci_label_provenance(config_json) == {}


def test_normalize_git_repository_url_strips_https_git_suffix():
    assert (
        ecr_layers._normalize_git_repository_url(
            "https://github.com/ExampleOrg/service.git"
        )
        == "https://github.com/ExampleOrg/service"
    )


def test_label_provenance_does_not_override_attestation_provenance():
    provenance_by_key = {
        "sha256:image": {
            "source_uri": "https://github.com/ExampleOrg/attested",
            "source_revision": "attested-revision",
        }
    }

    ecr_layers._merge_provenance(
        provenance_by_key,
        "sha256:image",
        {
            "source_uri": "https://github.com/ExampleOrg/label",
            "source_revision": "label-revision",
            "source_file": "Dockerfile",
        },
        fallback=True,
    )

    assert provenance_by_key["sha256:image"] == {
        "source_uri": "https://github.com/ExampleOrg/attested",
        "source_revision": "attested-revision",
        "source_file": "Dockerfile",
    }


def test_attestation_provenance_survives_later_label_merge():
    provenance_by_key = {
        "image-uri": {
            ecr_layers.ATTESTATION_PROVENANCE_FIELD: True,
            "parent_image_digest": "sha256:attested-parent",
            "source_uri": "https://github.com/exampleorg/attested",
        }
    }

    ecr_layers._merge_provenance(
        provenance_by_key,
        "image-uri",
        {
            "source_uri": "https://github.com/exampleorg/label",
            "source_revision": "label-revision",
        },
        fallback=True,
    )

    assert provenance_by_key["image-uri"] == {
        ecr_layers.ATTESTATION_PROVENANCE_FIELD: True,
        "parent_image_digest": "sha256:attested-parent",
        "source_uri": "https://github.com/exampleorg/attested",
        "source_revision": "label-revision",
    }


@pytest.mark.parametrize(
    "input_uri,expected_repo_uri",
    [
        # Digest-based URI
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo@sha256:abcdef123456789",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # Tag-based URI
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo:v1.0.0",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # No tag or digest
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # Complex repository name with slashes
        (
            "123456789.dkr.ecr.us-west-2.amazonaws.com/team/service/component:latest",
            "123456789.dkr.ecr.us-west-2.amazonaws.com/team/service/component",
        ),
        # Tag with multiple colons in name
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/namespace/my-repo:v1.0.0",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/namespace/my-repo",
        ),
        # Port in tag (edge case)
        (
            "123456789.dkr.ecr.eu-west-1.amazonaws.com/app:build-123",
            "123456789.dkr.ecr.eu-west-1.amazonaws.com/app",
        ),
        # Edge cases
        # Empty string
        ("", ""),
        # Only digest marker (malformed)
        ("@sha256:", ""),
        # Only colon (malformed)
        (":", ""),
        # Multiple @ symbols (should split on first)
        ("repo@sha256:abc@def", "repo"),
        # Mixed digest and tag markers (digest takes precedence)
        ("repo@sha256:abc:tag", "repo"),
    ],
)
def test_extract_repo_uri_from_image_uri(input_uri, expected_repo_uri):
    """Test the extract_repo_uri_from_image_uri helper function."""
    actual_repo_uri = extract_repo_uri_from_image_uri(input_uri)
    assert actual_repo_uri == expected_repo_uri


def test_transform_ecr_image_layers_missing_digest_fails():
    """Test that transform_ecr_image_layers fails when digest is missing from map."""
    image_layers_data = {"repo/image:tag": {"linux/amd64": ["sha256:layer1"]}}
    image_digest_map = {}  # Missing the digest mapping

    # Should raise KeyError since we use direct dictionary access
    with pytest.raises(KeyError):
        transform_ecr_image_layers(image_layers_data, image_digest_map)


def test_transform_ecr_image_layers_empty_input():
    """Test transform_ecr_image_layers with empty input."""
    layers, memberships = transform_ecr_image_layers({}, {})

    assert layers == []
    assert memberships == []


@pytest.mark.parametrize("error_code", ["AccessDenied", "AccessDeniedException"])
def test_batch_get_manifest_access_denied_returns_empty_result(error_code):
    """Test that access-denied errors are non-fatal when fetching manifests."""
    mock_ecr_client = AsyncMock()
    mock_ecr_client.batch_get_image.side_effect = ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "Not authorized to perform ecr:BatchGetImage",
            }
        },
        "BatchGetImage",
    )

    manifest, media_type = asyncio.run(
        batch_get_manifest(
            mock_ecr_client,
            "example/repository",
            "sha256:12345",
            ["application/vnd.oci.image.manifest.v1+json"],
        )
    )

    assert manifest == {}
    assert media_type == ""


def test_batch_get_manifest_transient_aws_error_raises_skip_signal():
    mock_ecr_client = AsyncMock()
    mock_ecr_client.batch_get_image.side_effect = ClientError(
        {
            "Error": {
                "Code": "ServiceUnavailableException",
                "Message": "Try again later",
            },
            "ResponseMetadata": {"HTTPStatusCode": 503},
        },
        "BatchGetImage",
    )

    with pytest.raises(ECRLayerFetchTransientError):
        asyncio.run(
            batch_get_manifest(
                mock_ecr_client,
                "example/repository",
                "sha256:12345",
                ["application/vnd.oci.image.manifest.v1+json"],
            )
        )


def test_get_blob_json_via_presigned_retries_remote_protocol_error(mocker):
    mock_ecr_client = AsyncMock()
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.com/blob"
    }

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"value": "ok"}

    http_client = AsyncMock()
    http_client.get.side_effect = [
        httpx.RemoteProtocolError("Server disconnected without sending a response."),
        response,
    ]

    sleep = mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    result = asyncio.run(
        get_blob_json_via_presigned(
            mock_ecr_client,
            "example/repository",
            "sha256:12345",
            http_client,
        )
    )

    assert result == {"value": "ok"}
    assert http_client.get.await_count == 2
    sleep.assert_awaited_once()


def test_get_blob_json_via_presigned_raises_skip_signal_after_retry_exhaustion(mocker):
    mock_ecr_client = AsyncMock()
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.com/blob"
    }

    http_client = AsyncMock()
    http_client.get.side_effect = [
        httpx.ReadError("boom"),
        httpx.ReadError("boom"),
        httpx.ReadError("boom"),
    ]

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    with pytest.raises(ECRLayerFetchTransientError):
        asyncio.run(
            get_blob_json_via_presigned(
                mock_ecr_client,
                "example/repository",
                "sha256:12345",
                http_client,
            )
        )


def test_get_blob_json_via_presigned_redacts_presigned_url_in_http_status_logs(
    mocker, caplog
):
    mock_ecr_client = AsyncMock()
    signed_url = "https://example.com/blob?X-Amz-Signature=SECRET&X-Amz-Credential=ABC"
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": signed_url
    }

    request = httpx.Request("GET", signed_url)
    response = httpx.Response(503, request=request)
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        response.raise_for_status()
    status_error = excinfo.value

    http_client = AsyncMock()
    http_client.get.side_effect = [status_error, status_error, status_error]

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ECRLayerFetchTransientError):
            asyncio.run(
                get_blob_json_via_presigned(
                    mock_ecr_client,
                    "example/repository",
                    "sha256:12345",
                    http_client,
                )
            )

    assert "X-Amz-Signature" not in caplog.text
    assert "HTTPStatusError(status_code=503)" in caplog.text


def test_fetch_image_layers_async_skips_only_transient_image_failure(mocker):
    repo_uri = "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    repo_images_list = [
        {
            "uri": f"{repo_uri}:bad",
            "imageDigest": "sha256:bad",
            "repo_uri": repo_uri,
        },
        {
            "uri": f"{repo_uri}:good",
            "imageDigest": "sha256:good",
            "repo_uri": repo_uri,
        },
    ]

    async def mock_batch_get_manifest(_client, _repo, image_ref, _accepted):
        if image_ref == "sha256:bad":
            raise ECRLayerFetchTransientError("temporary failure")
        return (
            test_data.SAMPLE_MANIFEST,
            "application/vnd.docker.distribution.manifest.v2+json",
        )

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.batch_get_manifest",
        side_effect=mock_batch_get_manifest,
    )
    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
        new=AsyncMock(return_value=test_data.SAMPLE_CONFIG_BLOB),
    )

    (
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
        image_attestation_map,
        fetch_complete,
    ) = asyncio.run(
        fetch_image_layers_async(
            AsyncMock(),
            repo_images_list,
            max_concurrent=2,
        )
    )

    assert f"{repo_uri}:bad" not in image_layers_data
    assert f"{repo_uri}:good" in image_layers_data
    assert image_digest_map == {f"{repo_uri}:good": "sha256:good"}
    assert isinstance(history_by_diff_id, dict)
    assert image_attestation_map == {}
    assert fetch_complete is False


@pytest.mark.asyncio
async def test_fetch_image_layers_async_cancels_siblings_on_unexpected_failure(mocker):
    repo_uri = "111122223333.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    repo_images_list = [
        {
            "uri": f"{repo_uri}:slow",
            "imageDigest": "sha256:slow",
            "repo_uri": repo_uri,
        },
        {
            "uri": f"{repo_uri}:invalid",
            "imageDigest": "sha256:invalid",
            "repo_uri": repo_uri,
        },
    ]
    slow_started = asyncio.Event()
    slow_cancelled = asyncio.Event()

    async def mock_batch_get_manifest(_client, _repo, image_ref, _accepted):
        if image_ref == "sha256:slow":
            slow_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                slow_cancelled.set()
                raise
        await slow_started.wait()
        raise ClientError(
            {
                "Error": {
                    "Code": "InvalidClientTokenId",
                    "Message": "Synthetic AWS client error",
                },
            },
            "AssumeRole",
        )

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.batch_get_manifest",
        side_effect=mock_batch_get_manifest,
    )

    with pytest.raises(ClientError):
        await fetch_image_layers_async(
            AsyncMock(),
            repo_images_list,
            max_concurrent=2,
        )

    assert slow_cancelled.is_set()


def test_fetch_image_layers_async_discards_manifest_list_when_one_child_fails_transiently(
    mocker,
):
    """A transient child failure must discard all partial manifest-list data."""
    repo_uri = "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    repo_images_list = [
        {
            "uri": f"{repo_uri}:manifest-list",
            "imageDigest": "sha256:manifest-list",
            "repo_uri": repo_uri,
        },
    ]

    async def mock_batch_get_manifest(_client, _repo, image_ref, _accepted):
        if image_ref == "sha256:manifest-list":
            return (
                test_data.SAMPLE_MANIFEST_LIST,
                "application/vnd.docker.distribution.manifest.list.v2+json",
            )
        if (
            image_ref
            == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1"
        ):
            return (
                test_data.SAMPLE_MANIFEST,
                "application/vnd.docker.distribution.manifest.v2+json",
            )
        raise ECRLayerFetchTransientError("temporary child failure")

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.batch_get_manifest",
        side_effect=mock_batch_get_manifest,
    )
    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
        new=AsyncMock(return_value=test_data.SAMPLE_CONFIG_BLOB),
    )

    (
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
        image_attestation_map,
        fetch_complete,
    ) = asyncio.run(
        fetch_image_layers_async(
            AsyncMock(),
            repo_images_list,
            max_concurrent=4,
        )
    )

    assert image_layers_data == {}
    assert image_digest_map == {}
    assert history_by_diff_id == {}
    assert image_attestation_map == {}
    assert fetch_complete is False


@pytest.mark.asyncio
async def test_extract_provenance_from_attestation_supports_slsa_v1():
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:intoto"}
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
                        "uri": "pkg:docker/111111111111.dkr.ecr.us-east-1.amazonaws.com/example-base@v1?platform=linux%2Famd64",
                        "digest": {
                            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                        },
                    },
                    {
                        "uri": "pkg:docker/docker/dockerfile@1.9",
                        "digest": {
                            "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                        },
                    },
                ],
                "externalParameters": {
                    "configSource": {"path": "Dockerfile.custom"},
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
                            "localdir:dockerfile": "services/backend",
                        },
                    },
                },
            },
        },
    }

    original_batch_get_manifest = ecr_layers.batch_get_manifest
    original_get_blob = ecr_layers.get_blob_json_via_presigned
    ecr_layers.batch_get_manifest = AsyncMock(return_value=attestation_manifest)
    ecr_layers.get_blob_json_via_presigned = AsyncMock(return_value=attestation_blob)

    try:
        result = await ecr_layers._extract_provenance_from_attestation(
            mock_ecr_client,
            "example-repository",
            "sha256:attestation",
            mock_http_client,
        )
    finally:
        ecr_layers.batch_get_manifest = original_batch_get_manifest
        ecr_layers.get_blob_json_via_presigned = original_get_blob

    assert result is not None
    assert (
        result["parent_image_uri"]
        == "pkg:docker/111111111111.dkr.ecr.us-east-1.amazonaws.com/example-base@v1?platform=linux%2Famd64"
    )
    assert (
        result["parent_image_digest"]
        == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert result["source_uri"] == "https://github.com/exampleco/example-repo"
    assert result["source_revision"] == "abcdef0123456789abcdef0123456789abcdef01"
    assert result["invocation_uri"] == "https://github.com/exampleco/example-repo"
    assert result["source_file"] == "services/backend/Dockerfile.custom"


def test_transform_layers_creates_graph_structure():
    """Test that transform creates proper graph structure from layer data."""
    # Test images sharing base layers (common in Docker)
    image_layers_data = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/web-app:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # base OS layer
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # runtime layer
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",  # app-specific
            ]
        },
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/api-service:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # shared base
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # shared runtime
                "sha256:4444444444444444444444444444444444444444444444444444444444444444",  # api-specific
            ]
        },
    }

    image_digest_map = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/web-app:v1": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/api-service:v1": "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Should have 4 unique layers (2 shared, 2 unique)
    assert len(layers) == 4

    # Base layer should be HEAD of both images
    base_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:1111111111111111111111111111111111111111111111111111111111111111"
    )
    assert len(base_layer["head_image_ids"]) == 2
    assert (
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
        in base_layer["head_image_ids"]
    )
    assert (
        "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
        in base_layer["head_image_ids"]
    )
    # Base layer should have NEXT pointing to runtime layer
    assert base_layer["next_diff_ids"] == [
        "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    ]

    # Runtime layer should have NEXT pointing to both app-specific layers (divergence point)
    runtime_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    )
    assert set(runtime_layer["next_diff_ids"]) == {
        "sha256:3333333333333333333333333333333333333333333333333333333333333333",
        "sha256:4444444444444444444444444444444444444444444444444444444444444444",
    }
    # No duplicated NEXT entries for the shared layer
    assert len(runtime_layer["next_diff_ids"]) == 2

    # App-specific layers should be TAIL of their respective images
    web_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:3333333333333333333333333333333333333333333333333333333333333333"
    )
    assert web_layer["tail_image_ids"] == [
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    ]

    api_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:4444444444444444444444444444444444444444444444444444444444444444"
    )
    assert api_layer["tail_image_ids"] == [
        "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
    ]
    # TAIL layers should have no NEXT relationships
    assert "next_diff_ids" not in web_layer
    assert "next_diff_ids" not in api_layer

    # Memberships should correspond to both images' layer sequences
    expected_memberships = {
        (
            "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
            (
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            ),
        ),
        (
            "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
            (
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:4444444444444444444444444444444444444444444444444444444444444444",
            ),
        ),
    }

    observed_memberships = {
        (m["imageDigest"], tuple(m["layer_diff_ids"])) for m in memberships
    }
    assert observed_memberships == expected_memberships


def test_transform_ecr_image_layers_with_attestation_data():
    """Test that attestation data is correctly added to memberships."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    image_attestation_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            ecr_layers.ATTESTATION_PROVENANCE_FIELD: True,
            "parent_image_uri": "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-images@abc123",
            "parent_image_digest": "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
        }
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        None,  # history_by_diff_id
        image_attestation_map,
    )

    # Should have 2 layers
    assert len(layers) == 2

    # Should have 1 membership with attestation data
    assert len(memberships) == 1
    membership = memberships[0]

    assert (
        membership["imageDigest"]
        == "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    )
    assert len(membership["layer_diff_ids"]) == 2
    assert (
        membership["parent_image_uri"]
        == "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-images@abc123"
    )
    assert (
        membership["parent_image_digest"]
        == "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
    )
    assert membership["from_attestation"] is True
    assert membership["confidence"] == "explicit"


def test_transform_ecr_image_layers_marks_source_only_attestation_provenance():
    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest"
    image_digest = (
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    )
    layers, memberships = transform_ecr_image_layers(
        {
            image_uri: {
                "linux/amd64": [
                    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
                ]
            }
        },
        {image_uri: image_digest},
        image_attestation_map={
            image_uri: {
                ecr_layers.ATTESTATION_PROVENANCE_FIELD: True,
                "source_uri": "https://github.com/exampleorg/service",
                "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
            }
        },
    )

    assert len(layers) == 1
    assert memberships == [
        {
            "imageDigest": image_digest,
            "layer_diff_ids": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111"
            ],
            "source_uri": "https://github.com/exampleorg/service",
            "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
            "from_attestation": True,
            "confidence": "explicit",
        }
    ]


def test_transform_ecr_image_layers_applies_new_provenance_to_skipped_image():
    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend@sha256:image"

    layers, memberships = transform_ecr_image_layers(
        {},
        {image_uri: "sha256:image"},
        image_attestation_map={
            image_uri: {
                ecr_layers.ATTESTATION_PROVENANCE_FIELD: True,
                "source_uri": "https://github.com/example/service",
            },
        },
        existing_properties_map={
            "sha256:image": {
                "type": "image",
                "layer_diff_ids": ["sha256:layer"],
                "source_revision": "existing-revision",
                "source_file": "Dockerfile",
                "invocation_uri": "https://github.com/example/actions/runs/1",
                "invocation_workflow": ".github/workflows/build.yml",
                "invocation_run_number": "1",
                "parent_image_digest": "sha256:parent",
                "parent_image_uri": "docker.io/library/alpine:3",
                "from_attestation": True,
                "confidence": "explicit",
            },
        },
    )

    assert layers == []
    assert memberships == [
        {
            "imageDigest": "sha256:image",
            "type": "image",
            "layer_diff_ids": ["sha256:layer"],
            "source_uri": "https://github.com/example/service",
            "source_revision": "existing-revision",
            "source_file": "Dockerfile",
            "invocation_uri": "https://github.com/example/actions/runs/1",
            "invocation_workflow": ".github/workflows/build.yml",
            "invocation_run_number": "1",
            "parent_image_digest": "sha256:parent",
            "parent_image_uri": "docker.io/library/alpine:3",
            "from_attestation": True,
            "confidence": "explicit",
        },
    ]


def test_transform_ecr_image_layers_without_attestation_data():
    """Test that transform works without attestation data (backward compatibility)."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    # No attestation map provided
    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Should work without errors
    assert len(layers) == 1
    assert len(memberships) == 1

    membership = memberships[0]
    # Should NOT have parent_image_uri or parent_image_digest
    assert "parent_image_uri" not in membership
    assert "parent_image_digest" not in membership


def test_transform_ecr_image_layers_with_history():
    """Test that history commands are correctly added to layers."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    history_by_diff_id = {
        "sha256:1111111111111111111111111111111111111111111111111111111111111111": "/bin/sh -c #(nop) ADD file:abc123 in /",
        "sha256:2222222222222222222222222222222222222222222222222222222222222222": "/bin/sh -c apt-get update && apt-get install -y python3",
        "sha256:3333333333333333333333333333333333333333333333333333333333333333": "/bin/sh -c #(nop) COPY dir:xyz789 in /app",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
    )

    # Should have 3 layers
    assert len(layers) == 3

    # Each layer should have its history command
    for layer in layers:
        diff_id = layer["diff_id"]
        assert "history" in layer, f"Layer {diff_id} should have history"
        assert layer["history"] == history_by_diff_id[diff_id]


def test_transform_ecr_image_layers_with_partial_history():
    """Test that layers without history in the map don't get a history field."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    # Only first layer has history
    history_by_diff_id = {
        "sha256:1111111111111111111111111111111111111111111111111111111111111111": "/bin/sh -c #(nop) ADD file:abc123 in /",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
    )

    # Should have 2 layers
    assert len(layers) == 2

    # Find each layer
    layer1 = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:1111111111111111111111111111111111111111111111111111111111111111"
    )
    layer2 = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    )

    # First layer should have history
    assert "history" in layer1
    assert layer1["history"] == "/bin/sh -c #(nop) ADD file:abc123 in /"

    # Second layer should NOT have history field (not in map)
    assert "history" not in layer2


@pytest.mark.parametrize(
    "workflow_ref,expected_path",
    [
        # Standard GitHub workflow ref
        (
            "subimagesec/subimage/.github/workflows/docker-push-subimage.yaml@refs/pull/1042/merge",
            ".github/workflows/docker-push-subimage.yaml",
        ),
        # Workflow ref with refs/heads/main
        (
            "owner/repo/.github/workflows/build.yaml@refs/heads/main",
            ".github/workflows/build.yaml",
        ),
        # Workflow ref with tag
        (
            "myorg/myrepo/.github/workflows/release.yml@refs/tags/v1.0.0",
            ".github/workflows/release.yml",
        ),
        # Nested workflow path
        (
            "org/repo/ci/workflows/test.yaml@refs/heads/develop",
            "ci/workflows/test.yaml",
        ),
        # Empty string
        ("", None),
        # None value
        (None, None),
        # No @ suffix (edge case)
        (
            "owner/repo/.github/workflows/build.yaml",
            ".github/workflows/build.yaml",
        ),
    ],
)
def testextract_workflow_path_from_ref(workflow_ref, expected_path):
    """Test extracting workflow path from GitHub workflow ref."""
    assert extract_workflow_path_from_ref(workflow_ref) == expected_path


def _credential_error(error_code: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": error_code, "Message": "Synthetic credential error"}},
        "GetDownloadUrlForLayer",
    )


def _stub_sync_dependencies(mocker, sessions_seen: list) -> None:
    """
    Neutralize everything sync() touches around the credential-retry loop so the tests
    only exercise that loop.
    """
    mocker.patch.object(
        ecr_layers,
        "get_complete_layer_digests",
        return_value=set(),
    )
    mocker.patch.object(
        ecr_layers,
        "partition_layer_fetches",
        side_effect=lambda images, complete, digest_key: (images, []),
    )
    mocker.patch.object(ecr_layers, "refresh_layer_closures")
    mocker.patch.object(
        ecr_layers,
        "transform_ecr_image_layers",
        return_value=([], []),
    )
    mocker.patch.object(ecr_layers, "load_ecr_image_layers")
    mocker.patch.object(ecr_layers, "load_ecr_image_layer_memberships")
    mocker.patch.object(ecr_layers, "cleanup")

    class _FakeClientContext:
        def __init__(self, session):
            sessions_seen.append(session)

        async def __aenter__(self):
            return AsyncMock()

        async def __aexit__(self, *_args):
            return False

    mocker.patch.object(
        ecr_layers,
        "create_aioboto3_client",
        side_effect=lambda session, _service, **_kwargs: _FakeClientContext(session),
    )


def _neo4j_session_with_one_image() -> MagicMock:
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = [
        {
            "digest": "sha256:aaa",
            "uri": "1234.dkr.ecr.us-east-1.amazonaws.com/repo@sha256:aaa",
            "repo_uri": "1234.dkr.ecr.us-east-1.amazonaws.com/repo",
            "type": "image",
        }
    ]
    return neo4j_session


def _run_sync(neo4j_session, session_factory=None, initial_session="session-0"):
    ecr_layers.sync(
        neo4j_session,
        initial_session,
        ["us-east-1"],
        "1234",
        123456789,
        {"UPDATE_TAG": 123456789, "AWS_ID": "1234"},
        aioboto3_session_factory=session_factory,
    )


@pytest.mark.parametrize(
    "error_code",
    [
        "ExpiredToken",
        "ExpiredTokenException",
        "InvalidClientTokenId",
        "RequestExpired",
    ],
)
def test_sync_retries_with_fresh_session_on_credential_error(mocker, error_code):
    sessions_seen: list = []
    _stub_sync_dependencies(mocker, sessions_seen)
    fetch_mock = mocker.patch.object(
        ecr_layers,
        "fetch_image_layers_async",
        side_effect=[
            _credential_error(error_code),
            ({}, {}, {}, {}, True),
        ],
    )
    factory = MagicMock(return_value="session-refreshed")

    _run_sync(_neo4j_session_with_one_image(), session_factory=factory)

    assert fetch_mock.call_count == 2
    factory.assert_called_once_with()
    assert sessions_seen == ["session-0", "session-refreshed"]
    # The region completed, so cleanup is allowed to delete stale layers.
    assert ecr_layers.cleanup.call_args.kwargs["fetch_complete"] is True


def test_sync_raises_when_credential_retry_budget_is_exhausted(mocker):
    sessions_seen: list = []
    _stub_sync_dependencies(mocker, sessions_seen)
    fetch_mock = mocker.patch.object(
        ecr_layers,
        "fetch_image_layers_async",
        side_effect=[
            _credential_error("ExpiredTokenException"),
            _credential_error("ExpiredTokenException"),
        ],
    )
    factory = MagicMock(return_value="session-refreshed")

    with pytest.raises(ClientError) as excinfo:
        _run_sync(_neo4j_session_with_one_image(), session_factory=factory)

    assert excinfo.value.response["Error"]["Code"] == "ExpiredTokenException"
    assert fetch_mock.call_count == 2
    factory.assert_called_once_with()
    ecr_layers.cleanup.assert_not_called()


def test_sync_raises_credential_error_when_no_session_factory(mocker):
    sessions_seen: list = []
    _stub_sync_dependencies(mocker, sessions_seen)
    fetch_mock = mocker.patch.object(
        ecr_layers,
        "fetch_image_layers_async",
        side_effect=_credential_error("ExpiredTokenException"),
    )

    with pytest.raises(ClientError) as excinfo:
        _run_sync(_neo4j_session_with_one_image(), session_factory=None)

    assert excinfo.value.response["Error"]["Code"] == "ExpiredTokenException"
    assert fetch_mock.call_count == 1
    ecr_layers.cleanup.assert_not_called()


def test_sync_does_not_retry_non_credential_client_error(mocker):
    sessions_seen: list = []
    _stub_sync_dependencies(mocker, sessions_seen)
    fetch_mock = mocker.patch.object(
        ecr_layers,
        "fetch_image_layers_async",
        side_effect=_credential_error("AccessDeniedException"),
    )
    factory = MagicMock(return_value="session-refreshed")

    with pytest.raises(ClientError) as excinfo:
        _run_sync(_neo4j_session_with_one_image(), session_factory=factory)

    assert excinfo.value.response["Error"]["Code"] == "AccessDeniedException"
    assert fetch_mock.call_count == 1
    factory.assert_not_called()


def test_transform_marks_empty_layer():
    layers, _ = ecr_layers.transform_ecr_image_layers(
        {
            "repo/image:tag": {
                "linux/amd64": [
                    ecr_layers.EMPTY_LAYER_DIFF_ID,
                    "sha256:abcdef0123456789",
                ],
            },
        },
        {"repo/image:tag": "sha256:image"},
    )

    empty_layer = next(
        layer for layer in layers if layer["diff_id"] == ecr_layers.EMPTY_LAYER_DIFF_ID
    )
    non_empty_layer = next(
        layer for layer in layers if layer["diff_id"] == "sha256:abcdef0123456789"
    )

    assert empty_layer["is_empty"] is True
    assert non_empty_layer["is_empty"] is False


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
    """Test extracting provenance from attestation with various URI schemes."""
    # Arrange
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

    original_batch_get_manifest = ecr_layers.batch_get_manifest
    original_get_blob = ecr_layers.get_blob_json_via_presigned

    ecr_layers.batch_get_manifest = AsyncMock(return_value=attestation_manifest)
    ecr_layers.get_blob_json_via_presigned = AsyncMock(return_value=attestation_blob)

    try:
        # Act
        result = await ecr_layers._extract_provenance_from_attestation(
            mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
        )

        # Assert
        assert result is not None
        assert result["parent_image_uri"] == parent_uri
        assert result["parent_image_digest"] == parent_digest
    finally:
        ecr_layers.batch_get_manifest = original_batch_get_manifest
        ecr_layers.get_blob_json_via_presigned = original_get_blob


@pytest.mark.asyncio
async def test_extract_provenance_from_attestation_with_source_info():
    """Test extracting full provenance including source repo and invocation info."""
    # Arrange
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

    # Full SLSA provenance attestation blob with VCS and invocation info
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
                    "github_repository": "subimagesec/subimage",
                    "github_workflow_ref": "subimagesec/subimage/.github/workflows/build.yaml@refs/heads/main",
                    "github_run_number": "1470",
                }
            },
            "metadata": {
                "https://mobyproject.org/buildkit@v1#metadata": {
                    "vcs": {
                        "source": "https://github.com/subimagesec/subimage",
                        "revision": "abc123def456",
                    }
                }
            },
        }
    }

    original_batch_get_manifest = ecr_layers.batch_get_manifest
    original_get_blob = ecr_layers.get_blob_json_via_presigned

    ecr_layers.batch_get_manifest = AsyncMock(return_value=attestation_manifest)
    ecr_layers.get_blob_json_via_presigned = AsyncMock(return_value=attestation_blob)

    try:
        # Act
        result = await ecr_layers._extract_provenance_from_attestation(
            mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
        )

        # Assert
        assert result is not None
        # Parent image info
        assert result["parent_image_uri"] == "pkg:docker/base-image@v1.0"
        assert result["parent_image_digest"] == "sha256:parentdigest123"
        # Source repository info
        assert result["source_uri"] == "https://github.com/subimagesec/subimage"
        assert result["source_revision"] == "abc123def456"
        # Build invocation info
        assert result["invocation_uri"] == "https://github.com/subimagesec/subimage"
        assert result["invocation_workflow"] == ".github/workflows/build.yaml"
        assert result["invocation_run_number"] == "1470"
        # Source file defaults to "Dockerfile" when no configSource.entryPoint
        assert result["source_file"] == "Dockerfile"
    finally:
        ecr_layers.batch_get_manifest = original_batch_get_manifest
        ecr_layers.get_blob_json_via_presigned = original_get_blob


@pytest.mark.asyncio
async def test_extract_provenance_source_file_with_config_source():
    """Test source_file extraction with configSource.entryPoint and vcs localdir:dockerfile."""
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

    original_batch_get_manifest = ecr_layers.batch_get_manifest
    original_get_blob = ecr_layers.get_blob_json_via_presigned

    ecr_layers.batch_get_manifest = AsyncMock(return_value=attestation_manifest)
    ecr_layers.get_blob_json_via_presigned = AsyncMock(return_value=attestation_blob)

    try:
        result = await ecr_layers._extract_provenance_from_attestation(
            mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
        )

        assert result is not None
        assert result["source_uri"] == "https://github.com/myorg/myrepo"
        assert result["source_file"] == "deploy/Dockerfile.prod"
    finally:
        ecr_layers.batch_get_manifest = original_batch_get_manifest
        ecr_layers.get_blob_json_via_presigned = original_get_blob


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
async def test_fetch_image_layers_async_handles_manifest_list(
    mock_batch_get_manifest,
    mock_get_blob_json,
):
    repo_image = {
        "uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:multi",
        "imageDigest": "sha256:indexdigest000000000000000000000000000000000000000000000000000000000000",
        "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared",
    }

    manifest_lookup = {
        repo_image["imageDigest"]: (
            test_data.MULTI_ARCH_INDEX,
            ecr_layers.ECR_OCI_INDEX_MT,
        ),
        "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": (
            test_data.MULTI_ARCH_AMD64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc": (
            test_data.MULTI_ARCH_ARM64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd": (
            test_data.ATTESTATION_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
    }

    def fake_batch_get_manifest(ecr_client, repo_name, image_ref, accepted_media_types):
        return manifest_lookup[image_ref]

    mock_batch_get_manifest.side_effect = fake_batch_get_manifest

    async def fake_get_blob_json(ecr_client, repo_name, digest, http_client):
        config_lookup = {
            test_data.MULTI_ARCH_AMD64_MANIFEST["config"][
                "digest"
            ]: test_data.MULTI_ARCH_AMD64_CONFIG,
            test_data.MULTI_ARCH_ARM64_MANIFEST["config"][
                "digest"
            ]: test_data.MULTI_ARCH_ARM64_CONFIG,
            # Attestation blob lookup
            "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456": test_data.SLSA_PROVENANCE_BLOB,
        }
        return config_lookup.get(digest, {})

    mock_get_blob_json.side_effect = fake_get_blob_json

    image_layers_data, digest_map, history_map, attestation_map, fetch_complete = (
        await ecr_layers.fetch_image_layers_async(
            MagicMock(),
            [repo_image],
            max_concurrent=1,
        )
    )

    # Verify platform layers are extracted
    assert image_layers_data == {
        repo_image["uri"]: {
            "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"]["diff_ids"],
        }
    }

    # Verify digest_map includes manifest list and child images
    assert repo_image["uri"] in digest_map
    assert digest_map[repo_image["uri"]] == repo_image["imageDigest"]

    # Verify history_map is populated (may be empty if test data doesn't include history)
    assert isinstance(history_map, dict)

    # Verify attestation data is extracted and mapped to child AMD64 image
    # The attestation in MULTI_ARCH_INDEX attests to the AMD64 image (line 108 of test_data)
    expected_child_uri = f"000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared@{test_data.MANIFEST_LIST_AMD64_DIGEST}"
    assert (
        expected_child_uri in attestation_map
    ), "Attestation data should be mapped to child image!"
    assert (
        attestation_map[expected_child_uri]["parent_image_digest"]
        == "sha256:parent1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    )
    # Verify child digest is in digest_map too
    assert digest_map[expected_child_uri] == test_data.MANIFEST_LIST_AMD64_DIGEST
    assert fetch_complete is True


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
async def test_fetch_image_layers_async_maps_manifest_child_label_provenance(
    mock_batch_get_manifest,
    mock_get_blob_json,
):
    repo_image = {
        "uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-service:multi",
        "imageDigest": test_data.MANIFEST_LIST_DIGEST,
        "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-service",
    }
    manifest_list = {
        **test_data.MULTI_ARCH_INDEX,
        "manifests": [
            manifest
            for manifest in test_data.MULTI_ARCH_INDEX["manifests"]
            if manifest.get("annotations", {}).get("vnd.docker.reference.type")
            != "attestation-manifest"
        ],
    }
    amd64_config = {
        **test_data.MULTI_ARCH_AMD64_CONFIG,
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/service.git",
                "com.example.CIRCLE_SHA1": "abcdef0123456789abcdef0123456789abcdef01",
                "com.example.DOCKERFILE": "Dockerfile",
            }
        },
    }
    arm64_config = {
        **test_data.MULTI_ARCH_ARM64_CONFIG,
        "config": {
            "Labels": {
                "com.example.CIRCLE_REPOSITORY_URL": "git@github.com:ExampleOrg/service.git",
                "com.example.CIRCLE_SHA1": "abcdef0123456789abcdef0123456789abcdef01",
                "com.example.DOCKERFILE": "Dockerfile",
            }
        },
    }

    manifest_lookup = {
        repo_image["imageDigest"]: (manifest_list, ecr_layers.ECR_OCI_INDEX_MT),
        test_data.MANIFEST_LIST_AMD64_DIGEST: (
            test_data.MULTI_ARCH_AMD64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        test_data.MANIFEST_LIST_ARM64_DIGEST: (
            test_data.MULTI_ARCH_ARM64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
    }

    def fake_batch_get_manifest(ecr_client, repo_name, image_ref, accepted_media_types):
        return manifest_lookup[image_ref]

    async def fake_get_blob_json(ecr_client, repo_name, digest, http_client):
        return {
            test_data.MULTI_ARCH_AMD64_MANIFEST["config"]["digest"]: amd64_config,
            test_data.MULTI_ARCH_ARM64_MANIFEST["config"]["digest"]: arm64_config,
        }.get(digest, {})

    mock_batch_get_manifest.side_effect = fake_batch_get_manifest
    mock_get_blob_json.side_effect = fake_get_blob_json

    image_layers_data, digest_map, _, provenance_map, fetch_complete = (
        await ecr_layers.fetch_image_layers_async(
            MagicMock(),
            [repo_image],
            max_concurrent=1,
        )
    )

    assert image_layers_data == {
        repo_image["uri"]: {
            "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"]["diff_ids"],
        }
    }
    assert repo_image["uri"] not in provenance_map
    expected_amd64_uri = (
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/"
        f"example-service@{test_data.MANIFEST_LIST_AMD64_DIGEST}"
    )
    expected_arm64_uri = (
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/"
        f"example-service@{test_data.MANIFEST_LIST_ARM64_DIGEST}"
    )
    assert digest_map[expected_amd64_uri] == test_data.MANIFEST_LIST_AMD64_DIGEST
    assert digest_map[expected_arm64_uri] == test_data.MANIFEST_LIST_ARM64_DIGEST
    assert provenance_map == {
        expected_amd64_uri: {
            "source_uri": "https://github.com/ExampleOrg/service",
            "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
            "source_file": "Dockerfile",
        },
        expected_arm64_uri: {
            "source_uri": "https://github.com/ExampleOrg/service",
            "source_revision": "abcdef0123456789abcdef0123456789abcdef01",
            "source_file": "Dockerfile",
        },
    }
    assert fetch_complete is True


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
async def test_fetch_image_layers_async_skips_attestation_only(
    mock_batch_get_manifest,
    mock_get_blob_json,
):
    repo_image = {
        "uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:attestation",
        "imageDigest": "sha256:attestationindex0000000000000000000000000000000000000000000000000000",
        "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared",
    }

    mock_batch_get_manifest.return_value = (
        test_data.ATTESTATION_MANIFEST,
        ecr_layers.ECR_OCI_MANIFEST_MT,
    )

    image_layers_data, digest_map, history_map, attestation_map, fetch_complete = (
        await ecr_layers.fetch_image_layers_async(
            MagicMock(),
            [repo_image],
            max_concurrent=1,
        )
    )

    assert image_layers_data == {}
    assert digest_map == {}
    assert history_map == {}
    assert fetch_complete is True
