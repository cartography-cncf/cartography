from dataclasses import asdict
from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.mapping import ONTOLOGY_MODELS
from cartography.models.ontology.mapping import ONTOLOGY_NODES_MAPPING
from cartography.models.ontology.mapping import SEMANTIC_LABELS_MAPPING
from cartography.sync import TOP_LEVEL_MODULES
from tests.utils import load_models

MODELS = list(load_models(cartography.models))
ALL_MAPPINGS = {
    **ONTOLOGY_NODES_MAPPING,
    **SEMANTIC_LABELS_MAPPING,
}

# Unfortunately, some nodes are not yet migrated to the new data model system.
# We need to ignore them in this test for now as we are not able to load their model class.
# This is a temporary workaround until all models are migrated.
OLD_FORMAT_NODES = [
    "OktaUser",
    "OktaApplication",
]


def _get_model_by_node_label(node_label: str) -> list[Type[CartographyNodeSchema]]:
    models = []
    for _, node_class in MODELS:
        if not issubclass(node_class, CartographyNodeSchema):
            continue
        if node_class.label == node_label:
            models.append(node_class)
    return models


def test_ontology_mapping_modules():
    # Verify that all modules defined in the ontology mapping exist in TOP_LEVEL_MODULES
    # and that module names match between the mapping and the key.
    for mappings in ONTOLOGY_NODES_MAPPING.values():
        for category, mapping in mappings.items():
            assert (
                category in TOP_LEVEL_MODULES
            ), f"Ontology mapping category '{category}' is not found in TOP_LEVEL_MODULES."
            assert (
                mapping.module_name == category
            ), f"Ontology mapping module name '{mapping.module_name}' does not match the key '{category}'."


def test_ontology_mapping_categories():
    # Verify that field used as id by the ontology model are marked as required in the mapping.
    for category, category_mappings in ONTOLOGY_NODES_MAPPING.items():
        assert (
            category in ONTOLOGY_MODELS
        ), f"Module '{category}' not found in ONTOLOGY_MODELS."


def test_ontology_mapping_fields():
    # Verify that all ontology fields in the mapping exist as extra indexed fields
    # in the corresponding module's model.
    for _, mappings in ALL_MAPPINGS.items():
        for module_name, mapping in mappings.items():
            # Skip ontology module as it does not have a corresponding model
            if module_name == "ontology":
                continue
            for node in mapping.nodes:
                # TODO: Remove that uggly exception once all models are migrated to the new data model system
                if node.node_label in OLD_FORMAT_NODES:
                    continue
                # Load the model classes for the module
                model_classes = _get_model_by_node_label(node.node_label)
                assert len(model_classes) > 0, (
                    f"Model class for node label '{node.node_label}' "
                    f"in module '{module_name}' not found."
                )

                for mapping_field in node.fields:
                    found = False
                    # Skip static value handling
                    if mapping_field.special_handling == "static_value":
                        continue
                    for model_class in model_classes:
                        model_property = getattr(
                            model_class.properties, mapping_field.node_field, None
                        )
                        if model_property is not None:
                            found = True
                            break
                    assert found, (
                        f"Model property '{mapping_field.node_field}' for node label "
                        f"'{node.node_label}' in module '{module_name}' not found."
                    )


def test_ontology_mapping_required_fields():
    # Verify that field used as id by the ontology model are marked as required in the mapping.
    for category, category_mappings in ONTOLOGY_NODES_MAPPING.items():
        assert (
            category in ONTOLOGY_MODELS
        ), f"Module '{category}' not found in ONTOLOGY_MODELS."
        model_class = ONTOLOGY_MODELS[category]
        data_dict_id_field = model_class().properties.id.name
        for module, mapping in category_mappings.items():
            for node in mapping.nodes:
                found_id_field = False
                for field in node.fields:
                    if field.ontology_field != data_dict_id_field:
                        continue
                    found_id_field = True
                    assert field.required, (
                        f"Field '{field.ontology_field}' in mapping for node '{node.node_label}' in '{category}.{module}' "
                        f"is used as id in the model but is not marked as `required` in the ontology mapping."
                    )
                if node.eligible_for_source:
                    assert found_id_field, (
                        f"Node '{node.node_label}' in module '{category}.{module}' does not have the id field "
                        f"'{data_dict_id_field}' mapped in the ontology mapping. "
                        "You should add it or set `eligible_for_source` to False."
                    )


