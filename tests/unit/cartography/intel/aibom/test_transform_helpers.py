import copy
from typing import Any
from typing import cast
from unittest.mock import patch

from cartography.intel.aibom.transform import _build_component_id
from cartography.intel.aibom.transform import _build_component_logical_id
from cartography.intel.aibom.transform import _build_relationship_component_lookup
from cartography.intel.aibom.transform import _flatten_count_map
from cartography.intel.aibom.transform import transform_aibom_relationship_payloads
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY


def _get_component(name: str) -> dict[str, Any]:
    sources = cast(
        dict[str, dict[str, Any]],
        AIBOM_REPORT["aibom_analysis"]["sources"],
    )
    source = next(iter(sources.values()))
    for items in source["components"].values():
        for component in items:
            if component["name"] == name:
                return copy.deepcopy(component)
    raise AssertionError(f"Component {name} not found in fixture")


def _get_first_relationship(document: dict[str, Any]) -> dict[str, Any]:
    sources = cast(
        dict[str, dict[str, Any]],
        document["aibom_analysis"]["sources"],
    )
    source = next(iter(sources.values()))
    return copy.deepcopy(source["relationships"][0])


def test_flatten_count_map_returns_sorted_keys_and_matching_counts() -> None:
    # Arrange
    count_map = {
        "tool": 27,
        "agent": 1,
        "dataset": 1,
    }

    # Act
    keys, counts = _flatten_count_map(count_map)

    # Assert
    assert keys == ["agent", "dataset", "tool"]
    assert counts == [1, 1, 27]


def test_flatten_count_map_returns_empty_lists_for_none() -> None:
    # Arrange
    count_map = None

    # Act
    keys, counts = _flatten_count_map(count_map)

    # Assert
    assert keys == []
    assert counts == []


def test_build_component_id_is_stable_for_same_source_and_component() -> None:
    # Arrange
    component = _get_component("litellm")

    # Act
    component_id_1 = _build_component_id(TEST_SOURCE_KEY, component)
    component_id_2 = _build_component_id(TEST_SOURCE_KEY, component)

    # Assert
    assert component_id_1 == component_id_2


def test_build_component_id_changes_when_source_key_changes() -> None:
    # Arrange
    component = _get_component("litellm")
    other_source_key = (
        "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend"
        "@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )

    # Act
    component_id_1 = _build_component_id(TEST_SOURCE_KEY, component)
    component_id_2 = _build_component_id(other_source_key, component)

    # Assert
    assert component_id_1 != component_id_2


def test_build_component_logical_id_is_stable_for_same_component() -> None:
    # Arrange
    component = _get_component("litellm")

    # Act
    logical_id_1 = _build_component_logical_id(component)
    logical_id_2 = _build_component_logical_id(component)

    # Assert
    assert logical_id_1 == logical_id_2


def test_build_component_logical_id_ignores_instance_specific_fields() -> None:
    # Arrange
    component = _get_component("litellm")
    changed_component = copy.deepcopy(component)
    changed_component["instance_id"] = "different-instance-id"
    changed_component["line_number"] = 9999

    # Act
    logical_id_1 = _build_component_logical_id(component)
    logical_id_2 = _build_component_logical_id(changed_component)

    # Assert
    assert logical_id_1 == logical_id_2


def test_build_relationship_component_lookup_returns_component_ids_by_type_and_name() -> (
    None
):
    # Arrange
    document = copy.deepcopy(AIBOM_REPORT)
    attack_path_tools = _get_component("attack_path_tools")

    # Act
    component_lookup = _build_relationship_component_lookup(document)

    # Assert
    assert component_lookup[
        (
            TEST_SOURCE_KEY,
            "mcp_server",
            "attack_path_tools",
        )
    ] == _build_component_id(TEST_SOURCE_KEY, attack_path_tools)


def test_transform_aibom_relationship_payloads_skips_unresolved_relationship() -> None:
    # Arrange
    document = copy.deepcopy(AIBOM_REPORT)
    relationship = _get_first_relationship(document)
    # Replace the target name with a missing component name to test the skip logic.
    relationship["target_name"] = "missing-target-component"
    sources = cast(
        dict[str, dict[str, Any]],
        document["aibom_analysis"]["sources"],
    )
    source = next(iter(sources.values()))
    source["relationships"] = [relationship]

    with patch("cartography.intel.aibom.transform.logger.warning") as mock_warning:
        # Act
        relationship_payloads = transform_aibom_relationship_payloads(document)

    # Assert
    assert relationship_payloads == []
    mock_warning.assert_called_once()
