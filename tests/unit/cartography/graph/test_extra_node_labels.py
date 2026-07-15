import inspect
from dataclasses import dataclass

import pytest

from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology import labels as ontology_labels


@dataclass(frozen=True)
class SampleExtraLabel(ExtraNodeLabel):
    """An additional label used to test the declarative label contract."""

    label: str = "Test"


def test_extra_node_label_must_be_subclassed() -> None:
    with pytest.raises(TypeError, match="ExtraNodeLabel must be subclassed"):
        ExtraNodeLabel()


def test_extra_node_labels_rejects_invalid_entries() -> None:
    for invalid_label in ["Test", object()]:
        with pytest.raises(TypeError, match="accepts only ExtraNodeLabel instances"):
            # Intentionally violate the annotation to verify runtime rejection.
            ExtraNodeLabels([invalid_label])  # type: ignore[list-item]


def test_extra_node_labels_accepts_declarative_labels() -> None:
    label = SampleExtraLabel(conditions={"kind": "test"})

    extra_labels = ExtraNodeLabels([label])

    assert extra_labels.labels == [label]
    assert label.label == "Test"
    assert label.conditions == {"kind": "test"}
    assert label.ontology is False


def test_extra_node_label_defaults_to_unconditional() -> None:
    assert SampleExtraLabel().conditions == {}


def test_ontology_label_classes_are_explicit_and_documented() -> None:
    concrete_classes = [
        label_class
        for _, label_class in inspect.getmembers(ontology_labels, inspect.isclass)
        if issubclass(label_class, ExtraNodeLabel)
        and label_class is not ExtraNodeLabel
        and label_class.__module__ == ontology_labels.__name__
    ]

    assert concrete_classes
    for label_class in concrete_classes:
        label = label_class()
        assert label.ontology is True, label_class.__name__
        assert label_class.__doc__, label_class.__name__
