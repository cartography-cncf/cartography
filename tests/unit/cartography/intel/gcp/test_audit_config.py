import json

import cartography.intel.gcp.audit_config
from tests.data.gcp.audit_config import ORG_AUDIT_CONFIGS


def test_transform_gcp_audit_configs_derives_log_type_booleans():
    configs = cartography.intel.gcp.audit_config.transform_gcp_audit_configs(
        ORG_AUDIT_CONFIGS,
        "organization",
        "organizations/123456789012",
    )

    by_service = {config["service"]: config for config in configs}

    assert by_service["allServices"]["has_admin_read"] is True
    assert by_service["allServices"]["has_data_read"] is True
    assert by_service["allServices"]["has_data_write"] is True

    assert by_service["cloudtasks.googleapis.com"]["has_admin_read"] is False
    assert by_service["cloudtasks.googleapis.com"]["has_data_read"] is True
    assert by_service["cloudtasks.googleapis.com"]["has_data_write"] is False

    assert by_service["empty.googleapis.com"]["has_admin_read"] is False
    assert by_service["empty.googleapis.com"]["has_data_read"] is False
    assert by_service["empty.googleapis.com"]["has_data_write"] is False


def test_transform_gcp_audit_configs_preserves_exempted_members():
    configs = cartography.intel.gcp.audit_config.transform_gcp_audit_configs(
        ORG_AUDIT_CONFIGS,
        "organization",
        "organizations/123456789012",
    )

    exempted_config = next(
        config for config in configs if config["service"] == "exempted.googleapis.com"
    )
    audit_log_configs = json.loads(exempted_config["audit_log_configs_json"])

    assert exempted_config["has_data_read"] is True
    assert audit_log_configs == [
        {
            "logType": "DATA_READ",
            "exemptedMembers": [
                "serviceAccount:test@example.iam.gserviceaccount.com",
            ],
        },
    ]
