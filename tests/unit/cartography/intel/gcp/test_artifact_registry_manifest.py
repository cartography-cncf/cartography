from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
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
    assert load_matchlinks_with_progress.call_count == 3
    for call in load_matchlinks_with_progress.call_args_list:
        assert call.args[2] == manifests
        assert call.kwargs["batch_size"] == ARTIFACT_REGISTRY_LOAD_BATCH_SIZE
        assert call.kwargs["_sub_resource_label"] == "GCPProject"
        assert call.kwargs["_sub_resource_id"] == "test-project"
