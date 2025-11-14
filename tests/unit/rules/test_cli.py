from unittest.mock import MagicMock

from typer.testing import CliRunner

from cartography.rules.cli import app
from cartography.rules.cli import complete_facts
from cartography.rules.cli import complete_findings

runner = CliRunner()


def test_complete_findings_filters_correctly():
    """Test that finding autocomplete filters by prefix correctly."""
    # Arrange
    incomplete = "mfa"

    # Act
    results = list(complete_findings(incomplete))

    # Assert
    # Should return findings starting with "mfa"
    assert len(results) > 0
    assert all(finding_id.startswith("mfa") for finding_id in results)
    assert any(finding_id == "mfa-missing" for finding_id in results)


def test_list_command_invalid_finding_exits():
    """Test that list command with invalid finding exits with error."""
    # Arrange
    invalid_finding = "fake-finding-xyz"

    # Act
    result = runner.invoke(app, ["list", invalid_finding])

    # Assert
    assert result.exit_code == 1
    assert "Unknown finding" in result.stdout or "Unknown finding" in result.stderr


def test_run_command_all_with_filters_fails():
    """Test that 'all' finding cannot be used with fact filters."""
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


def test_complete_facts_needs_valid_finding():
    """Test that fact autocomplete requires valid finding in context."""
    # Arrange - Context with invalid finding
    ctx = MagicMock()
    ctx.params = {"finding": "invalid-finding"}

    # Act
    results = list(complete_facts(ctx, ""))

    # Assert
    # Should return empty list when finding is invalid
    assert len(results) == 0
