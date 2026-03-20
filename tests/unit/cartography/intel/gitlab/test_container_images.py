from unittest.mock import Mock

from cartography.intel.gitlab.container_images import GITLAB_CONTAINER_IMAGE_BATCH_SIZE
from cartography.intel.gitlab.container_images import (
    GITLAB_CONTAINER_IMAGE_LAYER_BATCH_SIZE,
)
from cartography.intel.gitlab.container_images import load_container_image_layers
from cartography.intel.gitlab.container_images import load_container_images
from cartography.intel.gitlab.container_images import sync_container_images


def test_load_container_images_uses_conservative_batch_size(monkeypatch):
    load_mock = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load",
        load_mock,
    )

    load_container_images(
        neo4j_session=Mock(),
        images=[{"digest": "sha256:image"}],
        org_url="https://gitlab.example.com/groups/core",
        update_tag=123,
    )

    assert load_mock.call_args.kwargs["batch_size"] == GITLAB_CONTAINER_IMAGE_BATCH_SIZE


def test_load_container_image_layers_uses_conservative_batch_size(monkeypatch):
    load_mock = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load",
        load_mock,
    )

    load_container_image_layers(
        neo4j_session=Mock(),
        layers=[{"diff_id": "sha256:layer"}],
        org_url="https://gitlab.example.com/groups/core",
        update_tag=123,
    )

    assert (
        load_mock.call_args.kwargs["batch_size"]
        == GITLAB_CONTAINER_IMAGE_LAYER_BATCH_SIZE
    )


def test_sync_container_images_processes_repositories_in_batches(monkeypatch):
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.GITLAB_CONTAINER_REPOSITORY_BATCH_SIZE",
        2,
    )
    get_images_mock = Mock(
        side_effect=[
            ([{"_digest": "sha256:a"}], [{"_digest": "sha256:list-a"}]),
            ([{"_digest": "sha256:b"}], []),
            ([{"_digest": "sha256:c"}], [{"_digest": "sha256:list-c"}]),
        ]
    )
    transform_images_mock = Mock(
        side_effect=[
            [{"digest": "img-a"}],
            [{"digest": "img-b"}],
            [{"digest": "img-c"}],
        ]
    )
    transform_layers_mock = Mock(
        side_effect=[
            [{"diff_id": "layer-a"}],
            [{"diff_id": "layer-b"}],
            [{"diff_id": "layer-c"}],
        ]
    )
    load_images_mock = Mock()
    load_layers_mock = Mock()
    cleanup_images_mock = Mock()
    cleanup_layers_mock = Mock()

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_container_images",
        get_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_images",
        transform_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_image_layers",
        transform_layers_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_images",
        load_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_image_layers",
        load_layers_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_images",
        cleanup_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_image_layers",
        cleanup_layers_mock,
    )

    repositories = [{"id": i} for i in range(5)]
    manifests, manifest_lists = sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_url="https://gitlab.example.com/groups/core",
        repositories=repositories,
        update_tag=123,
        common_job_parameters={"UPDATE_TAG": 123},
    )

    assert get_images_mock.call_count == 3
    assert load_layers_mock.call_count == 3
    assert load_images_mock.call_count == 3
    cleanup_layers_mock.assert_called_once()
    cleanup_images_mock.assert_called_once()
    assert manifests == [
        {"_digest": "sha256:a"},
        {"_digest": "sha256:b"},
        {"_digest": "sha256:c"},
    ]
    assert manifest_lists == [
        {"_digest": "sha256:list-a"},
        {"_digest": "sha256:list-c"},
    ]


def test_sync_container_images_cleans_up_when_repositories_empty(monkeypatch):
    get_images_mock = Mock()
    transform_images_mock = Mock()
    transform_layers_mock = Mock()
    load_images_mock = Mock()
    load_layers_mock = Mock()
    cleanup_images_mock = Mock()
    cleanup_layers_mock = Mock()

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_container_images",
        get_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_images",
        transform_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_image_layers",
        transform_layers_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_images",
        load_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_image_layers",
        load_layers_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_images",
        cleanup_images_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_image_layers",
        cleanup_layers_mock,
    )

    manifests, manifest_lists = sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_url="https://gitlab.example.com/groups/core",
        repositories=[],
        update_tag=123,
        common_job_parameters={"UPDATE_TAG": 123},
    )

    get_images_mock.assert_not_called()
    transform_images_mock.assert_not_called()
    transform_layers_mock.assert_not_called()
    load_images_mock.assert_not_called()
    load_layers_mock.assert_not_called()
    cleanup_layers_mock.assert_called_once()
    cleanup_images_mock.assert_called_once()
    assert manifests == []
    assert manifest_lists == []
