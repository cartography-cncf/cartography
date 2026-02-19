from dataclasses import asdict
from typing import Type

import cartography.models
from cartography.models.core.nodes import CartographyNodeSchema
from tests.utils import load_models

MODELS = list(load_models(cartography.models))


def _container_model_classes() -> list[Type[CartographyNodeSchema]]:
    container_models: list[Type[CartographyNodeSchema]] = []
    for _, node_class in MODELS:
        if not issubclass(node_class, CartographyNodeSchema):
            continue
        model = node_class()
        extra_labels = model.extra_node_labels
        if not extra_labels:
            continue
        labels = [label for label in extra_labels.labels if isinstance(label, str)]
        if "Container" in labels:
            container_models.append(node_class)
    return container_models


def test_container_runtime_models_expose_architecture_contract() -> None:
    required_fields = {"architecture", "architecture_raw", "architecture_source"}
    models = _container_model_classes()
    assert models, "Expected at least one model with ExtraNodeLabels(['Container'])."
    for model_class in models:
        available = set(asdict(model_class().properties).keys())
        missing = required_fields - available
        assert not missing, (
            f"{model_class.__name__} is missing required container runtime field(s): "
            f"{', '.join(sorted(missing))}"
        )
