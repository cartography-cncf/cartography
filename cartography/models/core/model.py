import inspect
from pkgutil import iter_modules
from typing import Generator
from typing import Tuple
from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema

_MODEL_CLASSES = (
    CartographyNodeSchema,
    CartographyRelSchema,
    CartographyNodeProperties,
    CartographyRelProperties,
)

NODES: dict[str, Type[CartographyNodeSchema]] = {}
RELATIONSHIPS: dict[str, Type[CartographyRelSchema]] = {}


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
    """Load all model classes from a module.

    This function recursively loads all model classes from the given module.
    It yields tuples containing the module name and the model class.

    Args:
        module (_type_): The top-level module to load models from.
        module_name (str | None, optional): The name of the module. If None, the module's name will be used.

    Yields:
        Generator[ Tuple[ str, Type[ CartographyNodeSchema | CartographyRelSchema | CartographyNodeProperties | CartographyRelProperties ], ], None, None, ]: A generator yielding tuples of module name and model class.
    """
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
            if v in _MODEL_CLASSES:
                continue
            if issubclass(v, _MODEL_CLASSES):
                yield (sub_module_name, v)

        if hasattr(sub_module, "__path__"):
            yield from load_models(sub_module, sub_module_name)


# Load all models at import time
for _, entity_class in load_models(cartography.models):
    if issubclass(entity_class, CartographyNodeSchema):
        NODES[str(entity_class.label)] = entity_class
    elif issubclass(entity_class, CartographyRelSchema):
        RELATIONSHIPS[str(entity_class.rel_label)] = entity_class
