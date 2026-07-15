from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from cartography.rules.cli import _framework_sort_key
from cartography.rules.cli import app
from cartography.rules.cli import complete_facts
from cartography.rules.cli import complete_rules
from cartography.rules.spec.model import Framework

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


def test_list_command_includes_framework_control_title_when_present():
    result = runner.invoke(app, ["list", "--framework", "CIS:kubernetes:1.12"])

    assert result.exit_code == 0
    assert (
        "- cis:kubernetes:1.12 (5.1.8) Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
        in result.stdout
    )
    assert "  Name:         Bind/Impersonate/Escalate Permissions" in result.stdout


def test_list_command_invalid_framework_exits():
    result = runner.invoke(app, ["list", "--framework", "missing-framework"])

    assert result.exit_code == 1
    assert "No rules found matching the filter." in result.stderr


def test_frameworks_command_includes_control_titles_when_present():
    result = runner.invoke(app, ["frameworks"])

    assert result.exit_code == 0
    assert (
        "- cis:kubernetes:1.12 (5.1.8) Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
        in result.stdout
    )


def test_framework_control_sort_key_uses_natural_requirement_order():
    frameworks = [
        Framework("CIS Kubernetes Benchmark", "cis", "5.1.10", "kubernetes", "1.12"),
        Framework("CIS Kubernetes Benchmark", "cis", "5.1.2", "kubernetes", "1.12"),
        Framework("CIS Kubernetes Benchmark", "cis", "5.1.8", "kubernetes", "1.12"),
    ]

    assert [fw.requirement for fw in sorted(frameworks, key=_framework_sort_key)] == [
        "5.1.2",
        "5.1.8",
        "5.1.10",
    ]


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


@patch("cartography.rules.cli.run_rules", return_value=0)
def test_run_command_without_credentials_does_not_prompt(mock_run_rules, monkeypatch):
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    result = runner.invoke(app, ["run", "mfa-missing"])

    assert result.exit_code == 0
    assert "Neo4j password" not in result.output
    assert mock_run_rules.call_args.args[3] is None


@patch("cartography.rules.cli.run_rules", return_value=0)
def test_run_command_uses_default_password_environment_variable(
    mock_run_rules, monkeypatch
):
    monkeypatch.setenv("NEO4J_PASSWORD", "default-password")

    result = runner.invoke(app, ["run", "mfa-missing"])

    assert result.exit_code == 0
    assert mock_run_rules.call_args.args[3] == "default-password"


@patch("cartography.rules.cli.run_rules", return_value=0)
def test_run_command_uses_named_password_environment_variable(
    mock_run_rules, monkeypatch
):
    monkeypatch.setenv("CUSTOM_NEO4J_PASSWORD", "custom-password")

    result = runner.invoke(
        app,
        [
            "run",
            "mfa-missing",
            "--neo4j-password-env-var",
            "CUSTOM_NEO4J_PASSWORD",
        ],
    )

    assert result.exit_code == 0
    assert mock_run_rules.call_args.args[3] == "custom-password"


@patch("cartography.rules.cli.run_rules")
def test_run_command_fails_when_named_password_environment_variable_is_missing(
    mock_run_rules, monkeypatch
):
    monkeypatch.delenv("MISSING_NEO4J_PASSWORD", raising=False)

    result = runner.invoke(
        app,
        [
            "run",
            "mfa-missing",
            "--neo4j-password-env-var",
            "MISSING_NEO4J_PASSWORD",
        ],
    )

    assert result.exit_code == 1
    assert "MISSING_NEO4J_PASSWORD" in result.stderr
    assert "not set or is empty" in result.stderr
    mock_run_rules.assert_not_called()


@patch("cartography.rules.cli.run_rules", return_value=0)
def test_run_command_prompts_only_when_explicitly_requested(mock_run_rules):
    result = runner.invoke(
        app,
        ["run", "mfa-missing", "--neo4j-password-prompt"],
        input="prompt-password\n",
    )

    assert result.exit_code == 0
    assert "Neo4j password" in result.output
    assert mock_run_rules.call_args.args[3] == "prompt-password"


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
