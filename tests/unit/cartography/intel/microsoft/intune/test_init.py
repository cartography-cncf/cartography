from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.microsoft.intune import start_intune_ingestion
from cartography.intel.microsoft.intune.reports import IntuneReportExportError


def _build_config() -> MagicMock:
    config = MagicMock()
    config.entra_tenant_id = "tenant-id"
    config.entra_client_id = "client-id"
    config.entra_client_secret = "client-secret"
    config.update_tag = 1234567890
    return config


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
):
    # A failed Intune detected-apps export must not abort the whole Microsoft
    # sync: managed devices and compliance policies still run.
    mock_sync_detected_apps.side_effect = IntuneReportExportError(
        "Intune report export for AppInvAggregate did not complete after 3 "
        "attempt(s).",
    )

    start_intune_ingestion(MagicMock(), _build_config())

    mock_sync_managed_devices.assert_awaited_once()
    mock_sync_detected_apps.assert_awaited_once()
    mock_sync_compliance_policies.assert_awaited_once()
    mock_run_analysis.assert_called_once()


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
def test_unrelated_detected_app_error_still_fails_microsoft_sync(
    mock_credential,
    mock_create_client,
    mock_sync_managed_devices,
    mock_sync_detected_apps,
    mock_sync_compliance_policies,
    mock_run_analysis,
):
    # Only export-boundary failures are tolerated. An error from a later
    # report-processing phase (e.g. loading nodes) must still abort the sync
    # rather than be swallowed as an optional-export skip.
    mock_sync_detected_apps.side_effect = RuntimeError("load failed mid-write")

    with pytest.raises(RuntimeError, match="load failed mid-write"):
        start_intune_ingestion(MagicMock(), _build_config())

    mock_sync_compliance_policies.assert_not_awaited()
    mock_run_analysis.assert_not_called()
