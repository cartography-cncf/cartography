from dataclasses import dataclass
from typing import Optional

from cartography.graph.querybuilder import build_create_index_queries
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SimpleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    severity: PropertyRef = PropertyRef("severity")
    is_public: PropertyRef = PropertyRef("is_public")


RESOURCE = ExtraNodeLabel(
    label="Resource",
    description="A generic test resource.",
)


AWS_RESOURCE = ExtraNodeLabel(
    label="AWSResource",
    description="A generic test AWS resource.",
)


CRITICAL = ExtraNodeLabel(
    label="Critical",
    description="A test resource with critical severity.",
)


PUBLIC_RESOURCE = ExtraNodeLabel(
    label="PublicResource",
    description="A publicly accessible test resource.",
)


SPECIAL = ExtraNodeLabel(
    label="Special",
    description="A test label with a specially escaped condition.",
)


EMPTY_CONDITION = ExtraNodeLabel(
    label="EmptyCondition",
    description="An unconditional label used to test empty conditions.",
)


VALID_CONDITION = ExtraNodeLabel(
    label="ValidCondition",
    description="A conditional label paired with an unconditional test label.",
)


def _set_clause(query: str) -> str:
    """
    Return the part of an ingestion query that precedes the conditional label clauses.

    Conditional labels are applied with FOREACH clauses that themselves contain `SET i:Label`, so
    tests that assert on the unconditional SET clause need to look at the query prefix only.
    """
    return query.split("FOREACH")[0]


def _apply_clause(query: str, label: str) -> str:
    """Return the FOREACH clause that applies `label`, or "" if there is none."""
    for line in query.splitlines():
        if line.strip().startswith("FOREACH") and line.rstrip().endswith(
            f"| SET i:{label})"
        ):
            return line.strip()
    return ""


def _remove_clause(query: str, label: str) -> str:
    """Return the FOREACH clause that removes `label`, or "" if there is none."""
    for line in query.splitlines():
        if line.strip().startswith("FOREACH") and line.rstrip().endswith(
            f"| REMOVE i:{label})"
        ):
            return line.strip()
    return ""


@dataclass(frozen=True)
class NodeWithConditionalLabelSchema(CartographyNodeSchema):
    """Test schema with a conditional label."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            RESOURCE,
            CRITICAL.when(severity="high"),
        ]
    )


@dataclass(frozen=True)
class NodeWithMultipleConditionalLabelsSchema(CartographyNodeSchema):
    """Test schema with multiple conditional labels."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            RESOURCE,
            AWS_RESOURCE,
            CRITICAL.when(severity="high"),
            PUBLIC_RESOURCE.when(is_public="true", severity="high"),
        ]
    )


@dataclass(frozen=True)
class NodeWithOnlyConditionalLabelSchema(CartographyNodeSchema):
    """Test schema with only conditional labels (no string labels)."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            CRITICAL.when(severity="high"),
        ]
    )


@dataclass(frozen=True)
class NodeWithNoExtraLabelsSchema(CartographyNodeSchema):
    """Test schema without extra labels."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()


def test_build_ingestion_query_excludes_conditional_labels_from_set_clause():
    """
    Test that conditional labels are excluded from the unconditional SET clause.
    Only unconditional labels should appear there.
    """

    query = build_ingestion_query(NodeWithConditionalLabelSchema())

    # The SET clause should contain the unconditional label "Resource"
    assert "i:Resource" in _set_clause(query)
    # The SET clause should NOT contain the conditional label "Critical"
    assert "Critical" not in _set_clause(query)
    assert "i:Resource:Critical" not in query


def test_build_ingestion_query_with_multiple_conditional_labels():
    """
    Test that only unconditional labels appear in the SET clause when there are
    multiple conditional labels mixed with unconditional ones.
    """
    query = build_ingestion_query(NodeWithMultipleConditionalLabelsSchema())

    # Should contain unconditional labels
    assert "i:Resource:AWSResource" in _set_clause(query)
    # Should NOT contain conditional labels
    assert "Critical" not in _set_clause(query)
    assert "PublicResource" not in _set_clause(query)


