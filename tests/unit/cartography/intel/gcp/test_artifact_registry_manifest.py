from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry.manifest import (
    extract_digest_from_reference,
)
from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.manifest import transform_manifests
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageContainsImageMatchLink,
)


def test_load_manifests_uses_fixed_data_model_phases_for_many_parents():
    manifests = [
        {
            "digest": f"sha256:{index}",
            "parent_digest": f"sha256:parent-{index}",
            "child_digest": f"sha256:{index}",
        }
        for index in range(3000)
    ]

    with (
        patch(
            "cartography.intel.gcp.artifact_registry.manifest.load_nodes_without_relationships"
        ) as load_nodes_without_relationships,
        patch(
            "cartography.intel.gcp.artifact_registry.manifest.load_matchlinks_with_progress"
        ) as load_matchlinks_with_progress,
    ):
        load_manifests(MagicMock(), manifests, "test-project", 123)

    load_nodes_without_relationships.assert_called_once()
    assert load_nodes_without_relationships.call_args.args[2] == manifests
    assert (
        load_nodes_without_relationships.call_args.kwargs["batch_size"]
        == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
    )
    load_matchlinks_with_progress.assert_called_once()
    assert isinstance(
        load_matchlinks_with_progress.call_args.args[1],
        GCPArtifactRegistryImageContainsImageMatchLink,
    )
    assert load_matchlinks_with_progress.call_args.args[2] == manifests
    assert (
        load_matchlinks_with_progress.call_args.kwargs["batch_size"]
        == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
    )
    assert load_matchlinks_with_progress.call_args.kwargs["_sub_resource_label"] == (
        "GCPProject"
    )
    assert (
        load_matchlinks_with_progress.call_args.kwargs["_sub_resource_id"]
        == "test-project"
    )


def test_extract_digest_from_reference():
    assert (
        extract_digest_from_reference(
            "us-central1-docker.pkg.dev/test-project/repo/app@sha256:abc123"
        )
        == "sha256:abc123"
    )
    assert (
        extract_digest_from_reference(
            "projects/test-project/locations/us/repositories/repo/dockerImages/app@sha256:def456"
        )
        == "sha256:def456"
    )
    assert extract_digest_from_reference("app:latest") is None
    assert extract_digest_from_reference(None) is None


def test_transform_manifests_uses_parent_digest_directly():
    manifests = transform_manifests(
        [
            {
                "digest": "sha256:child",
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "platform": {"architecture": "amd64", "os": "linux"},
            }
        ],
        "sha256:parent",
    )

    assert manifests == [
        {
            "digest": "sha256:child",
            "type": "image",
            "architecture": "amd64",
            "os": "linux",
            "os_version": None,
            "os_features": None,
            "variant": None,
            "media_type": "application/vnd.oci.image.manifest.v1+json",
            "parent_digest": "sha256:parent",
            "child_digest": "sha256:child",
            "child_image_digests": ["sha256:child"],
        }
    ]
