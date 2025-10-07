from unittest.mock import MagicMock

from typer.testing import CliRunner

from cartography.rules.cli import app
from cartography.rules.cli import complete_frameworks
from cartography.rules.cli import complete_requirements

runner = CliRunner()


def test_complete_frameworks_filters_correctly():
    """Test that framework autocomplete filters by prefix correctly."""
    # Arrange
    incomplete = "mitre"

    # Act
    results = list(complete_frameworks(incomplete))

    # Assert
    # Should return frameworks starting with "mitre"
    assert len(results) > 0
    assert all(name.startswith("mitre") for name in results)
    assert "mitre-attack" in results


def test_list_command_invalid_framework_exits():
    """Test that list command with invalid framework exits with error."""
    # Arrange
    invalid_framework = "fake-framework-xyz"

    # Act
    result = runner.invoke(app, ["list", invalid_framework])

    # Assert
    assert result.exit_code == 1
    assert "Unknown framework" in result.stdout or "Unknown framework" in result.stderr


def test_run_command_all_with_filters_fails():
    """Test that 'all' framework cannot be used with requirement/fact filters."""
    # Act
    result = runner.invoke(
        app,
        ["run", "all", "T1190", "--neo4j-password-prompt"],
        input="password\n",
    )

    # Assert
    assert result.exit_code == 1
    assert (
        "Cannot filter by requirement/fact" in result.stdout
        or "Cannot filter by requirement/fact" in result.stderr
    )


def test_complete_requirements_needs_valid_framework():
    """Test that requirement autocomplete requires valid framework in context."""
    # Arrange - Context with invalid framework
    ctx = MagicMock()
    ctx.params = {"framework": "invalid-framework"}

    # Act
    results = list(complete_requirements(ctx, ""))

    # Assert
    # Should return empty list when framework is invalid
    assert len(results) == 0