def test_build_ingestion_query_with_only_conditional_labels():
    """
    Test that when all extra labels are conditional, no extra labels
    appear in the SET clause.
    """
    query = build_ingestion_query(NodeWithOnlyConditionalLabelSchema())

    assert "Critical" not in _set_clause(query)


def test_conditional_label_single_condition():
    """
    Test that a conditional label with a single condition is applied per row with a
    matching pair of FOREACH clauses.
    """
    query = build_ingestion_query(NodeWithConditionalLabelSchema())

    assert (
        _apply_clause(query, "Critical")
        == 'FOREACH (_ IN CASE WHEN i.severity = "high" THEN [1] ELSE [] END | SET i:Critical)'
    )
    assert (
        _remove_clause(query, "Critical")
        == 'FOREACH (_ IN CASE WHEN i.severity = "high" THEN [] ELSE [1] END | REMOVE i:Critical)'
    )
    # 1 conditional label = 1 apply clause + 1 remove clause.
    assert query.count("FOREACH") == 2


def test_conditional_label_multiple_conditions_are_anded():
    """
    Test that several conditions on one label declaration are ANDed together, and that each
    conditional label gets its own FOREACH pair.
    """
    query = build_ingestion_query(NodeWithMultipleConditionalLabelsSchema())

    # 2 conditional labels = 4 FOREACH clauses.
    assert query.count("FOREACH") == 4

    assert (
        _apply_clause(query, "Critical")
        == 'FOREACH (_ IN CASE WHEN i.severity = "high" THEN [1] ELSE [] END | SET i:Critical)'
    )

    public_apply = _apply_clause(query, "PublicResource")
    assert 'i.is_public = "true"' in public_apply
    assert 'i.severity = "high"' in public_apply
    assert " AND " in public_apply

    # The remove clause negates the same predicate by swapping the CASE branches, so that a node
    # whose condition property is missing (null predicate) still loses the stale label.
    public_remove = _remove_clause(query, "PublicResource")
    assert public_remove == public_apply.replace(
        "THEN [1] ELSE [] END | SET i:PublicResource",
        "THEN [] ELSE [1] END | REMOVE i:PublicResource",
    )


def test_conditional_label_declarations_sharing_a_label_are_ored():
    """
    Test that two declarations of the same label produce a single FOREACH pair whose predicate ORs
    the two condition groups, rather than two pairs that would clobber each other.
    """

    @dataclass(frozen=True)
    class NodeWithSharedLabelSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                CRITICAL.when(severity="high"),
                CRITICAL.when(severity="urgent"),
            ]
        )

    query = build_ingestion_query(NodeWithSharedLabelSchema())

    assert query.count("FOREACH") == 2
    assert (
        _apply_clause(query, "Critical")
        == 'FOREACH (_ IN CASE WHEN (i.severity = "high") OR (i.severity = "urgent") '
        "THEN [1] ELSE [] END | SET i:Critical)"
    )
    assert (
        _remove_clause(query, "Critical")
        == 'FOREACH (_ IN CASE WHEN (i.severity = "high") OR (i.severity = "urgent") '
        "THEN [] ELSE [1] END | REMOVE i:Critical)"
    )


def test_no_conditional_clauses_when_no_extra_labels():
    """
    Test that no FOREACH clauses are emitted when there are no extra labels.
    """
    query = build_ingestion_query(NodeWithNoExtraLabelsSchema())
    assert "FOREACH" not in query


def test_no_conditional_clauses_for_only_unconditional_labels():
    """
    Test that no FOREACH clauses are emitted when every extra label is unconditional.
    """

    @dataclass(frozen=True)
    class NodeWithOnlyUnconditionalLabelsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                RESOURCE,
                AWS_RESOURCE,
            ]
        )

    query = build_ingestion_query(NodeWithOnlyUnconditionalLabelsSchema())
    assert "FOREACH" not in query
    assert "i:Resource:AWSResource" in query


def test_conditional_label_escapes_special_chars():
    """
    Test that special characters in condition values are properly escaped.
    """

    @dataclass(frozen=True)
    class NodeWithSpecialCharsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                SPECIAL.when(severity='value with "quotes" and \\backslash'),
            ]
        )

    query = build_ingestion_query(NodeWithSpecialCharsSchema())

    apply_clause = _apply_clause(query, "Special")
    assert r"\"quotes\"" in apply_clause
    assert r"\\backslash" in apply_clause


