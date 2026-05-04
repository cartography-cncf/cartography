from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageContainsImageMatchLink,
)


def test_load_manifests_uses_fixed_data_model_phases_for_many_parents():
    manifests = [
        {
            "id": f"parent-{index}@sha256:{index}",
            "parent_artifact_id": f"parent-{index}",
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
