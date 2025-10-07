"""
Unit tests for cartography.rules.runners

These tests focus on verifying that the aggregation logic for findings
correctly sums up from facts → requirements → framework.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.rules.runners import _run_single_framework
from cartography.rules.runners import _run_single_requirement
from cartography.rules.spec.result import FactResult


@patch("cartography.rules.runners._run_fact")
def test_run_single_requirement_aggregates_findings_correctly(mock_run_fact):
    """Test that _run_single_requirement correctly sums findings from facts."""
    # Arrange
    # Create mock framework
    mock_framework = MagicMock()
    mock_framework.name = "Test Framework"

    # Create mock requirement with 3 facts
    mock_requirement = MagicMock()
    mock_requirement.id = "REQ-001"
    mock_requirement.name = "Test Requirement"
    mock_requirement.requirement_url = "https://example.com/req-001"

    # Create 3 mock facts
    mock_fact1 = MagicMock()
    mock_fact1.id = "fact-1"
    mock_fact1.name = "Fact 1"

    mock_fact2 = MagicMock()
    mock_fact2.id = "fact-2"
    mock_fact2.name = "Fact 2"

    mock_fact3 = MagicMock()
    mock_fact3.id = "fact-3"
    mock_fact3.name = "Fact 3"

    mock_requirement.facts = (mock_fact1, mock_fact2, mock_fact3)

    # Mock _run_fact to return FactResults with known finding counts
    # Fact 1: 5 findings, Fact 2: 3 findings, Fact 3: 7 findings
    # Total should be: 15 findings
    mock_run_fact.side_effect = [
        FactResult(
            fact_id="fact-1",
            fact_name="Fact 1",
            fact_description="Description 1",
            fact_provider="aws",
            finding_count=5,
            findings=[],
        ),
        FactResult(
            fact_id="fact-2",
            fact_name="Fact 2",
            fact_description="Description 2",
            fact_provider="aws",
            finding_count=3,
            findings=[],
        ),
        FactResult(
            fact_id="fact-3",
            fact_name="Fact 3",
            fact_description="Description 3",
            fact_provider="aws",
            finding_count=7,
            findings=[],
        ),
    ]

    # Act
    requirement_result, facts_executed = _run_single_requirement(
        requirement=mock_requirement,
        framework=mock_framework,
        driver=MagicMock(),
        database="neo4j",
        output_format="json",  # Use json to avoid print statements
        neo4j_uri="bolt://localhost:7687",
        fact_counter_start=0,
        total_facts=3,
        fact_filter=None,
    )

    # Assert
    # Verify the aggregation is correct
    assert (
        requirement_result.total_findings == 15
    ), f"Expected 15 total findings (5+3+7), got {requirement_result.total_findings}"

    assert (
        requirement_result.total_facts == 3
    ), f"Expected 3 facts, got {requirement_result.total_facts}"

    assert (
        len(requirement_result.facts) == 3
    ), f"Expected 3 fact results, got {len(requirement_result.facts)}"

    # Verify individual fact findings are preserved
    assert requirement_result.facts[0].finding_count == 5
    assert requirement_result.facts[1].finding_count == 3
    assert requirement_result.facts[2].finding_count == 7

    # Verify facts_executed count
    assert facts_executed == 3, f"Expected 3 facts executed, got {facts_executed}"


@patch("cartography.rules.runners._run_fact")
def test_run_single_requirement_with_zero_findings(mock_run_fact):
    """Test that _run_single_requirement correctly handles zero findings."""
    # Arrange
    mock_requirement = MagicMock()
    mock_requirement.id = "REQ-002"
    mock_requirement.name = "Empty Requirement"
    mock_requirement.requirement_url = None

    mock_fact = MagicMock()
    mock_fact.id = "fact-empty"
    mock_requirement.facts = (mock_fact,)

    # Mock fact with zero findings
    mock_run_fact.return_value = FactResult(
        fact_id="fact-empty",
        fact_name="Empty Fact",
        fact_description="No results",
        fact_provider="aws",
        finding_count=0,
        findings=[],
    )

    # Act
    requirement_result, facts_executed = _run_single_requirement(
        requirement=mock_requirement,
        framework=MagicMock(),
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        fact_counter_start=0,
        total_facts=1,
        fact_filter=None,
    )

    # Assert
    assert (
        requirement_result.total_findings == 0
    ), f"Expected 0 findings, got {requirement_result.total_findings}"
    assert requirement_result.total_facts == 1


@patch("cartography.rules.runners._run_fact")
@patch("cartography.rules.runners.FRAMEWORKS")
def test_run_single_framework_aggregates_across_requirements(
    mock_frameworks, mock_run_fact
):
    """Test that _run_single_framework correctly sums findings across requirements."""
    # Arrange
    # Create a test framework with 2 requirements
    # Requirement 1: 2 facts with 5 and 3 findings (total: 8)
    # Requirement 2: 3 facts with 2, 4, and 1 findings (total: 7)
    # Framework total should be: 15 findings

    mock_req1_fact1 = MagicMock()
    mock_req1_fact1.id = "req1-fact1"
    mock_req1_fact2 = MagicMock()
    mock_req1_fact2.id = "req1-fact2"

    mock_req1 = MagicMock()
    mock_req1.id = "REQ-001"
    mock_req1.name = "Requirement 1"
    mock_req1.requirement_url = None
    mock_req1.facts = (mock_req1_fact1, mock_req1_fact2)

    mock_req2_fact1 = MagicMock()
    mock_req2_fact1.id = "req2-fact1"
    mock_req2_fact2 = MagicMock()
    mock_req2_fact2.id = "req2-fact2"
    mock_req2_fact3 = MagicMock()
    mock_req2_fact3.id = "req2-fact3"

    mock_req2 = MagicMock()
    mock_req2.id = "REQ-002"
    mock_req2.name = "Requirement 2"
    mock_req2.requirement_url = None
    mock_req2.facts = (mock_req2_fact1, mock_req2_fact2, mock_req2_fact3)

    # Patch the FRAMEWORKS dict to include our test framework
    test_framework = MagicMock()
    test_framework.id = "test-framework"
    test_framework.name = "Test Framework"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req1, mock_req2)
    mock_frameworks.__getitem__.return_value = test_framework

    # Mock fact results with specific finding counts
    mock_run_fact.side_effect = [
        # Requirement 1 facts
        FactResult("req1-fact1", "Fact 1-1", "Desc", "aws", 5, []),
        FactResult("req1-fact2", "Fact 1-2", "Desc", "aws", 3, []),
        # Requirement 2 facts
        FactResult("req2-fact1", "Fact 2-1", "Desc", "aws", 2, []),
        FactResult("req2-fact2", "Fact 2-2", "Desc", "aws", 4, []),
        FactResult("req2-fact3", "Fact 2-3", "Desc", "aws", 1, []),
    ]

    # Act
    framework_result = _run_single_framework(
        framework_name="test-framework",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter=None,
        fact_filter=None,
    )

    # Assert
    # Verify framework-level aggregation
    assert (
        framework_result.total_findings == 15
    ), f"Expected 15 total findings (5+3+2+4+1), got {framework_result.total_findings}"

    assert (
        framework_result.total_requirements == 2
    ), f"Expected 2 requirements, got {framework_result.total_requirements}"

    assert (
        framework_result.total_facts == 5
    ), f"Expected 5 total facts (2+3), got {framework_result.total_facts}"

    # Verify requirement-level aggregation
    assert len(framework_result.requirements) == 2

    req1_result = framework_result.requirements[0]
    assert (
        req1_result.total_findings == 8
    ), f"Expected Requirement 1 to have 8 findings (5+3), got {req1_result.total_findings}"
    assert req1_result.total_facts == 2

    req2_result = framework_result.requirements[1]
    assert (
        req2_result.total_findings == 7
    ), f"Expected Requirement 2 to have 7 findings (2+4+1), got {req2_result.total_findings}"
    assert req2_result.total_facts == 3

    # Verify fact-level findings are preserved
    assert req1_result.facts[0].finding_count == 5
    assert req1_result.facts[1].finding_count == 3
    assert req2_result.facts[0].finding_count == 2
    assert req2_result.facts[1].finding_count == 4
    assert req2_result.facts[2].finding_count == 1


@patch("cartography.rules.runners._run_fact")
@patch("cartography.rules.runners.FRAMEWORKS")
def test_run_single_framework_with_requirement_filter(mock_frameworks, mock_run_fact):
    """Test that filtering by requirement still aggregates correctly."""
    # Arrange
    mock_req1 = MagicMock()
    mock_req1.id = "KEEP-ME"
    mock_req1.name = "Keep This"
    mock_req1.requirement_url = None

    mock_fact1 = MagicMock()
    mock_fact1.id = "fact1"
    mock_req1.facts = (mock_fact1,)

    mock_req2 = MagicMock()
    mock_req2.id = "FILTER-OUT"
    mock_req2.name = "Filter This"
    mock_req2.requirement_url = None

    mock_fact2 = MagicMock()
    mock_fact2.id = "fact2"
    mock_req2.facts = (mock_fact2,)

    test_framework = MagicMock()
    test_framework.id = "test-fw"
    test_framework.name = "Test"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req1, mock_req2)
    mock_frameworks.__getitem__.return_value = test_framework

    # Only return result for the first fact (since second requirement is filtered out)
    mock_run_fact.return_value = FactResult("fact1", "Fact 1", "Desc", "aws", 10, [])

    # Act
    framework_result = _run_single_framework(
        framework_name="test-fw",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter="KEEP-ME",  # Filter to only first requirement
        fact_filter=None,
    )

    # Assert
    # Verify only the filtered requirement was executed
    assert (
        framework_result.total_requirements == 1
    ), f"Expected 1 requirement after filtering, got {framework_result.total_requirements}"

    assert (
        framework_result.total_findings == 10
    ), f"Expected 10 findings from single requirement, got {framework_result.total_findings}"

    assert (
        framework_result.total_facts == 1
    ), f"Expected 1 fact after filtering, got {framework_result.total_facts}"

    assert framework_result.requirements[0].requirement_id == "KEEP-ME"


@patch("cartography.rules.runners._run_fact")
@patch("cartography.rules.runners.FRAMEWORKS")
def test_run_single_framework_with_fact_filter(mock_frameworks, mock_run_fact):
    """Test that filtering by fact still aggregates correctly."""
    # Arrange
    mock_fact1 = MagicMock()
    mock_fact1.id = "KEEP-FACT"

    mock_fact2 = MagicMock()
    mock_fact2.id = "FILTER-FACT"

    mock_req = MagicMock()
    mock_req.id = "REQ-001"
    mock_req.name = "Requirement"
    mock_req.requirement_url = None
    mock_req.facts = (mock_fact1, mock_fact2)

    test_framework = MagicMock()
    test_framework.id = "test-fw"
    test_framework.name = "Test"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req,)
    mock_frameworks.__getitem__.return_value = test_framework

    # Only one fact result since the second is filtered
    mock_run_fact.return_value = FactResult("KEEP-FACT", "Kept", "Desc", "aws", 7, [])

    # Act
    framework_result = _run_single_framework(
        framework_name="test-fw",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter=None,
        fact_filter="KEEP-FACT",  # Filter to only first fact
    )

    # Assert
    # Verify only the filtered fact was executed
    assert (
        framework_result.total_facts == 1
    ), f"Expected 1 fact after filtering, got {framework_result.total_facts}"

    assert (
        framework_result.total_findings == 7
    ), f"Expected 7 findings from single fact, got {framework_result.total_findings}"

    assert framework_result.requirements[0].total_facts == 1
    assert framework_result.requirements[0].facts[0].fact_id == "KEEP-FACT"
