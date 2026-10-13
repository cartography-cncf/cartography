import cartography.intel.subimage.modules


def test_transform():
    # Arrange
    raw = {
        "aws": {"is_configured": True, "last_sync_status": "success"},
        "gcp": {"is_configured": False, "last_sync_status": None},
    }

    # Act
    result = cartography.intel.subimage.modules.transform(raw)

    # Assert
    assert len(result) == 2
    assert {
        "module_name": "aws",
        "is_configured": True,
        "last_sync_status": "success",
    } in result
    assert {
        "module_name": "gcp",
        "is_configured": False,
        "last_sync_status": None,
    } in result
