from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.microsoft.intune import start_intune_ingestion


def _build_config() -> MagicMock:
    config = MagicMock()
    config.entra_tenant_id = "tenant-id"
    config.entra_client_id = "client-id"
    config.entra_client_secret = "client-secret"
    config.update_tag = 1234567890
    return config


@pytest.mark.parametrize(
    "export_error",
    [
        TimeoutError("Timed out waiting for export job for AppInvAggregate"),
        RuntimeError("Export job for AppInvAggregate failed."),
    ],
)
@patch("cartography.intel.microsoft.intune.run_scoped_analysis_job")
@patch(
    "cartography.intel.microsoft.intune.sync_compliance_policies",
    new_callable=AsyncMock,
)
@patch(
    "cartography.intel.microsoft.intune.sync_detected_apps",
    new_callable=AsyncMock,
)
@patch(
    "cartography.intel.microsoft.intune.sync_managed_devices",
    new_callable=AsyncMock,
)
@patch("cartography.intel.microsoft.intune.create_graph_service_client")
@patch("cartography.intel.microsoft.intune.ClientSecretCredential")
def test_detected_app_export_failure_does_not_fail_microsoft_sync(
    mock_credential,
    mock_create_client,
    mock_sync_managed_devices,
    mock_sync_detected_apps,
    mock_sync_compliance_policies,
    mock_run_analysis,
    export_error,
):
    # A stalled/failed Intune detected-apps export must not abort the whole
    # Microsoft sync: managed devices and compliance policies still run.
    mock_sync_detected_apps.side_effect = export_error

    start_intune_ingestion(MagicMock(), _build_config())

    mock_sync_managed_devices.assert_awaited_once()
    mock_sync_detected_apps.assert_awaited_once()
    mock_sync_compliance_policies.assert_awaited_once()
    mock_run_analysis.assert_called_once()
