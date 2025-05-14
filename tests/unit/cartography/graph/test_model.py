import inspect
import logging
import warnings
from pkgutil import iter_modules
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple
from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection

logger = logging.getLogger(__name__)

MODEL_CLASSES = (
    CartographyNodeSchema,
    CartographyRelSchema,
    CartographyNodeProperties,
    CartographyRelProperties,
)


def load_models(module, module_name: str | None = None) -> Generator[
    Tuple[
        str,
        Type[
            CartographyNodeSchema
            | CartographyRelSchema
            | CartographyNodeProperties
            | CartographyRelProperties
        ],
    ],
    None,
    None,
]:
    # DOC
    for sub_module_info in iter_modules(module.__path__):
        sub_module = __import__(
            f"{module.__name__}.{sub_module_info.name}",
            fromlist=[""],
        )
        if module_name is None:
            sub_module_name = sub_module.__name__
        else:
            sub_module_name = module_name
        for v in sub_module.__dict__.values():
            if not inspect.isclass(v):
                continue
            if v in MODEL_CLASSES:
                continue
            if issubclass(v, MODEL_CLASSES):
                yield (sub_module_name, v)

        if hasattr(sub_module, "__path__"):
            yield from load_models(sub_module, sub_module_name)


def test_model_objects_naming_convention():
    # DOC
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
    # DOC
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
        if len(nodes) == 0:
            warnings.warn(
                f"Module {module_name} has no root nodes (e.g. Tenant, Subscription ...). ",
                UserWarning,
            )
        if len(nodes) > 1:
            warnings.warn(
                f"Module {module_name} has multiple root nodes: {', '.join([node.label for node in nodes])}. "
                "Please check the module.",
                UserWarning,
            )
        # TODO: assert len(nodes) == 1
