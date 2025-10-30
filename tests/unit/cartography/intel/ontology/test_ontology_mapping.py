from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.mapping import ONTOLOGY_MAPPING
from cartography.models.ontology.mapping import ONTOLOGY_MODELS
from cartography.sync import TOP_LEVEL_MODULES
from tests.utils import load_models

MODELS = list(load_models(cartography.models))

# Unfortunately, some nodes are not yet migrated to the new data model system.
# We need to ignore them in this test for now as we are not able to load their model class.
# This is a temporary workaround until all models are migrated.
OLD_FORMAT_NODES = [
    "OktaUser",
]


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
    for _, node_class in list(load_models(cartography.models)):
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
                # TODO: Remove that uggly exception once all models are migrated to the new data model system
                if node.node_label in OLD_FORMAT_NODES:
                    continue
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
                    assert model_property is not None, (
                        f"Model property '{mapping_field.node_field}' for node label "
                        f"'{node.node_label}' in module '{module_name}' not found."
                    )


def test_ontology_mapping_required_fields():
    # Verify that field used as id by the ontology model are marked as required in the mapping.
    for category, category_mappings in ONTOLOGY_MAPPING.items():
        assert (
            category in ONTOLOGY_MODELS
        ), f"Module '{category}' not found in ONTOLOGY_MODELS, please update the unit test."
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
