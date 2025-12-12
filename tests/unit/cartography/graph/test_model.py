import logging
import warnings
from typing import Dict
from typing import Set
from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from tests.utils import load_models

logger = logging.getLogger(__name__)


def test_model_objects_naming_convention():
    """Test that all model objects follow the naming convention."""
    for module_name, element in load_models(cartography.models):
        if issubclass(element, CartographyNodeSchema):
            if not element.__name__.endswith("Schema"):
                warnings.warn(
                    f"Node {element.__name__} does not comply with naming convention. "
                    "Node names should end with 'Schema'."
                    f" Please rename the class to {element.__name__}Schema.",
                    UserWarning,
                )
            # TODO assert element.__name__.endswith("Schema")
        elif issubclass(element, CartographyRelSchema):
            if not element.__name__.endswith("Rel"):
                warnings.warn(
                    f"Relationship {element.__name__} does not comply with naming convention. "
                    "Relationship names should end with 'Rel'."
                    f" Please rename the class to {element.__name__}Rel.",
                    UserWarning,
                )
            # TODO assert element.__name__.endswith("Rel")
        elif issubclass(element, CartographyNodeProperties):
            if not element.__name__.endswith("Properties"):
                warnings.warn(
                    f"Node properties {element.__name__} does not comply with naming convention. "
                    "Node properties names should end with 'Properties'."
                    f" Please rename the class to {element.__name__}Properties.",
                    UserWarning,
                )
            # TODO assert element.__name__.endswith("Properties")
        elif issubclass(element, CartographyRelProperties):
            if not element.__name__.endswith("RelProperties"):
                warnings.warn(
                    f"Relationship properties {element.__name__} does not comply with naming convention. "
                    "Relationship properties names should end with 'RelProperties'."
                    f" Please rename the class to {element.__name__}RelProperties.",
                    UserWarning,
                )
            # TODO assert element.__name__.endswith("RelProperties")


def test_sub_resource_relationship():
    """Test that all root nodes have a sub_resource_relationship with rel_label 'RESOURCE' and direction 'INWARD'."""
    root_node_per_modules: Dict[str, Set[Type[CartographyNodeSchema]]] = {}

    for module_name, node in load_models(cartography.models):
        if module_name not in root_node_per_modules:
            root_node_per_modules[module_name] = set()
        if not issubclass(node, CartographyNodeSchema):
            continue
        sub_resource_relationship = getattr(node, "sub_resource_relationship", None)
        if sub_resource_relationship is None:
            root_node_per_modules[module_name].add(node)
            continue
        if not isinstance(sub_resource_relationship, CartographyRelSchema):
            root_node_per_modules[module_name].add(node)
            continue
        # Check that the rel_label is 'RESOURCE'
        if sub_resource_relationship.rel_label != "RESOURCE":
            warnings.warn(
                f"Node {node.label} has a sub_resource_relationship with rel_label {sub_resource_relationship.rel_label}. "
                "Expected 'RESOURCE'.",
                UserWarning,
            )
            # TODO assert sub_resource_relationship.rel_label == "RESOURCE"
        # Check that the direction is INWARD
        if sub_resource_relationship.direction != LinkDirection.INWARD:
            warnings.warn(
                f"Node {node.label} has a sub_resource_relationship with direction {sub_resource_relationship.direction}. "
                "Expected 'INWARD'.",
                UserWarning,
            )
            # TODO assert sub_resource_relationship.direction == "INWARD"

    for module_name, nodes in root_node_per_modules.items():
        if len(nodes) > 1:
            warnings.warn(
                f"Module {module_name} has multiple root nodes: {', '.join([node.label for node in nodes])}. "
                "Please check the module.",
                UserWarning,
            )
        # TODO: assert len(nodes) > 1
