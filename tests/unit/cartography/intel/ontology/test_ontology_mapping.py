from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.mapping import ONTOLOGY_MAPPING
from cartography.sync import TOP_LEVEL_MODULES
from tests.utils import load_models

MODELS = list(load_models(cartography.models))


def test_ontology_mapping_modules():
    # Verify that all modules defined in the ontology mapping exist in TOP_LEVEL_MODULES
    # and that module names match between the mapping and the key.
    for mappings in ONTOLOGY_MAPPING.values():
        for category, mapping in mappings.items():
            assert (
                category in TOP_LEVEL_MODULES
            ), f"Ontology mapping category '{category}' is not found in TOP_LEVEL_MODULES."
            assert (
                mapping.module_name == category
            ), f"Ontology mapping module name '{mapping.module_name}' does not match the key '{category}'."


def _get_model_by_node_label(node_label: str) -> Type[CartographyNodeSchema] | None:
    for _, node_class in MODELS:
        if not issubclass(node_class, CartographyNodeSchema):
            continue
        if node_class.label == node_label:
            return node_class
    return None


def test_ontology_mapping_fields():
    # Verify that all ontology fields in the mapping exist as extra indexed fields
    # in the corresponding module's model.
    for _, mappings in ONTOLOGY_MAPPING.items():
        for module_name, mapping in mappings.items():
            for node in mapping.nodes:
                # Load the model class for the module
                model_class = _get_model_by_node_label(node.node_label)
                assert model_class is not None, (
                    f"Model class for node label '{node.node_label}' "
                    f"in module '{module_name}' not found."
                )

                # Check all ontology fields are in extra indexed fields
                for mapping_field in node.fields:
                    model_property = getattr(
                        model_class.properties, mapping_field.node_field, None
                    )
                    print(
                        model_class.properties, mapping_field.node_field, model_property
                    )  # DEBUG
                    assert model_property is not None, (
                        f"Model property '{mapping_field.node_field}' for node label "
                        f"'{node.node_label}' in module '{module_name}' not found."
                    )
