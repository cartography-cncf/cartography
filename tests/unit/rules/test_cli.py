from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from cartography.rules.cli import app
from cartography.rules.cli import complete_facts
from cartography.rules.cli import complete_frameworks
from cartography.rules.cli import complete_rules
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Rule

runner = CliRunner()


def test_complete_rules_filters_correctly():
    """Test that rule autocomplete filters by prefix correctly."""
    # Arrange
    incomplete = "mfa"

    # Act
    results = list(complete_rules(incomplete))

    # Assert
    # Should return rules starting with "mfa"
    assert len(results) > 0
    assert all(rule_id.startswith("mfa") for rule_id in results)
    assert any(rule_id == "mfa-missing" for rule_id in results)


def test_list_command_invalid_rule_exits():
    """Test that list command with invalid rule exits with error."""
    # Arrange
    invalid_rule = "fake-rule-xyz"

    # Act
    result = runner.invoke(app, ["list", invalid_rule])

    # Assert
    assert result.exit_code == 1
    assert "Unknown rule" in result.stdout or "Unknown rule" in result.stderr


@patch("cartography.rules.cli.get_all_frameworks")
def test_complete_frameworks_supports_family_filters(mock_get_all_frameworks):
    mock_get_all_frameworks.return_value = {
        "cis": [
            Framework(
                name="CIS AWS Foundations Benchmark",
                short_name="CIS",
                scope="aws",
                family="foundations",
                revision="6.0",
                requirement="2.11",
            ),
            Framework(
                name="CIS AWS Compute Services Benchmark",
                short_name="CIS",
                scope="aws",
                family="compute",
                revision="1.1",
                requirement="3.1",
            ),
        ],
    }

    results = list(complete_frameworks("cis:aws"))

    assert "cis:aws" in results
    assert "cis:aws:foundations" in results
    assert "cis:aws:foundations:6.0" in results
    assert "cis:aws:compute" in results
    assert "cis:aws:compute:1.1" in results


def test_run_command_all_with_filters_fails():
    """Test that 'all' rule cannot be used with fact filters."""
    # Act
    result = runner.invoke(
        app,
        ["run", "all", "some-fact", "--neo4j-password-prompt"],
        input="password\n",
    )

    # Assert
    assert result.exit_code == 1
    assert (
        "Cannot filter by fact" in result.stdout
        or "Cannot filter by fact" in result.stderr
    )


def test_complete_facts_needs_valid_rule():
    """Test that fact autocomplete requires valid rule in context."""
    # Arrange - Context with invalid rule
    ctx = MagicMock()
    ctx.params = {"rule": "invalid-rule"}

    # Act
    results = list(complete_facts(ctx, ""))

    # Assert
    # Should return empty list when rule is invalid
    assert len(results) == 0


@patch.dict("cartography.rules.cli.RULES", clear=True)
def test_list_command_filters_by_family():
    rule_foundations = Rule(
        id="rule-foundations",
        name="Foundations Rule",
        description="Foundations",
        version="1.0.0",
        tags=("test",),
        facts=(),
        output_model=MagicMock(),
        frameworks=(
            Framework(
                name="CIS AWS Foundations Benchmark",
                short_name="CIS",
                scope="aws",
                family="foundations",
                revision="6.0",
                requirement="2.11",
            ),
        ),
    )
    rule_compute = Rule(
        id="rule-compute",
        name="Compute Rule",
        description="Compute",
        version="1.0.0",
        tags=("test",),
        facts=(),
        output_model=MagicMock(),
        frameworks=(
            Framework(
                name="CIS AWS Compute Services Benchmark",
                short_name="CIS",
                scope="aws",
                family="compute",
                revision="1.1",
                requirement="3.1",
            ),
        ),
    )

    from cartography.rules.cli import RULES

    RULES[rule_foundations.id] = rule_foundations
    RULES[rule_compute.id] = rule_compute

    result = runner.invoke(app, ["list", "--framework", "CIS:aws:foundations"])

    assert result.exit_code == 0
    assert "rule-foundations" in result.stdout
    assert "cis:aws:foundations:6.0" in result.stdout
    assert "rule-compute" not in result.stdout
