"""
Unit tests for cartography.rules.runners

These tests focus on verifying that the aggregation logic for findings
correctly sums up from facts → findings.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.rules.runners import _run_single_finding
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.result import FactResult


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.FINDINGS")
def test_run_single_finding_aggregates_facts_correctly(mock_run_fact):
    """Test that _run_single_finding correctly aggregates matches from facts."""
    # Arrange
    # Create mock facts
    mock_fact1 = MagicMock(spec=Fact)
    mock_fact1.id = "fact-1"
    mock_fact1.name = "Fact 1"
    mock_fact1.maturity = Maturity.STABLE

    mock_fact2 = MagicMock(spec=Fact)
    mock_fact2.id = "fact-2"
    mock_fact2.name = "Fact 2"
    mock_fact2.maturity = Maturity.STABLE

    mock_fact3 = MagicMock(spec=Fact)
    mock_fact3.id = "fact-3"
    mock_fact3.name = "Fact 3"
    mock_fact3.maturity = Maturity.STABLE

    # Create mock finding with 3 facts
    mock_finding = MagicMock(spec=Finding)
    mock_finding.id = "finding-1"
    mock_finding.name = "Test Finding"
    mock_finding.description = "Test Description"
    mock_finding.facts = (mock_fact1, mock_fact2, mock_fact3)

    # Add to FINDINGS dict
    from cartography.rules.runners import FINDINGS

    FINDINGS["finding-1"] = mock_finding

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

    # Act
    finding_result = _run_single_finding(
        finding_name="finding-1",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",  # Use json to avoid print statements
        neo4j_uri="bolt://localhost:7687",
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


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.FINDINGS")
def test_run_single_finding_with_zero_matches(mock_run_fact):
    """Test that _run_single_finding correctly handles zero matches."""
    # Arrange
    mock_fact = MagicMock(spec=Fact)
    mock_fact.id = "fact-empty"
    mock_fact.maturity = Maturity.STABLE

    mock_finding = MagicMock(spec=Finding)
    mock_finding.id = "finding-empty"
    mock_finding.name = "Empty Finding"
    mock_finding.description = "No results"
    mock_finding.facts = (mock_fact,)

    # Add to FINDINGS dict
    from cartography.rules.runners import FINDINGS

    FINDINGS["finding-empty"] = mock_finding

    # Mock fact with zero matches
    mock_run_fact.return_value = FactResult(
        fact_id="fact-empty",
        fact_name="Empty Fact",
        fact_description="No results",
        fact_provider="aws",
        matches=[],
    )

    # Act
    finding_result = _run_single_finding(
        finding_name="finding-empty",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        fact_filter=None,
    )

    # Assert
    assert len(finding_result.facts) == 1
    assert len(finding_result.facts[0].matches) == 0


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.FINDINGS")
def test_run_single_finding_with_fact_filter(mock_run_fact):
    """Test that filtering by fact works correctly."""
    # Arrange
    mock_fact1 = MagicMock(spec=Fact)
    mock_fact1.id = "KEEP-FACT"
    mock_fact1.maturity = Maturity.STABLE

    mock_fact2 = MagicMock(spec=Fact)
    mock_fact2.id = "FILTER-FACT"
    mock_fact2.maturity = Maturity.STABLE

    mock_finding = MagicMock(spec=Finding)
    mock_finding.id = "finding1"
    mock_finding.name = "Finding 1"
    mock_finding.description = "Desc"
    mock_finding.facts = (mock_fact1, mock_fact2)

    # Add to FINDINGS dict
    from cartography.rules.runners import FINDINGS

    FINDINGS["finding1"] = mock_finding

    # Mock _run_fact to return result and update counter like the real function
    def mock_run_fact_impl(
        fact, finding, driver, database, counter, output_format, neo4j_uri
    ):
        counter.total_matches += 7
        return FactResult(
            "KEEP-FACT", "Kept", "Desc", "aws", [MagicMock() for _ in range(7)]
        )

    mock_run_fact.side_effect = mock_run_fact_impl

    # Act
    finding_result = _run_single_finding(
        finding_name="finding1",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        fact_filter="KEEP-FACT",  # Filter to only first fact
    )

    # Assert
    # Verify only the filtered fact was executed
    assert len(finding_result.facts) == 1
    assert finding_result.facts[0].fact_id == "KEEP-FACT"
    assert finding_result.counter.total_matches == 7
