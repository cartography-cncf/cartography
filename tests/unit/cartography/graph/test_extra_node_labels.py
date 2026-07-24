import inspect

import pytest

from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.nodes import LabelKind
from cartography.models.ontology import labels as ontology_labels

SAMPLE_EXTRA = ExtraNodeLabel(
    label="Test",
    description="An additional label used to test the declarative label contract.",
)


def test_extra_node_label_requires_catalog_metadata() -> None:
    with pytest.raises(TypeError):
        # Intentionally omit required metadata to verify constructor rejection.
        ExtraNodeLabel()  # type: ignore[call-arg]


def test_extra_node_labels_rejects_invalid_entries() -> None:
    for invalid_label in ["Test", object()]:
        with pytest.raises(TypeError, match="accepts only ExtraNodeLabel instances"):
            # Intentionally violate the annotation to verify runtime rejection.
            ExtraNodeLabels([invalid_label])  # type: ignore[list-item]


def test_extra_node_labels_accepts_declarative_labels() -> None:
    label = SAMPLE_EXTRA.when(kind="test")

    extra_labels = ExtraNodeLabels([label])

    assert extra_labels.labels == (label,)
    assert label.label == "Test"
    assert label.conditions == (("kind", "test"),)
    assert label.kind is LabelKind.STANDARD


def test_extra_node_label_defaults_to_unconditional() -> None:
    assert SAMPLE_EXTRA.conditions == ()


def test_when_returns_an_immutable_deterministic_copy() -> None:
    conditioned_label = SAMPLE_EXTRA.when(second="2", first="1")

    assert SAMPLE_EXTRA.conditions == ()
    assert conditioned_label.conditions == (("first", "1"), ("second", "2"))
    assert isinstance(hash(conditioned_label), int)


def test_extra_node_label_sorts_direct_conditions() -> None:
    label = ExtraNodeLabel(
        label="Sorted",
        description="A label with deterministic conditions.",
        conditions=(("second", "2"), ("first", "1")),
    )

    assert label.conditions == (("first", "1"), ("second", "2"))


def test_remove_in_is_limited_to_compatibility_labels() -> None:
    with pytest.raises(
        ValueError,
        match="remove_in can only be set for compatibility labels",
    ):
        ExtraNodeLabel(
            label="Invalid",
            description="A noncompatibility label with removal metadata.",
            remove_in="1.0.0",
        )

    compatibility_label = ExtraNodeLabel(
        label="Legacy",
        description="A compatibility label.",
        kind=LabelKind.COMPATIBILITY,
        remove_in="1.0.0",
    )

    assert compatibility_label.remove_in == "1.0.0"


def test_ontology_label_constants_are_explicit_and_documented() -> None:
    catalog = [
        (name, label)
        for name, label in inspect.getmembers(ontology_labels)
        if isinstance(label, ExtraNodeLabel)
    ]

    assert catalog
    for name, label in catalog:
        assert name.isupper(), name
        assert label.kind is LabelKind.ONTOLOGY, name
        assert label.description, name
