from dataclasses import dataclass
from typing import Optional

from cartography.graph.querybuilder import build_conditional_label_queries
from cartography.graph.querybuilder import build_create_index_queries
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
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


@dataclass(frozen=True)
class NodeWithConditionalLabelSchema(CartographyNodeSchema):
    """Test schema with a conditional label."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            "Resource",
            ConditionalNodeLabel(label="Critical", conditions={"severity": "high"}),
        ]
    )


@dataclass(frozen=True)
class NodeWithMultipleConditionalLabelsSchema(CartographyNodeSchema):
    """Test schema with multiple conditional labels."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            "Resource",
            "AWSResource",
            ConditionalNodeLabel(label="Critical", conditions={"severity": "high"}),
            ConditionalNodeLabel(
                label="PublicResource",
                conditions={"is_public": "true", "severity": "high"},
            ),
        ]
    )


@dataclass(frozen=True)
class NodeWithOnlyConditionalLabelSchema(CartographyNodeSchema):
    """Test schema with only conditional labels (no string labels)."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            ConditionalNodeLabel(label="Critical", conditions={"severity": "high"}),
        ]
    )


@dataclass(frozen=True)
class NodeWithNoExtraLabelsSchema(CartographyNodeSchema):
    """Test schema without extra labels."""

    label: str = "TestAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()


def test_build_ingestion_query_excludes_conditional_labels():
    """
    Test that conditional labels are excluded from the main ingestion query.
    Only string labels should appear in the SET clause.
    """

    query = build_ingestion_query(NodeWithConditionalLabelSchema())

    # The query should contain the string label "Resource"
    assert "i:Resource" in query
    # The query should NOT contain the conditional label "Critical"
    assert "i:Critical" not in query
    assert "i:Resource:Critical" not in query


def test_build_ingestion_query_with_multiple_conditional_labels():
    """
    Test that only string labels appear in the main query when there are
    multiple conditional labels mixed with string labels.
    """
    query = build_ingestion_query(NodeWithMultipleConditionalLabelsSchema())

    # Should contain string labels
    assert "i:Resource:AWSResource" in query
    # Should NOT contain conditional labels
    assert "Critical" not in query
    assert "PublicResource" not in query


def test_build_ingestion_query_with_only_conditional_labels():
    """
    Test that when all extra labels are conditional, no extra labels
    appear in the SET clause.
    """
    query = build_ingestion_query(NodeWithOnlyConditionalLabelSchema())

    # Should NOT contain any extra labels in SET clause
    # (no "i:SomeLabel" pattern after the property settings)
    assert "i:Critical" not in query


def test_build_conditional_label_queries_single_condition():
    """
    Test building a conditional label query with a single condition.
    Each conditional label generates 2 queries: REMOVE then SET.
    """
    queries = build_conditional_label_queries(NodeWithConditionalLabelSchema())

    # 1 conditional label = 2 queries (remove + set)
    assert len(queries) == 2

    # First query should remove the label from all nodes that have it
    remove_query = queries[0]
    assert "MATCH (n:TestAsset:Critical)" in remove_query
    assert "REMOVE n:Critical" in remove_query

    # Second query should set the label on matching nodes
    set_query = queries[1]
    assert "MATCH (n:TestAsset)" in set_query
    assert 'n.severity = "high"' in set_query
    assert "SET n:Critical" in set_query


def test_build_conditional_label_queries_multiple_conditions():
    """
    Test building conditional label queries with multiple conditions.
    Each conditional label generates 2 queries: REMOVE then SET.
    """
    queries = build_conditional_label_queries(NodeWithMultipleConditionalLabelsSchema())

    # 2 conditional labels = 4 queries (2 x (remove + set))
    assert len(queries) == 4

    # First conditional label: Critical (queries 0 and 1)
    critical_remove = queries[0]
    assert "MATCH (n:TestAsset:Critical)" in critical_remove
    assert "REMOVE n:Critical" in critical_remove

    critical_set = queries[1]
    assert "MATCH (n:TestAsset)" in critical_set
    assert 'n.severity = "high"' in critical_set
    assert "SET n:Critical" in critical_set

    # Second conditional label: PublicResource (queries 2 and 3)
    public_remove = queries[2]
    assert "MATCH (n:TestAsset:PublicResource)" in public_remove
    assert "REMOVE n:PublicResource" in public_remove

    public_set = queries[3]
    assert "MATCH (n:TestAsset)" in public_set
    assert 'n.is_public = "true"' in public_set
    assert 'n.severity = "high"' in public_set
    assert "SET n:PublicResource" in public_set
    # Multiple conditions should be joined with AND
    assert " AND " in public_set


def test_build_conditional_label_queries_no_extra_labels():
    """
    Test that an empty list is returned when there are no extra labels.
    """
    queries = build_conditional_label_queries(NodeWithNoExtraLabelsSchema())
    assert queries == []


def test_build_conditional_label_queries_only_string_labels():
    """
    Test that an empty list is returned when there are only string labels.
    """

    @dataclass(frozen=True)
    class NodeWithOnlyStringLabelsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                "Resource",
                "AWSResource",
            ]
        )

    queries = build_conditional_label_queries(NodeWithOnlyStringLabelsSchema())
    assert queries == []


def test_build_conditional_label_queries_escapes_special_chars():
    """
    Test that special characters in condition values are properly escaped.
    """

    @dataclass(frozen=True)
    class NodeWithSpecialCharsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                ConditionalNodeLabel(
                    label="Special",
                    conditions={"severity": 'value with "quotes" and \\backslash'},
                ),
            ]
        )

    queries = build_conditional_label_queries(NodeWithSpecialCharsSchema())

    # 1 conditional label = 2 queries (remove + set)
    assert len(queries) == 2
    # Check the SET query (second one) for escaped values
    set_query = queries[1]
    # Check that quotes and backslashes are escaped
    assert r"\"quotes\"" in set_query
    assert r"\\backslash" in set_query


def test_build_create_index_queries_includes_conditional_label_indexes():
    """
    Test that index creation includes indexes for conditional labels
    and their condition fields.
    """
    queries = build_create_index_queries(NodeWithConditionalLabelSchema())

    # Should have index for the primary label
    assert any("TestAsset" in q and "id" in q for q in queries)
    assert any("TestAsset" in q and "lastupdated" in q for q in queries)

    # Should have index for the string extra label
    assert any("Resource" in q and "id" in q for q in queries)

    # Should have index for the conditional label
    assert any("Critical" in q and "id" in q for q in queries)

    # Should have index for the condition field on the primary label
    assert any("TestAsset" in q and "severity" in q for q in queries)


def test_build_create_index_queries_with_multiple_conditional_labels():
    """
    Test index creation with multiple conditional labels and conditions.
    """
    queries = build_create_index_queries(NodeWithMultipleConditionalLabelsSchema())

    # Should have indexes for both conditional labels
    assert any("Critical" in q and "id" in q for q in queries)
    assert any("PublicResource" in q and "id" in q for q in queries)

    # Should have indexes for all condition fields
    assert any("TestAsset" in q and "severity" in q for q in queries)
    assert any("TestAsset" in q and "is_public" in q for q in queries)


def test_build_conditional_label_queries_empty_conditions_skipped():
    """
    Test that conditional labels with empty conditions are skipped
    and don't generate invalid Cypher.
    """

    @dataclass(frozen=True)
    class NodeWithEmptyConditionsSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                ConditionalNodeLabel(label="EmptyCondition", conditions={}),
                ConditionalNodeLabel(
                    label="ValidCondition", conditions={"severity": "high"}
                ),
            ]
        )

    queries = build_conditional_label_queries(NodeWithEmptyConditionsSchema())

    # Should only have 2 queries for the valid conditional label (remove + set)
    assert len(queries) == 2
    # Should NOT contain EmptyCondition in any query
    assert all("EmptyCondition" not in q for q in queries)
    # Should contain ValidCondition
    assert "REMOVE n:ValidCondition" in queries[0]
    assert "SET n:ValidCondition" in queries[1]


def test_build_conditional_label_queries_scoped_by_sub_resource():
    """
    Test that conditional label queries are scoped to the sub-resource
    when a sub_resource_relationship is defined on the schema.
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
                "Resource",
                ConditionalNodeLabel(label="Critical", conditions={"severity": "high"}),
            ]
        )

    queries = build_conditional_label_queries(ScopedNodeSchema())

    assert len(queries) == 2

    # REMOVE query should be scoped to the sub-resource
    remove_query = queries[0]
    assert "MATCH (n:TestAsset:Critical)" in remove_query
    # Should have the relationship pattern to AWSAccount (INWARD direction)
    assert "<-[:RESOURCE]-" in remove_query
    assert "(sub:AWSAccount{" in remove_query
    assert "id: $AWS_ID" in remove_query
    assert "REMOVE n:Critical" in remove_query

    # SET query should also be scoped to the sub-resource
    set_query = queries[1]
    assert "MATCH (n:TestAsset)" in set_query
    assert "<-[:RESOURCE]-" in set_query
    assert "(sub:AWSAccount{" in set_query
    assert "id: $AWS_ID" in set_query
    assert 'n.severity = "high"' in set_query
    assert "SET n:Critical" in set_query


