import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp


@patch.object(cartography.intel.gcp, "sync_gcp_organizations", return_value=[])
@patch(
    "cartography.intel.gcp.parse_and_validate_gcp_requested_syncs",
    return_value=["permission_relationships"],
)
def test_selective_sync_warns_permission_relationships_missing_deps(
    mock_validate,
    mock_sync_orgs,
    caplog,
):
    """
    Test that requesting permission_relationships without iam and policy_bindings
    produces a dependency warning.
    """
    config = MagicMock()
    config.gcp_requested_syncs = "permission_relationships"
    config.update_tag = 123456789
    config.gcp_permission_relationships_file = "dummy_path"

    with caplog.at_level(logging.WARNING):
        cartography.intel.gcp.start_gcp_ingestion(
            MagicMock(),
            config,
            credentials=MagicMock(),
        )

    warning_records = [
        r
        for r in caplog.records
        if "permission_relationships" in r.message and "dependencies" in r.message
    ]
    assert len(warning_records) == 1
    assert "iam" in warning_records[0].message
    assert "policy_bindings" in warning_records[0].message
