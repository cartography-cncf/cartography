from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_okta_oauth_cli_config(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_OKTA_PRIVATE_KEY", "test-private-key")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "okta",
                "--okta-org-id",
                "acme",
                "--okta-client-id",
                "0oaclient",
                "--okta-private-key-env-var",
                "TEST_OKTA_PRIVATE_KEY",
                "--okta-private-key-id",
                "key-1",
                "--okta-scopes",
                "okta.users.read,okta.groups.read",
                "--okta-disable-dpop",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.okta_org_id == "acme"
    assert config.okta_api_key is None
    assert config.okta_client_id == "0oaclient"
    assert config.okta_private_key == "test-private-key"
    assert config.okta_private_key_id == "key-1"
    assert config.okta_scopes == "okta.users.read,okta.groups.read"
    assert config.okta_dpop_enabled is False


def _run_okta_cli(args):
    cli = cartography.cli.CLI(MagicMock(), "test")
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "okta",
                "--okta-org-id",
                "acme",
                *args,
            ]
        )
    return exit_code, run


def test_okta_cli_rejects_client_id_without_private_key():
    # Act
    exit_code, run = _run_okta_cli(["--okta-client-id", "0oaclient"])

    # Assert
    assert exit_code != 0
    run.assert_not_called()


def test_okta_cli_rejects_empty_private_key_env_var(monkeypatch):
    # Arrange
    monkeypatch.delenv("TEST_OKTA_PRIVATE_KEY", raising=False)

    # Act
    exit_code, run = _run_okta_cli(
        [
            "--okta-client-id",
            "0oaclient",
            "--okta-private-key-env-var",
            "TEST_OKTA_PRIVATE_KEY",
        ]
    )

    # Assert
    assert exit_code != 0
    run.assert_not_called()


def test_okta_cli_rejects_oauth_without_org_id(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_OKTA_PRIVATE_KEY", "test-private-key")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "okta",
                "--okta-client-id",
                "0oaclient",
                "--okta-private-key-env-var",
                "TEST_OKTA_PRIVATE_KEY",
            ]
        )

    # Assert
    assert exit_code != 0
    run.assert_not_called()
