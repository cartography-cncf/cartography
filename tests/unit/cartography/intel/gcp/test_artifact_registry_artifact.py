from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError

from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)


def _permission_denied_getter(client, repository_name):
    return None


def _unexpected_error_getter(client, repository_name):
    raise GoogleAPICallError("boom")


def test_sync_artifact_registry_artifacts_skips_cleanup_when_repository_incomplete(
    monkeypatch,
):
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
        {"DOCKER": (_permission_denied_getter, transform_docker_images)},
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

    with patch("cartography.intel.gcp.artifact_registry.artifact.load") as load:
        load_docker_images(MagicMock(), [{"id": "image"}], "test-project", 123)

    assert load.call_args.kwargs["batch_size"] == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
