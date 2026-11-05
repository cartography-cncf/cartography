from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_tencentcloud_cli_config(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_TENCENTCLOUD_SECRET_KEY", "test-secret-key")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "tencentcloud",
                "--tencentcloud-secret-id",
                "AKIDtest",
                "--tencentcloud-secret-key-env-var",
                "TEST_TENCENTCLOUD_SECRET_KEY",
                "--tencentcloud-regions",
                "ap-guangzhou, ap-singapore",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.tencentcloud_secret_id == "AKIDtest"
    assert config.tencentcloud_secret_key == "test-secret-key"
    assert config.tencentcloud_regions == ["ap-guangzhou", "ap-singapore"]
