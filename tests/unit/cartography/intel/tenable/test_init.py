from types import SimpleNamespace
from unittest.mock import MagicMock

import cartography.intel.tenable as tenable

TEST_UPDATE_TAG = 123456789


def _config(**overrides):
    values = {
        "tenable_access_key": "access-key",
        "tenable_secret_key": "secret-key",
        "tenable_findings_lookback_days": 180,
        "tenable_url": None,
        "tenable_tenant_id": None,
        "update_tag": TEST_UPDATE_TAG,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_start_tenable_ingestion_skips_when_credentials_are_missing(mocker):
    # Arrange
    mock_session = mocker.patch.object(tenable, "get_tenable_session")
    mock_assets_sync = mocker.patch.object(tenable.assets, "sync")
    mock_findings_sync = mocker.patch.object(tenable.findings, "sync")

    # Act
    tenable.start_tenable_ingestion(
        MagicMock(),
        _config(tenable_access_key=None),
    )

    # Assert
    mock_session.assert_not_called()
    mock_assets_sync.assert_not_called()
    mock_findings_sync.assert_not_called()


def test_start_tenable_ingestion_skips_when_lookback_is_invalid(mocker):
    # Arrange
    mock_session = mocker.patch.object(tenable, "get_tenable_session")
    mock_assets_sync = mocker.patch.object(tenable.assets, "sync")
    mock_findings_sync = mocker.patch.object(tenable.findings, "sync")

    # Act
    tenable.start_tenable_ingestion(
        MagicMock(),
        _config(tenable_findings_lookback_days=0),
    )

    # Assert
    mock_session.assert_not_called()
    mock_assets_sync.assert_not_called()
    mock_findings_sync.assert_not_called()


def test_start_tenable_ingestion_derives_tenant_id_from_default_url(mocker):
    # Arrange
    neo4j_session = MagicMock()
    api_session = MagicMock()
    mocker.patch.object(tenable, "get_tenable_session", return_value=api_session)
    mock_assets_sync = mocker.patch.object(tenable.assets, "sync")
    mock_findings_sync = mocker.patch.object(tenable.findings, "sync")
    mock_metadata = mocker.patch.object(tenable, "merge_module_sync_metadata")

    # Act
    tenable.start_tenable_ingestion(neo4j_session, _config())

    # Assert
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": "cloud.tenable.com",
    }
    mock_assets_sync.assert_called_once_with(
        neo4j_session,
        api_session,
        tenable.TENABLE_DEFAULT_URL,
        "cloud.tenable.com",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    mock_findings_sync.assert_called_once_with(
        neo4j_session,
        api_session,
        tenable.TENABLE_DEFAULT_URL,
        "cloud.tenable.com",
        TEST_UPDATE_TAG,
        common_job_parameters,
        lookback_days=180,
    )
    mock_metadata.assert_called_once_with(
        neo4j_session,
        group_type="TenableTenant",
        group_id="cloud.tenable.com",
        synced_type="TenableData",
        update_tag=TEST_UPDATE_TAG,
        stat_handler=tenable.stat_handler,
    )


def test_start_tenable_ingestion_uses_explicit_url_and_tenant_id(mocker):
    # Arrange
    neo4j_session = MagicMock()
    api_session = MagicMock()
    mock_session_factory = mocker.patch.object(
        tenable,
        "get_tenable_session",
        return_value=api_session,
    )
    mock_assets_sync = mocker.patch.object(tenable.assets, "sync")
    mock_findings_sync = mocker.patch.object(tenable.findings, "sync")
    mocker.patch.object(tenable, "merge_module_sync_metadata")
    config = _config(
        tenable_url="https://tenable.example.test/api",
        tenable_tenant_id="tenant-1",
        tenable_findings_lookback_days=30,
    )

    # Act
    tenable.start_tenable_ingestion(neo4j_session, config)

    # Assert
    mock_session_factory.assert_called_once_with("access-key", "secret-key")
    assert mock_assets_sync.call_args.args[3] == "tenant-1"
    assert mock_findings_sync.call_args.args[3] == "tenant-1"
    assert mock_findings_sync.call_args.kwargs["lookback_days"] == 30
