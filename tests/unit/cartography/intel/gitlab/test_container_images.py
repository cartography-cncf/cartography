from unittest.mock import Mock

from cartography.intel.gitlab.container_images import get_container_images
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
    complete_digests_mock=None,
    refresh_layers_mock=None,
):
    mocks = {
        "get_images": get_images_mock or Mock(),
        "transform_images": transform_images_mock or Mock(),
        "transform_layers": transform_layers_mock or Mock(),
        "load_images": load_images_mock or Mock(),
        "load_layers": load_layers_mock or Mock(),
        "cleanup_images": cleanup_images_mock or Mock(),
        "cleanup_layers": cleanup_layers_mock or Mock(),
        "complete_digests": complete_digests_mock or Mock(return_value=set()),
        "refresh_layers": refresh_layers_mock or Mock(),
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
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_complete_layer_digests",
        mocks["complete_digests"],
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.refresh_layer_closures",
        mocks["refresh_layers"],
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


def test_get_container_images_skips_config_for_complete_digest(monkeypatch):
    # Arrange
    digest = "sha256:complete"
    fetch_blob = Mock()
    observed_and_skipped: set[str] = set()
    skipped_attestation_manifests: list[dict] = []
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_paginated",
        Mock(return_value=[{"name": "latest"}]),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        Mock(
            return_value={
                "_digest": digest,
                "_registry_url": "https://registry.gitlab.example.com",
                "_repository_name": "group/project",
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": "sha256:config"},
            },
        ),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.fetch_registry_blob",
        fetch_blob,
    )

    # Act
    manifests, manifest_lists = get_container_images(
        "https://gitlab.example.com",
        "token",
        [
            {
                "id": 1,
                "project_id": 2,
                "location": "registry.gitlab.example.com/group/project",
            },
        ],
        skip_digests={digest},
        observed_and_skipped=observed_and_skipped,
        skipped_attestation_manifests=skipped_attestation_manifests,
    )

    # Assert
    assert manifests == []
    assert manifest_lists == []
    assert observed_and_skipped == {digest}
    assert skipped_attestation_manifests == [
        {
            "_digest": digest,
            "_registry_url": "https://registry.gitlab.example.com",
            "_repository_name": "group/project",
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {"digest": "sha256:config"},
        },
    ]
    fetch_blob.assert_not_called()


def _repo():
    return {
        "id": 1,
        "project_id": 2,
        "location": "registry.gitlab.example.com/group/project",
    }


def test_get_container_images_skips_manifest_fetch_for_known_complete_digest(
    monkeypatch,
):
    # Arrange: the tag record already carries the digest, and that digest is
    # already enriched in the graph, so no registry request should be issued.
    digest = "sha256:complete"
    get_manifest = Mock()
    get_paginated = Mock()
    head_digest = Mock()
    observed_and_skipped: set[str] = set()
    skipped_attestation_manifests: list[dict] = []
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images.get_paginated",
        get_paginated,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        get_manifest,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest_digest",
        head_digest,
    )

    # Act
    manifests, manifest_lists = get_container_images(
        "https://gitlab.example.com",
        "token",
        [_repo()],
        skip_digests={digest},
        observed_and_skipped=observed_and_skipped,
        skipped_attestation_manifests=skipped_attestation_manifests,
        tags_by_repository={
            "registry.gitlab.example.com/group/project": [
                {"name": "latest", "digest": digest},
            ],
        },
    )

    # Assert
    assert manifests == []
    assert manifest_lists == []
    assert observed_and_skipped == {digest}
    assert skipped_attestation_manifests == [
        {
            "_digest": digest,
            "_registry_url": "https://registry.gitlab.example.com",
            "_repository_name": "group/project",
        },
    ]
    get_manifest.assert_not_called()
    head_digest.assert_not_called()
    # The tag records were supplied, so the tag list endpoint is not re-paginated.
    get_paginated.assert_not_called()


def test_get_container_images_fetches_shared_digest_once(monkeypatch):
    # Arrange: two tags point at the same digest and none is already enriched.
    digest = "sha256:shared"
    manifest = {
        "_digest": digest,
        "_registry_url": "https://registry.gitlab.example.com",
        "_repository_name": "group/project",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
    }
    get_manifest = Mock(return_value=manifest)
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        get_manifest,
    )

    # Act
    manifests, _ = get_container_images(
        "https://gitlab.example.com",
        "token",
        [_repo()],
        tags_by_repository={
            "registry.gitlab.example.com/group/project": [
                {"name": "latest", "digest": digest},
                {"name": "v1.0.0", "digest": digest},
            ],
        },
    )

    # Assert: one manifest fetch, not one per tag.
    assert get_manifest.call_count == 1
    assert manifests == [manifest]


