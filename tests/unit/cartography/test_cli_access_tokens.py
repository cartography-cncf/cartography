from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_azure_cli_reads_access_token_from_env(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_AZURE_ACCESS_TOKEN", "test-arm-token")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "azure",
                "--azure-access-token-env-var",
                "TEST_AZURE_ACCESS_TOKEN",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.azure_access_token == "test-arm-token"
    assert not config.azure_sp_auth


def test_microsoft_cli_reads_access_token_from_env(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_MICROSOFT_ACCESS_TOKEN", "test-graph-token")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "microsoft",
                "--microsoft-tenant-id",
                "tenant-id",
                "--microsoft-access-token-env-var",
                "TEST_MICROSOFT_ACCESS_TOKEN",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.microsoft_access_token == "test-graph-token"
    assert config.microsoft_delegated_auth is True
