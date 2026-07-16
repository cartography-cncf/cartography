from typer.testing import CliRunner

from cartography.rules.cli import app


def test_rules_cli_runs_against_no_auth_neo4j_without_stdin(neo4j_url, monkeypatch):
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    result = CliRunner().invoke(
        app,
        ["run", "object_storage_public", "--uri", neo4j_url],
        input=None,
    )

    assert result.exit_code == 0, result.output
    assert "Neo4j password" not in result.output
    assert "Rule execution completed" in result.output