def test_get_container_images_head_probes_when_tag_digest_unknown(monkeypatch):
    # Arrange: the tag record has no digest (tag detail fetch fell back to basic
    # info), so the digest is resolved with a HEAD before any body is fetched.
    digest = "sha256:complete"
    get_manifest = Mock()
    head_digest = Mock(return_value=digest)
    observed_and_skipped: set[str] = set()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        get_manifest,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest_digest",
        head_digest,
    )

    # Act
    manifests, _ = get_container_images(
        "https://gitlab.example.com",
        "token",
        [_repo()],
        skip_digests={digest},
        observed_and_skipped=observed_and_skipped,
        tags_by_repository={
            "registry.gitlab.example.com/group/project": [{"name": "latest"}],
        },
    )

    # Assert
    assert manifests == []
    assert observed_and_skipped == {digest}
    head_digest.assert_called_once_with(
        "https://gitlab.example.com",
        "https://registry.gitlab.example.com",
        "group/project",
        "latest",
        "token",
    )
    get_manifest.assert_not_called()


def test_get_container_images_skips_head_probe_on_first_run(monkeypatch):
    # Arrange: nothing is enriched yet, so a HEAD would only add a round trip on
    # top of the GET that has to happen anyway.
    manifest = {
        "_digest": "sha256:new",
        "_registry_url": "https://registry.gitlab.example.com",
        "_repository_name": "group/project",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
    }
    get_manifest = Mock(return_value=manifest)
    head_digest = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        get_manifest,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest_digest",
        head_digest,
    )

    # Act
    manifests, _ = get_container_images(
        "https://gitlab.example.com",
        "token",
        [_repo()],
        skip_digests=set(),
        tags_by_repository={
            "registry.gitlab.example.com/group/project": [{"name": "latest"}],
        },
    )

    # Assert
    head_digest.assert_not_called()
    assert manifests == [manifest]


def test_get_container_images_walks_manifest_list_when_child_is_skipped(monkeypatch):
    # Arrange: a manifest list with two children, one of which is already
    # enriched. The already-enriched child must be skipped without a fetch while
    # the parent and the new child are still ingested.
    parent_digest = "sha256:parent"
    known_child = "sha256:knownchild"
    new_child = "sha256:newchild"
    parent = {
        "_digest": parent_digest,
        "_registry_url": "https://registry.gitlab.example.com",
        "_repository_name": "group/project",
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [{"digest": known_child}, {"digest": new_child}],
    }
    child = {
        "_digest": new_child,
        "_registry_url": "https://registry.gitlab.example.com",
        "_repository_name": "group/project",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
    }
    get_manifest = Mock(side_effect=[parent, child])
    observed_and_skipped: set[str] = set()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest",
        get_manifest,
    )

    # Act
    manifests, manifest_lists = get_container_images(
        "https://gitlab.example.com",
        "token",
        [_repo()],
        skip_digests={known_child},
        observed_and_skipped=observed_and_skipped,
        tags_by_repository={
            "registry.gitlab.example.com/group/project": [
                {"name": "latest", "digest": parent_digest},
            ],
        },
    )

    # Assert
    assert manifest_lists == [parent]
    assert manifests == [parent, child]
    assert observed_and_skipped == {known_child}
    assert get_manifest.call_count == 2


def test_sync_container_images_excludes_manifest_lists_from_skip_set(monkeypatch):
    # Arrange: the layer-closure query reports a manifest list digest alongside a
    # regular image. Skipping the manifest list would drop the child walk that
    # discovers its platform images, so it must not reach get_container_images.
    parent_digest = "sha256:parent"
    image_digest = "sha256:image"
    get_images = Mock(return_value=([], []))
    mocks = _patch_sync_container_images_dependencies(
        monkeypatch,
        get_images_mock=get_images,
        complete_digests_mock=Mock(return_value={parent_digest, image_digest}),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest_list_digests",
        Mock(return_value={parent_digest}),
    )

    # Act
    sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="token",
        org_id=123,
        repositories=[_repo()],
        update_tag=1,
        common_job_parameters={},
    )

    # Assert
    assert get_images.call_args.kwargs["skip_digests"] == {image_digest}
    assert mocks["cleanup_images"].called


def test_sync_container_images_forwards_tags_by_repository(monkeypatch):
    # Arrange
    tags_by_repository = {
        "registry.gitlab.example.com/group/project": [
            {"name": "latest", "digest": "sha256:image"},
        ],
    }
    get_images = Mock(return_value=([], []))
    _patch_sync_container_images_dependencies(
        monkeypatch,
        get_images_mock=get_images,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_images._get_manifest_list_digests",
        Mock(return_value=set()),
    )

    # Act
    sync_container_images(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="token",
        org_id=123,
        repositories=[_repo()],
        update_tag=1,
        common_job_parameters={},
        tags_by_repository=tags_by_repository,
    )

    # Assert
    assert get_images.call_args.kwargs["tags_by_repository"] is tags_by_repository
