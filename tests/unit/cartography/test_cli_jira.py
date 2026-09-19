from unittest.mock import Mock
from unittest.mock import patch

from cartography.cli import CLI


def test_jira_cli_resolves_token_environment_and_options(monkeypatch):
    # Arrange
    monkeypatch.setenv("CUSTOM_JIRA_TOKEN", "test-token")
    cli = CLI(Mock(), "test")
    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "jira",
                "--jira-cloud-id",
                "11111111-1111-4111-8111-111111111111",
                "--jira-email",
                "reader@example.com",
                "--jira-api-token-env-var",
                "CUSTOM_JIRA_TOKEN",
                "--jira-site-url",
                "https://example.atlassian.net",
            ]
        )
    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.jira_api_token == "test-token"
    assert config.jira_cloud_id == "11111111-1111-4111-8111-111111111111"
    assert config.jira_email == "reader@example.com"
    assert config.jira_site_url == "https://example.atlassian.net"
