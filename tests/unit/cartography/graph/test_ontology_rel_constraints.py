import cartography.models
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.ontology.constraints import LEGACY_REL_WHITELIST
from cartography.models.ontology.constraints import ONTOLOGY_REL_CONSTRAINTS
from tests.utils import load_models


def _ontology_labels(node_cls: type[CartographyNodeSchema]) -> set[str]:
    """Return the set of labels (primary + extra) carried by a node schema.

    Conditional labels are treated as "may carry this label": included so that
    a node potentially-tagged with an ontology label is still constrained.
    """
    labels: set[str] = set()
    primary = getattr(node_cls, "label", None)
    if isinstance(primary, str):
        labels.add(primary)
    extra = getattr(node_cls, "extra_node_labels", None)
    if isinstance(extra, ExtraNodeLabels):
        for entry in extra.labels:
            if isinstance(entry, str):
                labels.add(entry)
            elif isinstance(entry, ConditionalNodeLabel):
                labels.add(entry.label)
    return labels


def _violations_for(
    rel: CartographyRelSchema,
    src_labels: set[str],
    dst_labels: set[str],
    owner_repr: str,
) -> list[str]:
    out: list[str] = []
    if type(rel) in LEGACY_REL_WHITELIST:
        return out
    for constraint in ONTOLOGY_REL_CONSTRAINTS:
        canonical = constraint.src in src_labels and constraint.dst in dst_labels
        reverse = constraint.dst in src_labels and constraint.src in dst_labels
        if canonical and rel.rel_label != constraint.label:
            out.append(
                f"{owner_repr}: {type(rel).__name__} uses rel_label "
                f"'{rel.rel_label}' for ({constraint.src})->({constraint.dst}); "
                f"expected '{constraint.label}'."
            )
        elif reverse and not canonical:
            # Edge between the same ontology pair but going the wrong way:
            # canonical direction is (src)-[label]->(dst), so any
            # (dst)-[*]->(src) edge violates the constraint.
            out.append(
                f"{owner_repr}: {type(rel).__name__} wires "
                f"({constraint.dst})-[{rel.rel_label}]->({constraint.src}); "
                f"canonical direction is ({constraint.src})-[{constraint.label}]"
                f"->({constraint.dst})."
            )
    return out


def test_ontology_rel_constraints():
    """Edges between ontology-labelled nodes must use the canonical rel_label.

    Walks every CartographyNodeSchema and every standalone MatchLink-style
    CartographyRelSchema. For each (src_labels, dst_labels) pair derived from
    the rel direction, every matching RelConstraint must hold.
    """
    # Pass 1: index every node schema by primary label so we can resolve
    # target_node_label / source_node_label strings to ontology label sets.
    label_index: dict[str, set[str]] = {}
    node_classes: list[type[CartographyNodeSchema]] = []
    rel_classes: list[type[CartographyRelSchema]] = []
    for _module_name, element in load_models(cartography.models):
        if issubclass(element, CartographyNodeSchema):
            primary = getattr(element, "label", None)
            if isinstance(primary, str):
                label_index[primary] = _ontology_labels(element)
                node_classes.append(element)
        elif issubclass(element, CartographyRelSchema):
            rel_classes.append(element)

    violations: list[str] = []

    # Pass 2: relationships attached to a node schema.
    for node_cls in node_classes:
        owner_labels = label_index.get(node_cls.label, set())
        rels: list[CartographyRelSchema] = []
        sub_rel = getattr(node_cls, "sub_resource_relationship", None)
        if isinstance(sub_rel, CartographyRelSchema):
            rels.append(sub_rel)
        others = getattr(node_cls, "other_relationships", None)
        if isinstance(others, OtherRelationships):
            rels.extend(others.rels)

        for rel in rels:
            target_labels = label_index.get(rel.target_node_label)
            if target_labels is None:
                # Target node is not modeled in cartography (e.g. legacy
                # handwritten label); we cannot reason about its ontology
                # tags so we skip rather than emit false positives.
                continue
            if rel.direction == LinkDirection.OUTWARD:
                src_labels, dst_labels = owner_labels, target_labels
            else:
                src_labels, dst_labels = target_labels, owner_labels
            violations.extend(
                _violations_for(
                    rel,
                    src_labels,
                    dst_labels,
                    owner_repr=node_cls.__name__,
                )
            )

    # Pass 3: standalone MatchLink rel classes (those that declare
    # source_node_label as a class-level default).
    for rel_cls in rel_classes:
        source_label = getattr(rel_cls, "source_node_label", None)
        target_label = getattr(rel_cls, "target_node_label", None)
        if not isinstance(source_label, str) or not isinstance(target_label, str):
            continue
        src_set = label_index.get(source_label)
        dst_set = label_index.get(target_label)
        if src_set is None or dst_set is None:
            continue
        # Instantiate to read direction / rel_label as concrete values.
        try:
            rel = rel_cls()
        except TypeError:
            continue
        if rel.direction == LinkDirection.OUTWARD:
            src_labels, dst_labels = src_set, dst_set
        else:
            src_labels, dst_labels = dst_set, src_set
        violations.extend(
            _violations_for(
                rel,
                src_labels,
                dst_labels,
                owner_repr=f"MatchLink {rel_cls.__name__}",
            )
        )

    assert (
        not violations
    ), "Ontology relationship constraints violated:\n  - " + "\n  - ".join(
        sorted(set(violations))
    )
