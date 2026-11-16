from cartography.intel.tenable import assets


def test_asset_export_includes_web_application_assets(mocker):
    # Arrange: Tenable's asset export defaults to `host`, which would leave out the
    # `webapp` assets that Web App Scanning findings point at.
    mock_export = mocker.patch.object(assets, "export_and_download", return_value=[])

    # Act
    assets.get(mocker.MagicMock(), "https://cloud.tenable.com")

    # Assert
    export_params = mock_export.call_args.args[4]
    assert export_params["chunk_size"] == 1000
    assert export_params["filters"]["types"] == ["host", "webapp"]
