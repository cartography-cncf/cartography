"""
Unit tests for cartography.rules.runners

These tests focus on verifying that the aggregation logic for findings
correctly sums up from facts → requirements → framework.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.rules.runners import _run_single_finding
from cartography.rules.runners import _run_single_framework
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import FactResult


@patch("cartography.rules.runners._run_fact")
def test_run_single_requirement_aggregates_findings_correctly(mock_run_fact):
    """Test that _run_single_finding correctly aggregates matches from facts."""
    # Arrange
    # Create mock framework
    mock_framework = MagicMock()
    mock_framework.name = "Test Framework"

    # Create mock requirement
    mock_requirement = MagicMock()
    mock_requirement.id = "REQ-001"
    mock_requirement.name = "Test Requirement"
    mock_requirement.requirement_url = "https://example.com/req-001"

    # Create mock finding with 3 facts
    mock_finding = MagicMock()
    mock_finding.id = "finding-1"
    mock_finding.name = "Test Finding"
    mock_finding.description = "Test Description"

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

    mock_finding.facts = (mock_fact1, mock_fact2, mock_fact3)

    # Mock _run_fact to return FactResults with known match counts
    # Fact 1: 5 matches, Fact 2: 3 matches, Fact 3: 7 matches
    # Total should be: 15 matches
    mock_run_fact.side_effect = [
        FactResult(
            fact_id="fact-1",
            fact_name="Fact 1",
            fact_description="Description 1",
            fact_provider="aws",
            matches=[MagicMock() for _ in range(5)],
        ),
        FactResult(
            fact_id="fact-2",
            fact_name="Fact 2",
            fact_description="Description 2",
            fact_provider="aws",
            matches=[MagicMock() for _ in range(3)],
        ),
        FactResult(
            fact_id="fact-3",
            fact_name="Fact 3",
            fact_description="Description 3",
            fact_provider="aws",
            matches=[MagicMock() for _ in range(7)],
        ),
    ]

    # Create counter
    counter = CounterResult()

    # Act
    finding_result, facts_executed = _run_single_finding(
        framework=mock_framework,
        requirement=mock_requirement,
        finding=mock_finding,
        driver=MagicMock(),
        database="neo4j",
        output_format="json",  # Use json to avoid print statements
        neo4j_uri="bolt://localhost:7687",
        counter=counter,
        fact_filter=None,
    )

    # Assert
    # Verify the structure is correct
    assert finding_result.finding_id == "finding-1"
    assert finding_result.finding_name == "Test Finding"

    assert (
        len(finding_result.facts) == 3
    ), f"Expected 3 fact results, got {len(finding_result.facts)}"

    # Verify individual fact matches are preserved
    assert len(finding_result.facts[0].matches) == 5
    assert len(finding_result.facts[1].matches) == 3
    assert len(finding_result.facts[2].matches) == 7

    # Verify facts_executed count
    assert facts_executed == 3, f"Expected 3 facts executed, got {facts_executed}"


@patch("cartography.rules.runners._run_fact")
def test_run_single_requirement_with_zero_findings(mock_run_fact):
    """Test that _run_single_finding correctly handles zero matches."""
    # Arrange
    mock_framework = MagicMock()
    mock_requirement = MagicMock()
    mock_requirement.id = "REQ-002"
    mock_requirement.name = "Empty Requirement"
    mock_requirement.requirement_url = None

    mock_finding = MagicMock()
    mock_finding.id = "finding-empty"
    mock_finding.name = "Empty Finding"
    mock_finding.description = "No results"

    mock_fact = MagicMock()
    mock_fact.id = "fact-empty"
    mock_finding.facts = (mock_fact,)

    # Mock fact with zero matches
    mock_run_fact.return_value = FactResult(
        fact_id="fact-empty",
        fact_name="Empty Fact",
        fact_description="No results",
        fact_provider="aws",
        matches=[],
    )

    counter = CounterResult()

    # Act
    finding_result, facts_executed = _run_single_finding(
        framework=mock_framework,
        requirement=mock_requirement,
        finding=mock_finding,
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        counter=counter,
        fact_filter=None,
    )

    # Assert
    assert len(finding_result.facts) == 1
    assert len(finding_result.facts[0].matches) == 0
    assert facts_executed == 1


@patch("cartography.rules.runners._run_fact")
@patch("cartography.rules.runners.FRAMEWORKS")
def test_run_single_framework_aggregates_across_requirements(
    mock_frameworks, mock_run_fact
):
    """Test that _run_single_framework correctly aggregates matches across requirements."""
    # Arrange
    # Create a test framework with 2 requirements, each with 1 finding
    # Requirement 1, Finding 1: 2 facts with 5 and 3 matches (total: 8)
    # Requirement 2, Finding 1: 3 facts with 2, 4, and 1 matches (total: 7)
    # Framework total should be: 15 matches, 2 findings, 5 facts

    # Requirement 1 setup
    mock_req1_fact1 = MagicMock()
    mock_req1_fact1.id = "req1-fact1"
    mock_req1_fact2 = MagicMock()
    mock_req1_fact2.id = "req1-fact2"

    mock_req1_finding = MagicMock()
    mock_req1_finding.id = "req1-finding1"
    mock_req1_finding.name = "Req1 Finding 1"
    mock_req1_finding.description = "Desc"
    mock_req1_finding.facts = (mock_req1_fact1, mock_req1_fact2)

    mock_req1 = MagicMock()
    mock_req1.id = "REQ-001"
    mock_req1.name = "Requirement 1"
    mock_req1.requirement_url = None
    mock_req1.findings = (mock_req1_finding,)

    # Requirement 2 setup
    mock_req2_fact1 = MagicMock()
    mock_req2_fact1.id = "req2-fact1"
    mock_req2_fact2 = MagicMock()
    mock_req2_fact2.id = "req2-fact2"
    mock_req2_fact3 = MagicMock()
    mock_req2_fact3.id = "req2-fact3"

    mock_req2_finding = MagicMock()
    mock_req2_finding.id = "req2-finding1"
    mock_req2_finding.name = "Req2 Finding 1"
    mock_req2_finding.description = "Desc"
    mock_req2_finding.facts = (mock_req2_fact1, mock_req2_fact2, mock_req2_fact3)

    mock_req2 = MagicMock()
    mock_req2.id = "REQ-002"
    mock_req2.name = "Requirement 2"
    mock_req2.requirement_url = None
    mock_req2.findings = (mock_req2_finding,)

    # Patch the FRAMEWORKS dict to include our test framework
    test_framework = MagicMock()
    test_framework.id = "test-framework"
    test_framework.name = "Test Framework"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req1, mock_req2)
    mock_frameworks.__getitem__.return_value = test_framework

    # Mock _run_fact to return FactResults and update counter like the real function
    def mock_run_fact_impl(
        fact,
        finding,
        requirement,
        framework,
        driver,
        database,
        counter,
        output_format,
        neo4j_uri,
    ):
        # Map fact IDs to match counts
        match_counts = {
            "req1-fact1": 5,
            "req1-fact2": 3,
            "req2-fact1": 2,
            "req2-fact2": 4,
            "req2-fact3": 1,
        }
        count = match_counts.get(fact.id, 0)
        counter.total_matches += count  # Update counter like real function does
        return FactResult(
            fact.id,
            f"Fact {fact.id}",
            "Desc",
            "aws",
            [MagicMock() for _ in range(count)],
        )

    mock_run_fact.side_effect = mock_run_fact_impl

    # Act
    framework_result = _run_single_framework(
        framework_name="test-framework",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter=None,
        finding_filter=None,
        fact_filter=None,
    )

    # Assert
    # Verify framework-level aggregation via counter
    assert framework_result.counter.total_requirements == 2
    assert framework_result.counter.total_findings == 2
    assert framework_result.counter.total_facts == 5
    assert framework_result.counter.total_matches == 15

    # Verify requirement-level structure
    assert len(framework_result.requirements) == 2

    req1_result = framework_result.requirements[0]
    assert req1_result.requirement_id == "REQ-001"
    assert len(req1_result.findings) == 1
    assert len(req1_result.findings[0].facts) == 2

    req2_result = framework_result.requirements[1]
    assert req2_result.requirement_id == "REQ-002"
    assert len(req2_result.findings) == 1
    assert len(req2_result.findings[0].facts) == 3

    # Verify fact-level matches are preserved
    assert len(req1_result.findings[0].facts[0].matches) == 5
    assert len(req1_result.findings[0].facts[1].matches) == 3
    assert len(req2_result.findings[0].facts[0].matches) == 2
    assert len(req2_result.findings[0].facts[1].matches) == 4
    assert len(req2_result.findings[0].facts[2].matches) == 1


@patch("cartography.rules.runners._run_fact")
@patch("cartography.rules.runners.FRAMEWORKS")
def test_run_single_framework_with_requirement_filter(mock_frameworks, mock_run_fact):
    """Test that filtering by requirement still aggregates correctly."""
    # Arrange
    mock_fact1 = MagicMock()
    mock_fact1.id = "fact1"

    mock_finding1 = MagicMock()
    mock_finding1.id = "finding1"
    mock_finding1.name = "Finding 1"
    mock_finding1.description = "Desc"
    mock_finding1.facts = (mock_fact1,)

    mock_req1 = MagicMock()
    mock_req1.id = "KEEP-ME"
    mock_req1.name = "Keep This"
    mock_req1.requirement_url = None
    mock_req1.findings = (mock_finding1,)

    mock_fact2 = MagicMock()
    mock_fact2.id = "fact2"

    mock_finding2 = MagicMock()
    mock_finding2.id = "finding2"
    mock_finding2.name = "Finding 2"
    mock_finding2.description = "Desc"
    mock_finding2.facts = (mock_fact2,)

    mock_req2 = MagicMock()
    mock_req2.id = "FILTER-OUT"
    mock_req2.name = "Filter This"
    mock_req2.requirement_url = None
    mock_req2.findings = (mock_finding2,)

    test_framework = MagicMock()
    test_framework.id = "test-fw"
    test_framework.name = "Test"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req1, mock_req2)
    mock_frameworks.__getitem__.return_value = test_framework

    # Mock _run_fact to update counter like real function
    def mock_run_fact_impl(
        fact,
        finding,
        requirement,
        framework,
        driver,
        database,
        counter,
        output_format,
        neo4j_uri,
    ):
        counter.total_matches += 10
        return FactResult(
            "fact1", "Fact 1", "Desc", "aws", [MagicMock() for _ in range(10)]
        )

    mock_run_fact.side_effect = mock_run_fact_impl

    # Act
    framework_result = _run_single_framework(
        framework_name="test-fw",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter="KEEP-ME",  # Filter to only first requirement
        finding_filter=None,
        fact_filter=None,
    )

    # Assert
    # Verify only the filtered requirement was executed via counter
    assert framework_result.counter.total_requirements == 1
    assert framework_result.counter.total_findings == 1
    assert framework_result.counter.total_facts == 1
    assert framework_result.counter.total_matches == 10

    assert len(framework_result.requirements) == 1
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

    mock_finding = MagicMock()
    mock_finding.id = "finding1"
    mock_finding.name = "Finding 1"
    mock_finding.description = "Desc"
    mock_finding.facts = (mock_fact1, mock_fact2)

    mock_req = MagicMock()
    mock_req.id = "REQ-001"
    mock_req.name = "Requirement"
    mock_req.requirement_url = None
    mock_req.findings = (mock_finding,)

    test_framework = MagicMock()
    test_framework.id = "test-fw"
    test_framework.name = "Test"
    test_framework.version = "1.0"
    test_framework.requirements = (mock_req,)
    mock_frameworks.__getitem__.return_value = test_framework

    # Mock _run_fact to update counter like real function
    def mock_run_fact_impl(
        fact,
        finding,
        requirement,
        framework,
        driver,
        database,
        counter,
        output_format,
        neo4j_uri,
    ):
        counter.total_matches += 7
        return FactResult(
            "KEEP-FACT", "Kept", "Desc", "aws", [MagicMock() for _ in range(7)]
        )

    mock_run_fact.side_effect = mock_run_fact_impl

    # Act
    framework_result = _run_single_framework(
        framework_name="test-fw",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        requirement_filter=None,
        finding_filter=None,
        fact_filter="KEEP-FACT",  # Filter to only first fact
    )

    # Assert
    # Verify only the filtered fact was executed via counter
    assert framework_result.counter.total_facts == 1
    assert framework_result.counter.total_matches == 7

    assert len(framework_result.requirements) == 1
    assert len(framework_result.requirements[0].findings) == 1
    assert len(framework_result.requirements[0].findings[0].facts) == 1
    assert framework_result.requirements[0].findings[0].facts[0].fact_id == "KEEP-FACT"
