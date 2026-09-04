import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

import cartography.intel.gcp.audit_config
from tests.data.gcp.audit_config import ORG_AUDIT_CONFIGS


def _make_http_error(
    status: int,
    *,
    reason: str | None = None,
    message: str | None = None,
) -> HttpError:
    payload: dict = {"error": {"code": status}}
    if message:
        payload["error"]["message"] = message
    if reason:
        payload["error"]["errors"] = [{"reason": reason}]

    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps(payload).encode("utf-8"))


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


def test_get_project_audit_config_falls_back_to_project_number_on_invalid():
    client = MagicMock()
    string_request = MagicMock()
    number_request = MagicMock()
    client.projects.return_value.getIamPolicy.side_effect = [
        string_request,
        number_request,
    ]

    invalid_error = _make_http_error(400, reason="invalid", message="Invalid resource")

    with patch.object(
        cartography.intel.gcp.audit_config,
        "gcp_api_execute_with_retry",
        side_effect=[invalid_error, {"auditConfigs": [{"service": "allServices"}]}],
    ):
        result = cartography.intel.gcp.audit_config.get_project_audit_config(
            client,
            "test-project",
            "1234567890",
        )

    assert result == [{"service": "allServices"}]
    assert (
        client.projects.return_value.getIamPolicy.call_args_list[0].kwargs["resource"]
        == "projects/test-project"
    )
    assert (
        client.projects.return_value.getIamPolicy.call_args_list[1].kwargs["resource"]
        == "projects/1234567890"
    )


def test_get_project_audit_config_reraises_invalid_without_project_number():
    client = MagicMock()
    client.projects.return_value.getIamPolicy.return_value = MagicMock()
    invalid_error = _make_http_error(400, reason="invalid", message="Invalid resource")

    with patch.object(
        cartography.intel.gcp.audit_config,
        "gcp_api_execute_with_retry",
        side_effect=invalid_error,
    ):
        with pytest.raises(HttpError):
            cartography.intel.gcp.audit_config.get_project_audit_config(
                client,
                "test-project",
                None,
            )


def test_get_project_audit_config_skips_on_forbidden():
    client = MagicMock()
    client.projects.return_value.getIamPolicy.return_value = MagicMock()
    forbidden_error = _make_http_error(403, reason="forbidden", message="Forbidden")

    with patch.object(
        cartography.intel.gcp.audit_config,
        "gcp_api_execute_with_retry",
        side_effect=forbidden_error,
    ):
        result = cartography.intel.gcp.audit_config.get_project_audit_config(
            client,
            "test-project",
            "1234567890",
        )

    assert result is None
