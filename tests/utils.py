import inspect
import logging
from functools import cache
from pkgutil import iter_modules
from typing import Generator
from typing import Tuple
from typing import Type
from typing import TypeGuard

import cartography.models
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema

logger = logging.getLogger(__name__)


def unwrapper(func):
    """
    Unwraps a function to get past decorators to the original function.
    """
    if not hasattr(func, "__wrapped__"):
        return func
    return unwrapper(func.__wrapped__)


_MODEL_CLASSES = (
    CartographyNodeSchema,
    CartographyRelSchema,
    CartographyNodeProperties,
    CartographyRelProperties,
)
_MODEL_CLASS_SET = frozenset(_MODEL_CLASSES)


# The model base classes are ABCs with thousands of subclasses, so `issubclass()`
# against them goes through `ABCMeta.__subclasscheck__` and walks the whole subclass
# tree on every miss. Walk the MRO instead, like `cartography.models.introspection`
# does. These are the hot predicates for the guard tests that iterate over every
# model class in the codebase.
def is_node_schema(cls: Type) -> TypeGuard[Type[CartographyNodeSchema]]:
    return CartographyNodeSchema in cls.__mro__


def is_rel_schema(cls: Type) -> TypeGuard[Type[CartographyRelSchema]]:
    return CartographyRelSchema in cls.__mro__


def is_node_properties(cls: Type) -> TypeGuard[Type[CartographyNodeProperties]]:
    return CartographyNodeProperties in cls.__mro__


def is_rel_properties(cls: Type) -> TypeGuard[Type[CartographyRelProperties]]:
    return CartographyRelProperties in cls.__mro__


@cache
def _discover_models(
    module,
    module_name: str | None,
) -> Tuple[
    Tuple[
        str,
        Type[
            CartographyNodeSchema
            | CartographyRelSchema
            | CartographyNodeProperties
            | CartographyRelProperties
        ],
    ],
    ...,
]:
    """Walk `module` and return every model class it defines.

    Memoized: model classes are created at import time and never change, and the
    guard tests walk `cartography.models` (5700+ classes) over twenty times.
    """
    discovered = []
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
            if v in _MODEL_CLASS_SET:
                continue
            if _MODEL_CLASS_SET.intersection(v.__mro__):
                discovered.append((sub_module_name, v))

        if hasattr(sub_module, "__path__"):
            discovered.extend(_discover_models(sub_module, sub_module_name))
    return tuple(discovered)


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
    yield from _discover_models(module, module_name)


def node_schema_labels(node_cls: Type[CartographyNodeSchema]) -> set[str]:
    """Return the labels (primary + extra) carried by a node schema.

    Conditional labels are treated as "may carry this label": they are included
    so that a node potentially tagged with an ontology label still counts as
    carrying it.
    """
    labels: set[str] = set()
    primary = getattr(node_cls, "label", None)
    if isinstance(primary, str):
        labels.add(primary)
    extra = getattr(node_cls, "extra_node_labels", None)
    if isinstance(extra, ExtraNodeLabels):
        for entry in extra.labels:
            labels.add(entry.label)
    return labels


def all_graph_labels() -> set[str]:
    """Every Neo4j label the declarative data model can write.

    Walks all `CartographyNodeSchema` subclasses and collects primary labels
    plus every extra label (ontology, compatibility, conditional). Labels
    written only by legacy handwritten Cypher are not modeled, so they are
    absent from this set.
    """
    labels: set[str] = set()
    for _module_name, element in load_models(cartography.models):
        if is_node_schema(element):
            labels.update(node_schema_labels(element))
    return labels
