from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.cli import CLI


@pytest.mark.parametrize(
    "token_env, token_args",
    [
        ("JIRA_API_TOKEN", []),
        ("CUSTOM_JIRA_TOKEN", ["--jira-api-token-env-var", "CUSTOM_JIRA_TOKEN"]),
    ],
)
def test_jira_cli_resolves_token_environment_and_options(
    monkeypatch, token_env, token_args
):
    # Arrange
    monkeypatch.setenv(token_env, "test-token")
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
                *token_args,
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
