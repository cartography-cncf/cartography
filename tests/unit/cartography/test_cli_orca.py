import unittest.mock
from typing import get_args

import cartography.cli


def test_cli_orca_options_set_config(monkeypatch) -> None:
    # Arrange
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    monkeypatch.setenv("TEST_ORCA_API_TOKEN", "api-token")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "orca",
                "--orca-api-endpoint",
                "https://api.orcasecurity.io",
                "--orca-api-token-env-var",
                "TEST_ORCA_API_TOKEN",
            ],
        )

    # Assert
    assert exit_code == 0
    run_with_config.assert_called_once()
    config = run_with_config.call_args[0][1]
    assert config.orca_api_endpoint == "https://api.orcasecurity.io"
    assert config.orca_api_token == "api-token"


def test_cli_selected_modules_orca_shows_orca_options() -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")

    # Act
    app = cli._build_app(
        cartography.cli._parse_selected_modules_from_argv(
            ["--selected-modules", "orca", "--help"],
        ),
    )
    annotations = app.registered_commands[0].callback.__annotations__

    # Assert
    assert get_args(annotations["orca_api_endpoint"])[1].hidden is False
    assert get_args(annotations["orca_api_token_env_var"])[1].hidden is False


def test_cli_orca_token_uses_default_environment_variable(monkeypatch) -> None:
    # Arrange
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    monkeypatch.setenv("ORCASECURITY_API_TOKEN", "default-env-token")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "orca",
                "--orca-api-endpoint",
                "https://api.orcasecurity.io",
            ],
        )

    # Assert
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.orca_api_token == "default-env-token"
