from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_azure_cli_reads_access_token_from_env(monkeypatch):
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_AZURE_ACCESS_TOKEN", "test-arm-token")

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

    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.azure_access_token == "test-arm-token"
    assert not config.azure_sp_auth


def test_azure_cli_rejects_access_token_with_sp_auth(monkeypatch):
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_AZURE_ACCESS_TOKEN", "test-arm-token")

    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "azure",
                "--azure-sp-auth",
                "--azure-access-token-env-var",
                "TEST_AZURE_ACCESS_TOKEN",
            ]
        )

    assert exit_code != 0
    run.assert_not_called()


def test_azure_cli_rejects_unset_access_token_env_var(monkeypatch):
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.delenv("TEST_AZURE_ACCESS_TOKEN", raising=False)

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

    assert exit_code != 0
    run.assert_not_called()
