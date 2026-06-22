from cartography.driftdetect.schema_docs import compare_schema_docs_to_models
from cartography.driftdetect.schema_docs import DocNode
from cartography.driftdetect.schema_docs import ModelNode
from cartography.driftdetect.schema_docs import ModelRelationship
from cartography.driftdetect.schema_docs import parse_schema_doc_content


def _node(label: str) -> ModelNode:
    return ModelNode(
        label=label,
        module="example",
        properties=("id", "lastupdated"),
        extra_labels=(),
        model_file="cartography/models/example.py",
        model_line=1,
    )


def _relationship(source: str, rel_label: str, target: str) -> ModelRelationship:
    return ModelRelationship(
        rel_label=rel_label,
        source_label=source,
        target_label=target,
        direction="OUTWARD",
        module="example",
        model_file="cartography/models/example.py",
        model_line=10,
        owner_label=source,
        rel_class_name="ExampleRel",
    )


def _doc(content: str) -> tuple[DocNode, ...]:
    return parse_schema_doc_content(
        content,
        module="example",
        doc_file="docs/root/modules/example/schema.md",
    )


def test_explicit_arrow_examples_are_authoritative_relationship_triples() -> None:
    # Arrange
    content = """
### A

| Field | Description |
|-------|-------------|
|**id**| identifier |

#### Relationships
- A has a relationship to B.
  ```cypher
  (:A)-[:REL]->(:B)
  ```
"""

    # Act
    doc_nodes = _doc(content)

    # Assert
    assert doc_nodes[0].relationships[0].source_label == "A"
    assert doc_nodes[0].relationships[0].rel_label == "REL"
    assert doc_nodes[0].relationships[0].target_label == "B"
    assert doc_nodes[0].relationships[0].doc_pattern == "(:A)-[:REL]->(:B)"


def test_reversed_relationship_direction_is_p1_contradiction() -> None:
    # Arrange
    model_nodes = (_node("A"), _node("B"))
    model_relationships = (_relationship("A", "REL", "B"),)
    doc_nodes = _doc(
        """
### B

#### Relationships
- Reversed in docs.
  ```cypher
  (:B)-[:REL]->(:A)
  ```
"""
    )

    # Act
    findings = compare_schema_docs_to_models(
        model_nodes,
        model_relationships,
        doc_nodes,
    )

    # Assert
    assert any(
        finding.severity == "P1"
        and finding.issue_type == "relationship_direction_contradiction"
        and finding.doc_pattern == "(:B)-[:REL]->(:A)"
        and finding.model_pattern == "(:A)-[:REL]->(:B)"
        for finding in findings
    )


def test_missing_docs_relationship_is_coverage_only() -> None:
    # Arrange
    model_nodes = (_node("A"), _node("B"))
    model_relationships = (_relationship("A", "REL", "B"),)
    doc_nodes = _doc(
        """
### A

| Field | Description |
|-------|-------------|
|**id**| identifier |
|lastupdated| timestamp |
"""
    )

    # Act
    findings = compare_schema_docs_to_models(
        model_nodes,
        model_relationships,
        doc_nodes,
    )

    # Assert
    assert any(
        finding.severity == "P2"
        and finding.issue_type == "missing_docs_relationship"
        and finding.model_pattern == "(:A)-[:REL]->(:B)"
        for finding in findings
    )
    assert not any(finding.severity == "P1" for finding in findings)


def test_docs_only_relationship_is_separate_from_contradiction() -> None:
    # Arrange
    model_nodes = (_node("A"), _node("B"))
    model_relationships: tuple[ModelRelationship, ...] = ()
    doc_nodes = _doc(
        """
### A

#### Relationships
- Docs-only relationship.
  ```cypher
  (:A)-[:DOCS_ONLY]->(:B)
  ```
"""
    )

    # Act
    findings = compare_schema_docs_to_models(
        model_nodes,
        model_relationships,
        doc_nodes,
    )

    # Assert
    assert any(
        finding.severity == "P2"
        and finding.issue_type == "docs_only_relationship"
        and finding.doc_pattern == "(:A)-[:DOCS_ONLY]->(:B)"
        for finding in findings
    )
    assert not any(finding.severity == "P1" for finding in findings)


def test_accepted_legacy_docs_label_is_not_unknown_label_contradiction() -> None:
    # Arrange
    model_nodes = (_node("AWSRole"),)
    model_relationships: tuple[ModelRelationship, ...] = ()
    doc_nodes = _doc(
        """
### AWSRole

#### Relationships
- AWS roles can be allowed by legacy Okta groups documented without dataclass models.
  ```cypher
  (:AWSRole)-[:ALLOWED_BY]->(:OktaGroup)
  ```
"""
    )

    # Act
    findings = compare_schema_docs_to_models(
        model_nodes,
        model_relationships,
        doc_nodes,
    )

    # Assert
    assert any(
        finding.severity == "P2"
        and finding.issue_type == "docs_only_relationship"
        and finding.doc_pattern == "(:AWSRole)-[:ALLOWED_BY]->(:OktaGroup)"
        for finding in findings
    )
    assert not any(finding.severity == "P1" for finding in findings)


def test_labels_in_relationship_prose_are_not_authoritative() -> None:
    # Arrange
    content = """
### A

#### Relationships
- A points at B with REL, but this sentence has no explicit arrow pattern.
"""

    # Act
    doc_nodes = _doc(content)

    # Assert
    assert doc_nodes[0].relationships == ()
    assert doc_nodes[0].warnings == ()


def test_multitarget_arrow_examples_expand_to_ordered_triples() -> None:
    # Arrange
    content = """
### A

#### Relationships
- A points to multiple targets.
  ```cypher
  (:A)-[:REL]->(:B,
                :C)
  ```
"""

    # Act
    doc_nodes = _doc(content)

    # Assert
    assert {
        relationship.doc_pattern for relationship in doc_nodes[0].relationships
    } == {
        "(:A)-[:REL]->(:B)",
        "(:A)-[:REL]->(:C)",
    }
