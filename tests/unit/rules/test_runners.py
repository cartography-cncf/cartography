"""
Unit tests for cartography.rules.runners

These tests focus on verifying that the aggregation logic for findings
correctly sums up from facts → findings.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.rules.runners import _run_single_rule
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Rule
from cartography.rules.spec.result import FactResult


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.RULES")
def test_run_single_rule_aggregates_facts_correctly(mock_run_fact):
    """Test that _run_single_rule correctly aggregates findings from facts."""
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

    # Create mock rule with 3 facts
    mock_rule = MagicMock(spec=Rule)
    mock_rule.id = "rule-1"
    mock_rule.name = "Test Rule"
    mock_rule.description = "Test Description"
    mock_rule.facts = (mock_fact1, mock_fact2, mock_fact3)

    # Add to RULES dict
    from cartography.rules.runners import RULES

    RULES["rule-1"] = mock_rule

    # Mock _run_fact to return FactResults with known finding counts
    # Fact 1: 5 findings, Fact 2: 3 findings, Fact 3: 7 findings
    # Total should be: 15 findings
    mock_run_fact.side_effect = [
        FactResult(
            fact_id="fact-1",
            fact_name="Fact 1",
            fact_description="Description 1",
            fact_provider="aws",
            findings=[MagicMock() for _ in range(5)],
        ),
        FactResult(
            fact_id="fact-2",
            fact_name="Fact 2",
            fact_description="Description 2",
            fact_provider="aws",
            findings=[MagicMock() for _ in range(3)],
        ),
        FactResult(
            fact_id="fact-3",
            fact_name="Fact 3",
            fact_description="Description 3",
            fact_provider="aws",
            findings=[MagicMock() for _ in range(7)],
        ),
    ]

    # Act
    rule_result = _run_single_rule(
        rule_name="rule-1",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",  # Use json to avoid print statements
        neo4j_uri="bolt://localhost:7687",
        fact_filter=None,
    )

    # Assert
    # Verify the structure is correct
    assert rule_result.rule_id == "rule-1"
    assert rule_result.rule_name == "Test Rule"

    assert (
        len(rule_result.facts) == 3
    ), f"Expected 3 fact results, got {len(rule_result.facts)}"

    # Verify individual fact findings are preserved
    assert len(rule_result.facts[0].findings) == 5
    assert len(rule_result.facts[1].findings) == 3
    assert len(rule_result.facts[2].findings) == 7


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.RULES")
def test_run_single_rule_with_zero_findings(mock_run_fact):
    """Test that _run_single_rule correctly handles zero findings."""
    # Arrange
    mock_fact = MagicMock(spec=Fact)
    mock_fact.id = "fact-empty"
    mock_fact.maturity = Maturity.STABLE

    mock_rule = MagicMock(spec=Rule)
    mock_rule.id = "rule-empty"
    mock_rule.name = "Empty Rule"
    mock_rule.description = "No results"
    mock_rule.facts = (mock_fact,)

    # Add to RULES dict
    from cartography.rules.runners import RULES

    RULES["rule-empty"] = mock_rule

    # Mock fact with zero findings
    mock_run_fact.return_value = FactResult(
        fact_id="fact-empty",
        fact_name="Empty Fact",
        fact_description="No results",
        fact_provider="aws",
        findings=[],
    )

    # Act
    rule_result = _run_single_rule(
        rule_name="rule-empty",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        fact_filter=None,
    )

    # Assert
    assert len(rule_result.facts) == 1
    assert len(rule_result.facts[0].findings) == 0


@patch("cartography.rules.runners._run_fact")
@patch.dict("cartography.rules.runners.RULES")
def test_run_single_rule_with_fact_filter(mock_run_fact):
    """Test that filtering by fact works correctly."""
    # Arrange
    mock_fact1 = MagicMock(spec=Fact)
    mock_fact1.id = "KEEP-FACT"
    mock_fact1.maturity = Maturity.STABLE

    mock_fact2 = MagicMock(spec=Fact)
    mock_fact2.id = "FILTER-FACT"
    mock_fact2.maturity = Maturity.STABLE

    mock_rule = MagicMock(spec=Rule)
    mock_rule.id = "rule1"
    mock_rule.name = "Rule 1"
    mock_rule.description = "Desc"
    mock_rule.facts = (mock_fact1, mock_fact2)

    # Add to RULES dict
    from cartography.rules.runners import RULES

    RULES["rule1"] = mock_rule

    # Mock _run_fact to return result and update counter like the real function
    def mock_run_fact_impl(
        fact, rule, driver, database, counter, output_format, neo4j_uri
    ):
        counter.total_findings += 7
        return FactResult(
            "KEEP-FACT", "Kept", "Desc", "aws", [MagicMock() for _ in range(7)]
        )

    mock_run_fact.side_effect = mock_run_fact_impl

    # Act
    rule_result = _run_single_rule(
        rule_name="rule1",
        driver=MagicMock(),
        database="neo4j",
        output_format="json",
        neo4j_uri="bolt://localhost:7687",
        fact_filter="KEEP-FACT",  # Filter to only first fact
    )

    # Assert
    # Verify only the filtered fact was executed
    assert len(rule_result.facts) == 1
    assert rule_result.facts[0].fact_id == "KEEP-FACT"
    assert rule_result.counter.total_findings == 7
