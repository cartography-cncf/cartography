from unittest.mock import Mock

from cartography.intel.gitlab.container_images import GITLAB_CONTAINER_IMAGE_BATCH_SIZE
from cartography.intel.gitlab.container_images import (
    GITLAB_CONTAINER_IMAGE_LAYER_BATCH_SIZE,
)
from cartography.intel.gitlab.container_images import load_container_image_layers
from cartography.intel.gitlab.container_images import load_container_images
from cartography.intel.gitlab.container_images import sync_container_images
from cartography.intel.gitlab.container_images import transform_container_image_layers


def _patch_sync_container_images_dependencies(
    monkeypatch,
    *,
    get_images_mock=None,
    transform_images_mock=None,
    transform_layers_mock=None,
    load_images_mock=None,
    load_layers_mock=None,
    cleanup_images_mock=None,
    cleanup_layers_mock=None,
):
    mocks = {
        "get_images": get_images_mock or Mock(),
        "transform_images": transform_images_mock or Mock(),
        "transform_layers": transform_layers_mock or Mock(),
        "load_images": load_images_mock or Mock(),
        "load_layers": load_layers_mock or Mock(),
        "cleanup_images": cleanup_images_mock or Mock(),
        "cleanup_layers": cleanup_layers_mock or Mock(),
    }

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_container_images",
        mocks["get_images"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_images",
        mocks["transform_images"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.transform_container_image_layers",
        mocks["transform_layers"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_images",
        mocks["load_images"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load_container_image_layers",
        mocks["load_layers"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_images",
        mocks["cleanup_images"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.cleanup_container_image_layers",
        mocks["cleanup_layers"],
    )

    return mocks


def test_load_container_images_uses_conservative_batch_size(monkeypatch):
    load_mock = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.load",
        load_mock,
    )

    load_container_images(
        neo4j_session=Mock(),
        images=[{"digest": "sha256:image"}],
        org_id=123,
        gitlab_url="https://gitlab.example.com",
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
        org_id=123,
        gitlab_url="https://gitlab.example.com",
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
    mocks = _patch_sync_container_images_dependencies(
        monkeypatch,
        get_images_mock=Mock(
            side_effect=[
                ([{"_digest": "sha256:a"}], [{"_digest": "sha256:list-a"}]),
                ([{"_digest": "sha256:b"}], []),
                ([{"_digest": "sha256:c"}], [{"_digest": "sha256:list-c"}]),
            ]
        ),
        transform_images_mock=Mock(
            side_effect=[
                [{"digest": "img-a"}],
                [{"digest": "img-b"}],
                [{"digest": "img-c"}],
            ]
        ),
        transform_layers_mock=Mock(
            side_effect=[
                [{"diff_id": "layer-a"}],
                [{"diff_id": "layer-b"}],
                [{"diff_id": "layer-c"}],
            ]
        ),
    )

    repositories = [{"id": i} for i in range(5)]
    manifests, manifest_lists = sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_id=123,
        repositories=repositories,
        update_tag=123,
        common_job_parameters={
            "UPDATE_TAG": 123,
            "org_id": 123,
            "gitlab_url": "https://gitlab.example.com",
        },
    )

    assert mocks["get_images"].call_count == 3
    assert mocks["load_layers"].call_count == 3
    assert mocks["load_images"].call_count == 3
    mocks["cleanup_layers"].assert_called_once()
    mocks["cleanup_images"].assert_called_once()
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
    mocks = _patch_sync_container_images_dependencies(monkeypatch)

    manifests, manifest_lists = sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_id=123,
        repositories=[],
        update_tag=123,
        common_job_parameters={
            "UPDATE_TAG": 123,
            "org_id": 123,
            "gitlab_url": "https://gitlab.example.com",
        },
    )

    mocks["get_images"].assert_not_called()
    mocks["transform_images"].assert_not_called()
    mocks["transform_layers"].assert_not_called()
    mocks["load_images"].assert_not_called()
    mocks["load_layers"].assert_not_called()
    mocks["cleanup_layers"].assert_called_once()
    mocks["cleanup_images"].assert_called_once()
    assert manifests == []
    assert manifest_lists == []


def test_transform_container_image_layers_persists_history_and_is_empty():
    raw_manifests = [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "_digest": "sha256:image",
            "layers": [
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 10,
                    "digest": "sha256:layer1",
                },
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 20,
                    "digest": "sha256:layer2",
                },
            ],
            "_config": {
                "rootfs": {
                    "diff_ids": [
                        "sha256:diff1",
                        "sha256:diff2",
                    ],
                },
                "history": [
                    {
                        "created_by": "/bin/sh -c #(nop) LABEL maintainer=test",
                        "empty_layer": True,
                    },
                    {"created_by": "/bin/sh -c apk add curl"},
                    {"created_by": "/bin/sh -c mkdir /app"},
                ],
            },
        },
    ]

    layers = transform_container_image_layers(raw_manifests)

    assert layers == [
        {
            "diff_id": "sha256:diff1",
            "digest": "sha256:layer1",
            "media_type": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 10,
            "is_empty": False,
            "history": "/bin/sh -c apk add curl",
            "next_diff_ids": ["sha256:diff2"],
        },
        {
            "diff_id": "sha256:diff2",
            "digest": "sha256:layer2",
            "media_type": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 20,
            "is_empty": False,
            "history": "/bin/sh -c mkdir /app",
        },
    ]