def test_build_create_index_queries_includes_conditional_label_indexes():
    """
    Test that index creation covers conditional labels but not their condition fields.
    """
    queries = build_create_index_queries(NodeWithConditionalLabelSchema())

    # Should have index for the primary label
    assert any("TestAsset" in q and "id" in q for q in queries)
    assert any("TestAsset" in q and "lastupdated" in q for q in queries)

    # Should have index for the string extra label
    assert any("Resource" in q and "id" in q for q in queries)

    # Should have index for the conditional label
    assert any("Critical" in q and "id" in q for q in queries)

    # Should NOT index the condition field: conditions are evaluated against the already-bound node
    # of the current row, so there is no lookup for an index to serve.
    assert not any("severity" in q for q in queries)


def test_build_create_index_queries_with_multiple_conditional_labels():
    """
    Test index creation with multiple conditional labels and conditions.
    """
    queries = build_create_index_queries(NodeWithMultipleConditionalLabelsSchema())

    # Should have indexes for both conditional labels
    assert any("Critical" in q and "id" in q for q in queries)
    assert any("PublicResource" in q and "id" in q for q in queries)

    # Should NOT index any condition field
    assert not any("severity" in q for q in queries)
    assert not any("is_public" in q for q in queries)


def test_empty_conditions_apply_label_unconditionally():
    """
    Test that labels with empty conditions land in the SET clause and get no FOREACH pair.
    """

    @dataclass(frozen=True)
    class NodeWithEmptyConditionsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                EMPTY_CONDITION,
                VALID_CONDITION.when(severity="high"),
            ]
        )

    query = build_ingestion_query(NodeWithEmptyConditionsSchema())

    assert "i:EmptyCondition" in _set_clause(query)
    assert query.count("FOREACH") == 2
    assert "EmptyCondition" not in query.split(_set_clause(query))[1]
    assert _apply_clause(query, "ValidCondition")
    assert _remove_clause(query, "ValidCondition")


def test_label_declared_both_unconditionally_and_conditionally_is_never_removed():
    """
    Test that a label declared both with and without conditions is applied unconditionally and gets
    no removal clause. Otherwise the removal clause would strip a label the SET clause just applied.
    """

    @dataclass(frozen=True)
    class NodeWithRedundantConditionSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                CRITICAL,
                CRITICAL.when(severity="high"),
            ]
        )

    query = build_ingestion_query(NodeWithRedundantConditionSchema())

    assert "i:Critical" in _set_clause(query)
    assert "FOREACH" not in query


def test_conditional_labels_are_not_scoped_by_sub_resource():
    """
    Test that a sub_resource_relationship does not change how conditional labels are applied.

    Conditional labels used to be maintained by post-load queries that had to be scoped to the
    current tenant to avoid touching other tenants' nodes. Applying them per row makes that scoping
    unnecessary: only the nodes in the current batch are ever touched.
    """

    @dataclass(frozen=True)
    class SubResourceRelProperties(CartographyRelProperties):
        lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    @dataclass(frozen=True)
    class TestAssetToAWSAccountRel(CartographyRelSchema):
        target_node_label: str = "AWSAccount"
        target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
            {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
        )
        direction: LinkDirection = LinkDirection.INWARD
        rel_label: str = "RESOURCE"
        properties: SubResourceRelProperties = SubResourceRelProperties()

    @dataclass(frozen=True)
    class ScopedNodeSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        sub_resource_relationship: TestAssetToAWSAccountRel = TestAssetToAWSAccountRel()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                RESOURCE,
                CRITICAL.when(severity="high"),
            ]
        )

    scoped_query = build_ingestion_query(ScopedNodeSchema())
    unscoped_query = build_ingestion_query(NodeWithConditionalLabelSchema())

    assert _apply_clause(scoped_query, "Critical") == _apply_clause(
        unscoped_query, "Critical"
    )
    assert _remove_clause(scoped_query, "Critical") == _remove_clause(
        unscoped_query, "Critical"
    )
    assert scoped_query.count("FOREACH") == 2
