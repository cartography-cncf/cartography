import logging
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.config import Config
from cartography.intel.microsoft import start_microsoft_ingestion


@patch("cartography.intel.microsoft.start_o365_ingestion")
@patch("cartography.intel.microsoft.start_intune_ingestion")
@patch("cartography.intel.microsoft.start_entra_ingestion")
def test_delegated_auth_runs_only_entra(
    mock_start_entra,
    mock_start_intune,
    mock_start_o365,
    caplog,
) -> None:
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_delegated_auth=True,
    )

    # Act
    with caplog.at_level(logging.WARNING):
        start_microsoft_ingestion(MagicMock(), config)

    # Assert
    mock_start_entra.assert_called_once()
    mock_start_intune.assert_not_called()
    mock_start_o365.assert_not_called()
    assert "best-effort Entra-only mode" in caplog.text


@patch("cartography.intel.microsoft.start_o365_ingestion")
@patch("cartography.intel.microsoft.start_intune_ingestion")
@patch("cartography.intel.microsoft.start_entra_ingestion")
def test_requested_syncs_skip_unrequested_intune_and_o365(
    mock_start_entra,
    mock_start_intune,
    mock_start_o365,
) -> None:
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_client_id="client-id",
        microsoft_client_secret="client-secret",
        microsoft_requested_syncs="groups,intune",
    )

    # Act
    start_microsoft_ingestion(MagicMock(), config)

    # Assert
    mock_start_entra.assert_called_once()
    mock_start_intune.assert_called_once()
    mock_start_o365.assert_not_called()
