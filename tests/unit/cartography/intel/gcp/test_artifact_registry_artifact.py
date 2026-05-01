import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError

from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.util import _load_with_progress
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
            "cartography.intel.gcp.artifact_registry.artifact.cleanup_docker_images"
        ) as cleanup_docker_images,
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
        cleanup_docker_images,
        cleanup_helm_charts,
        cleanup_language_packages,
        cleanup_generic_artifacts,
    )


def test_sync_artifact_registry_artifacts_skips_cleanup_when_repository_incomplete(
    monkeypatch,
):
    (
        result,
        cleanup_docker_images,
        cleanup_helm_charts,
        cleanup_language_packages,
        cleanup_generic_artifacts,
    ) = _run_sync_with_cleanup_mocks(monkeypatch, _permission_denied_getter)

    assert result.cleanup_safe is False
    assert result.platform_images == []
    cleanup_docker_images.assert_not_called()
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
        patch(
            "cartography.intel.gcp.artifact_registry.artifact.apply_conditional_labels"
        ) as apply_conditional_labels,
    ):
        load_docker_images(
            MagicMock(),
            [{"id": "image", "repository_id": "repo"}],
            "test-project",
            123,
        )

    load_nodes_without_relationships.assert_called_once()
    assert load_nodes_without_relationships.call_args.kwargs["apply_labels"] is False
    assert (
        load_nodes_without_relationships.call_args.kwargs["batch_size"]
        == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
    )
    assert load_matchlinks_with_progress.call_count == 2
    for call in load_matchlinks_with_progress.call_args_list:
        assert call.kwargs["batch_size"] == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
        assert call.kwargs["_sub_resource_label"] == "GCPProject"
        assert call.kwargs["_sub_resource_id"] == "test-project"
    apply_conditional_labels.assert_called_once()


def test_load_nodes_without_relationships_logs_batch_progress(caplog):
    caplog.set_level(
        logging.INFO,
        logger="cartography.intel.gcp.artifact_registry.util",
    )
    neo4j_session = MagicMock()
    node_schema = MagicMock()
    node_schema.label = "GCPArtifactRegistryContainerImage"

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
            apply_labels=False,
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
        "node.gcpartifactregistrycontainerimage.loaded", 3
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
