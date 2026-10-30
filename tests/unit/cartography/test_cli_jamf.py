from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.cli


def _run_jamf_cli(*args):
    cli = cartography.cli.CLI(MagicMock(), "test")
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "jamf",
                *args,
            ]
        )
    return exit_code, run


def test_jamf_api_client_cli_config(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_JAMF_CLIENT_SECRET", "test-client-secret")

    # Act
    exit_code, run = _run_jamf_cli(
        "--jamf-base-uri",
        "https://test.jamfcloud.com",
        "--jamf-client-id",
        "test-client-id",
        "--jamf-client-secret-env-var",
        "TEST_JAMF_CLIENT_SECRET",
    )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.jamf_client_id == "test-client-id"
    assert config.jamf_client_secret == "test-client-secret"
    assert config.jamf_password is None


@pytest.mark.parametrize(
    "args",
    [
        # Client ID without a secret.
        [
            "--jamf-base-uri",
            "https://test.jamfcloud.com",
            "--jamf-client-id",
            "test-client-id",
        ],
        # Secret without a client ID.
        [
            "--jamf-base-uri",
            "https://test.jamfcloud.com",
            "--jamf-client-secret-env-var",
            "TEST_JAMF_CLIENT_SECRET",
        ],
        # Secret variable that is not set.
        [
            "--jamf-base-uri",
            "https://test.jamfcloud.com",
            "--jamf-client-id",
            "test-client-id",
            "--jamf-client-secret-env-var",
            "UNSET_JAMF_CLIENT_SECRET",
        ],
        # API client without a base URI.
        [
            "--jamf-client-id",
            "test-client-id",
            "--jamf-client-secret-env-var",
            "TEST_JAMF_CLIENT_SECRET",
        ],
    ],
)
def test_jamf_cli_rejects_incomplete_api_client_settings(monkeypatch, args):
    # Arrange
    monkeypatch.setenv("TEST_JAMF_CLIENT_SECRET", "test-client-secret")
    monkeypatch.delenv("UNSET_JAMF_CLIENT_SECRET", raising=False)

    # Act
    exit_code, run = _run_jamf_cli(*args)

    # Assert
    assert exit_code != 0
    run.assert_not_called()
