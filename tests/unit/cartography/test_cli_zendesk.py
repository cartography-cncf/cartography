from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_zendesk_cli_config(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_ZENDESK_TOKEN", "test-oauth-token")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "zendesk",
                "--zendesk-subdomain",
                "acme",
                "--zendesk-oauth-token-env-var",
                "TEST_ZENDESK_TOKEN",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.zendesk_subdomain == "acme"
    assert config.zendesk_oauth_token == "test-oauth-token"
