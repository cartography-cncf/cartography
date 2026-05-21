import copy
from typing import Any

from cartography.intel.aibom.transform import transform_aibom_component_payloads
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY


def _get_component_payload_by_name(
    component_payloads: list[dict[str, object]],
    component_name: str,
) -> dict[str, object]:
    return next(
        component_payload
        for component_payload in component_payloads
        if component_payload["name"] == component_name
    )


def test_transform_aibom_component_payloads_deduplicates_duplicate_relationship_records() -> (
    None
):
    # Arrange
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    relationships = document["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "relationships"
    ]
    relationships.append(copy.deepcopy(relationships[0]))

    # Act
    component_payloads = transform_aibom_component_payloads(document)

    # Assert
    agent_payload = _get_component_payload_by_name(component_payloads, "Agent")
    assert agent_payload["uses_model_component_ids"] == [
        "4a6116d40ef28aa5a6ecca3339a38fae1b3a440345d8b096b5a2fb2ec7591721",
    ]