def test_ontology_mapping_prefix_usage():
    # Verify that no mapping field uses the 'prefix' attribute
    for _, mappings in SEMANTIC_LABELS_MAPPING.items():
        for module_name, mapping in mappings.items():
            for node in mapping.nodes:
                for mapping_field in node.fields:
                    assert not mapping_field.ontology_field.startswith("_ont_"), (
                        f"Mapping field '{mapping_field.node_field}' in node '{node.node_label}' of module '{module_name}' "
                        "should not use ontology fields starting with '_ont_' (prefix are added automatically)."
                    )


def test_ontology_mapping_or_boolean_fields():
    # Verify that all ontology fields in the mapping exist as extra indexed fields
    # in the corresponding module's model.
    for _, mappings in SEMANTIC_LABELS_MAPPING.items():
        for module_name, mapping in mappings.items():
            for node in mapping.nodes:
                for mapping_field in node.fields:
                    if mapping_field.special_handling != "or_boolean":
                        continue
                    extra_fields = mapping_field.extra.get("fields")
                    assert extra_fields is not None, (
                        f"Mapping field '{mapping_field.node_field}' in node '{node.node_label}' of module '{module_name}' "
                        "is marked as 'or_boolean' but has no 'fields' defined in extra."
                    )
                    node_classes = _get_model_by_node_label(node.node_label)
                    assert len(node_classes) > 0, (
                        f"Model class for node label '{node.node_label}' "
                        f"in module '{module_name}' not found."
                    )
                    for node_class in node_classes:
                        node_properties = asdict(node_class.properties)
                        found = False
                        for extra_field in extra_fields:
                            assert isinstance(extra_field, str), (
                                f"Extra field '{extra_field}' in mapping field '{mapping_field.node_field}' "
                                f"in node '{node.node_label}' of module '{module_name}' should be a string."
                            )
                            if extra_field in node_properties:
                                found = True
                                break
                        assert found, (
                            f"Extra field '{extra_field}' in mapping field '{mapping_field.node_field}' "
                            f"in node '{node.node_label}' of module '{module_name}' not found in model."
                        )


def test_ontology_mapping_nor_boolean_fields():
    # Verify that all ontology fields in the mapping exist as extra indexed fields
    # in the corresponding module's model.
    for _, mappings in SEMANTIC_LABELS_MAPPING.items():
        for module_name, mapping in mappings.items():
            for node in mapping.nodes:
                for mapping_field in node.fields:
                    if mapping_field.special_handling != "nor_boolean":
                        continue
                    extra_fields = mapping_field.extra.get("fields")
                    assert extra_fields is not None, (
                        f"Mapping field '{mapping_field.node_field}' in node '{node.node_label}' of module '{module_name}' "
                        "is marked as 'nor_boolean' but has no 'fields' defined in extra."
                    )
                    node_classes = _get_model_by_node_label(node.node_label)
                    assert len(node_classes) > 0, (
                        f"Model class for node label '{node.node_label}' "
                        f"in module '{module_name}' not found."
                    )
                    for node_class in node_classes:
                        node_properties = asdict(node_class().properties)
                        found = False
                        for extra_field in extra_fields:
                            assert isinstance(extra_field, str), (
                                f"Extra field '{extra_field}' in mapping field '{mapping_field.node_field}' "
                                f"in node '{node.node_label}' of module '{module_name}' should be a string."
                            )
                            if extra_field in node_properties:
                                found = True
                                break
                        assert found, (
                            f"Extra field '{extra_field}' in mapping field '{mapping_field.node_field}' "
                            f"in node '{node.node_label}' of module '{module_name}' not found in model."
                        )


def test_ontology_mapping_equal_boolean_fields():
    # Verify that all ontology fields in the mapping exist as extra indexed fields
    # in the corresponding module's model.
    for _, mappings in SEMANTIC_LABELS_MAPPING.items():
        for module_name, mapping in mappings.items():
            for node in mapping.nodes:
                for mapping_field in node.fields:
                    if mapping_field.special_handling != "equal_boolean":
                        continue
                    extra_values = mapping_field.extra.get("values")
                    assert extra_values is not None, (
                        f"Mapping field '{mapping_field.node_field}' in node '{node.node_label}' of module '{module_name}' "
                        "is marked as 'equal_boolean' but has no 'values' defined in extra."
                    )
                    assert isinstance(extra_values, list), (
                        f"'values' in mapping field '{mapping_field.node_field}' "
                        f"in node '{node.node_label}' of module '{module_name}' should be a list."
                    )
