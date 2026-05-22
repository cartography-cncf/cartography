import copy
from typing import Any

from cartography.intel.aibom.transform import _build_component_id
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


def test_transform_aibom_component_payloads_uses_instance_ids_when_present() -> None:
    # Arrange
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    source_components = document["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "components"
    ]
    agent_component = next(
        component
        for component in source_components["agent"]
        if component["name"] == "Agent"
    )
    model_component = next(
        component
        for component in source_components["model"]
        if component["name"] == "gpt-5.2"
    )
    agent_component["instance_id"] = "agent-instance"
    model_component["instance_id"] = "model-instance"
    model_component_id = _build_component_id(TEST_SOURCE_KEY, model_component)
    document["aibom_analysis"]["sources"][TEST_SOURCE_KEY]["relationships"] = [
        {
            "relationship_type": "USES_MODEL",
            "source_name": "Agent",
            "target_name": "not-the-real-model-name",
            "source_type": "agent",
            "target_type": "model",
            "source_instance_id": "agent-instance",
            "target_instance_id": "model-instance",
        },
    ]

    # Act
    component_payloads = transform_aibom_component_payloads(document)

    # Assert
    agent_payload = _get_component_payload_by_name(component_payloads, "Agent")
    assert agent_payload["uses_model_component_ids"] == [model_component_id]


def test_transform_aibom_component_payloads_falls_back_to_unique_type_name() -> None:
    # Arrange
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    source_components = document["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "components"
    ]
    model_component = next(
        component
        for component in source_components["model"]
        if component["name"] == "gpt-5.2"
    )
    model_component_id = _build_component_id(TEST_SOURCE_KEY, model_component)
    document["aibom_analysis"]["sources"][TEST_SOURCE_KEY]["relationships"] = [
        {
            "relationship_type": "USES_MODEL",
            "source_name": "Agent",
            "target_name": "gpt-5.2",
            "source_type": "agent",
            "target_type": "model",
            "source_instance_id": "",
            "target_instance_id": "",
        },
    ]

    # Act
    component_payloads = transform_aibom_component_payloads(document)

    # Assert
    agent_payload = _get_component_payload_by_name(component_payloads, "Agent")
    assert agent_payload["uses_model_component_ids"] == [model_component_id]


def test_transform_aibom_component_payloads_skips_ambiguous_type_name_fallback() -> (
    None
):
    # Arrange
    document: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    model_components = document["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "components"
    ]["model"]
    model_components.append(
        {
            **copy.deepcopy(model_components[0]),
            "file_path": "/tmp/other_model_file.py",
            "line_number": 777,
        },
    )
    document["aibom_analysis"]["sources"][TEST_SOURCE_KEY]["relationships"] = [
        {
            "relationship_type": "USES_MODEL",
            "source_name": "Agent",
            "target_name": "gpt-5.2",
            "source_type": "agent",
            "target_type": "model",
            "source_instance_id": "",
            "target_instance_id": "",
        },
    ]

    # Act
    component_payloads = transform_aibom_component_payloads(document)

    # Assert
    agent_payload = _get_component_payload_by_name(component_payloads, "Agent")
    assert agent_payload["uses_model_component_ids"] == []
