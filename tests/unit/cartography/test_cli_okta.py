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