def test_build_conditional_label_queries_scoped_outward_direction():
    """
    Test that conditional label queries handle OUTWARD direction correctly.
    """

    @dataclass(frozen=True)
    class SubResourceRelProperties(CartographyRelProperties):
        lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    @dataclass(frozen=True)
    class TestAssetToTenantRel(CartographyRelSchema):
        target_node_label: str = "Tenant"
        target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
            {"id": PropertyRef("tenant_id", set_in_kwargs=True)},
        )
        direction: LinkDirection = LinkDirection.OUTWARD
        rel_label: str = "BELONGS_TO"
        properties: SubResourceRelProperties = SubResourceRelProperties()

    @dataclass(frozen=True)
    class OutwardScopedNodeSchema(CartographyNodeSchema):
        label: str = "TestAsset"
        properties: SimpleNodeProperties = SimpleNodeProperties()
        sub_resource_relationship: TestAssetToTenantRel = TestAssetToTenantRel()
        extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
            [
                ConditionalNodeLabel(label="Critical", conditions={"severity": "high"}),
            ]
        )

    queries = build_conditional_label_queries(OutwardScopedNodeSchema())

    assert len(queries) == 2

    # Both queries should have OUTWARD relationship pattern
    for query in queries:
        assert "-[:BELONGS_TO]->" in query
        assert "(sub:Tenant{" in query
        assert "id: $tenant_id" in query
