import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError

from cartography.intel.gcp.artifact_registry.artifact import get_docker_images
from cartography.intel.gcp.artifact_registry.artifact import get_maven_artifacts
from cartography.intel.gcp.artifact_registry.artifact import get_npm_packages
from cartography.intel.gcp.artifact_registry.artifact import get_python_packages
from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.util import _load_with_progress
from cartography.intel.gcp.artifact_registry.util import ARTIFACT_REGISTRY_LIST_TIMEOUT
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import (
    load_nodes_without_relationships,
)


def _permission_denied_getter(client, repository_name):
    return None


def _unexpected_error_getter(client, repository_name):
    raise GoogleAPICallError("boom")


def _run_sync_with_cleanup_mocks(monkeypatch, getter):
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
        {"DOCKER": (getter, transform_docker_images)},
    )

    with (
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.sync_docker_images"
        ) as sync_docker_images,
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.cleanup_helm_charts"
        ) as cleanup_helm_charts,
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.cleanup_language_packages"
        ) as cleanup_language_packages,
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.cleanup_generic_artifacts"
        ) as cleanup_generic_artifacts,
    ):
        result = sync_artifact_registry_artifacts(
            MagicMock(),
            MagicMock(),
            [{"name": "repo", "format": "DOCKER"}],
            "test-project",
            123,
            {"UPDATE_TAG": 123},
            max_workers=1,
        )

    return (
        result,
        sync_docker_images,
        cleanup_helm_charts,
        cleanup_language_packages,
        cleanup_generic_artifacts,
    )


def test_sync_artifact_registry_artifacts_skips_cleanup_when_repository_incomplete(
    monkeypatch,
):
    (
        result,
        sync_docker_images,
        cleanup_helm_charts,
        cleanup_language_packages,
        cleanup_generic_artifacts,
    ) = _run_sync_with_cleanup_mocks(monkeypatch, _permission_denied_getter)

    assert result.cleanup_safe is False
    assert result.platform_images == []
    assert sync_docker_images.call_args.kwargs["cleanup_safe"] is False
    cleanup_helm_charts.assert_not_called()
    cleanup_language_packages.assert_not_called()
    cleanup_generic_artifacts.assert_not_called()


def test_sync_artifact_registry_artifacts_propagates_unexpected_gapic_errors(
    monkeypatch,
):
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
        {"DOCKER": (_unexpected_error_getter, transform_docker_images)},
    )

    with pytest.raises(GoogleAPICallError):
        sync_artifact_registry_artifacts(
            MagicMock(),
            MagicMock(),
            [{"name": "repo", "format": "DOCKER"}],
            "test-project",
            123,
            {"UPDATE_TAG": 123},
            max_workers=1,
        )


def test_load_docker_images_uses_artifact_registry_batch_size():
    from cartography.intel.gcp.artifact_registry.artifact import load_docker_images

    with (
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.load_nodes_without_relationships"
        ) as load_nodes_without_relationships,
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.load_matchlinks_with_progress"
        ) as load_matchlinks_with_progress,
    ):
        load_docker_images(
            MagicMock(),
            [{"id": "image", "repository_id": "repo"}],
            "test-project",
            123,
        )

    assert load_nodes_without_relationships.call_count == 2
    assert (
        load_nodes_without_relationships.call_args_list[0].kwargs["batch_size"]
        == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
    )
    assert (
        load_nodes_without_relationships.call_args_list[1].kwargs["batch_size"]
        == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
    )
    assert load_matchlinks_with_progress.call_count == 4
    assert [
        call.args[1].__class__.__name__
        for call in load_matchlinks_with_progress.call_args_list
    ] == [
        "GCPArtifactRegistryProjectToRepositoryImageRel",
        "GCPArtifactRegistryRepositoryToRepositoryImageRel",
        "GCPArtifactRegistryRepositoryToRepositoryImageRepoImageRel",
        "GCPArtifactRegistryRepositoryImageToImageMatchLink",
    ]
    for call in load_matchlinks_with_progress.call_args_list:
        assert call.kwargs["batch_size"] == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
        assert call.kwargs["_sub_resource_label"] == "GCPProject"
        assert call.kwargs["_sub_resource_id"] == "test-project"


def test_load_nodes_without_relationships_logs_batch_progress(caplog):
    caplog.set_level(
        logging.INFO,
        logger="cartography.intel.gcp.artifact_registry.util",
    )
    neo4j_session = MagicMock()
    node_schema = MagicMock()
    node_schema.label = "GCPArtifactRegistryRepositoryImage"

    with (
        patch(
            "cartography.intel.gcp.artifact_registry.util.ensure_indexes"
        ) as ensure_indexes,
        patch(
            "cartography.intel.gcp.artifact_registry.util.build_ingestion_query",
            return_value="UNWIND ...",
        ) as build_ingestion_query,
        patch(
            "cartography.intel.gcp.artifact_registry.util.load_graph_data"
        ) as load_graph_data,
        patch(
            "cartography.intel.gcp.artifact_registry.util.stat_handler"
        ) as stat_handler,
    ):
        load_nodes_without_relationships(
            neo4j_session,
            node_schema,
            [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            batch_size=2,
            progress_description="test GAR nodes",
            lastupdated=123,
        )

    ensure_indexes.assert_called_once_with(neo4j_session, node_schema)
    build_ingestion_query.assert_called_once_with(
        node_schema, selected_relationships=set()
    )
    assert load_graph_data.call_count == 2
    assert "Loaded test GAR nodes batch 1/2" in caplog.text
    assert "Loaded test GAR nodes batch 2/2" in caplog.text
    stat_handler.incr.assert_called_once_with(
        "node.gcpartifactregistryrepositoryimage.loaded", 3
    )


def test_load_with_progress_rejects_non_positive_batch_size():
    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        _load_with_progress(
            MagicMock(),
            "UNWIND ...",
            [{"id": "1"}],
            batch_size=0,
            progress_description="test GAR nodes",
        )


@pytest.mark.parametrize(
    ("get_artifacts", "list_method"),
    [
        (get_docker_images, lambda client: client.list_docker_images),
        (get_maven_artifacts, lambda client: client.list_maven_artifacts),
        (get_npm_packages, lambda client: client.list_npm_packages),
        (get_python_packages, lambda client: client.list_python_packages),
    ],
)
def test_artifact_listing_asks_for_full_pages(get_artifacts, list_method):
    client = MagicMock()
    list_method(client).return_value = []

    get_artifacts(client, "projects/test-project/locations/us-east1/repositories/repo")

    list_method(client).assert_called_once_with(
        request={
            "parent": "projects/test-project/locations/us-east1/repositories/repo",
            "page_size": 1000,
        },
        timeout=ARTIFACT_REGISTRY_LIST_TIMEOUT,
    )
