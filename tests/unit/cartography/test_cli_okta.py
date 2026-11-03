from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.cli


def _run_okta_cli(*args):
    cli = cartography.cli.CLI(MagicMock(), "test")
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "okta",
                *args,
            ]
        )
    return exit_code, run


def test_okta_oauth_cli_config(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_OKTA_PRIVATE_KEY", "test-private-key")

    # Act
    exit_code, run = _run_okta_cli(
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


@pytest.mark.parametrize(
    "args",
    [
        # Client ID without a private key.
        ["--okta-org-id", "acme", "--okta-client-id", "0oaclient"],
        # Private key variable that is not set.
        [
            "--okta-org-id",
            "acme",
            "--okta-client-id",
            "0oaclient",
            "--okta-private-key-env-var",
            "UNSET_OKTA_PRIVATE_KEY",
        ],
        # OAuth credentials without an org ID.
        [
            "--okta-client-id",
            "0oaclient",
            "--okta-private-key-env-var",
            "TEST_OKTA_PRIVATE_KEY",
        ],
    ],
)
def test_okta_cli_rejects_incomplete_oauth_settings(monkeypatch, args):
    # Arrange
    monkeypatch.setenv("TEST_OKTA_PRIVATE_KEY", "test-private-key")
    monkeypatch.delenv("UNSET_OKTA_PRIVATE_KEY", raising=False)

    # Act
    exit_code, run = _run_okta_cli(*args)

    # Assert
    assert exit_code != 0
    run.assert_not_called()
