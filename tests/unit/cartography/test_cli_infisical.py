import unittest.mock
from typing import get_args

import cartography.cli


def test_cli_infisical_options_set_config(monkeypatch) -> None:
    # Arrange
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    monkeypatch.setenv("TEST_INFISICAL_CLIENT_ID", "client-id")
    monkeypatch.setenv("TEST_INFISICAL_CLIENT_SECRET", "client-secret")

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
                "infisical",
                "--infisical-api-url",
                "https://app.infisical.example",
                "--infisical-organization-id",
                "org-123",
                "--infisical-client-id-env-var",
                "TEST_INFISICAL_CLIENT_ID",
                "--infisical-client-secret-env-var",
                "TEST_INFISICAL_CLIENT_SECRET",
            ],
        )

    # Assert
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.infisical_api_url == "https://app.infisical.example"
    assert config.infisical_organization_id == "org-123"
    assert config.infisical_client_id == "client-id"
    assert config.infisical_client_secret == "client-secret"


def test_cli_selected_modules_infisical_shows_infisical_options() -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")

    # Act
    app = cli._build_app(
        cartography.cli._parse_selected_modules_from_argv(
            ["--selected-modules", "infisical", "--help"],
        ),
    )
    annotations = app.registered_commands[0].callback.__annotations__

    # Assert
    for option in (
        "infisical_api_url",
        "infisical_organization_id",
        "infisical_client_id_env_var",
        "infisical_client_secret_env_var",
    ):
        assert get_args(annotations[option])[1].hidden is False


def test_cli_infisical_uses_default_environment_variables(monkeypatch) -> None:
    # Arrange
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    monkeypatch.setenv("INFISICAL_CLIENT_ID", "default-client-id")
    monkeypatch.setenv("INFISICAL_CLIENT_SECRET", "default-client-secret")

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
                "infisical",
                "--infisical-organization-id",
                "org-123",
            ],
        )

    # Assert
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.infisical_client_id == "default-client-id"
    assert config.infisical_client_secret == "default-client-secret"
