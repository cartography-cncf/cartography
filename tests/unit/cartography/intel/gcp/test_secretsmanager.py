import json
import logging
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.gcp.secretsmanager import get_secret_versions
from cartography.intel.gcp.secretsmanager import get_secrets


def _make_http_error(status: int, payload: dict) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


def _make_secretmanager_client() -> tuple[MagicMock, MagicMock]:
    secretmanager = MagicMock()
    req = MagicMock()
    secretmanager.projects.return_value.secrets.return_value.list.return_value = req
    (
        secretmanager.projects.return_value.secrets.return_value.versions.return_value.list.return_value
    ) = req
    return secretmanager, req


def test_get_secrets_returns_empty_when_billing_disabled(monkeypatch):
    secretmanager, _req = _make_secretmanager_client()
    error = _make_http_error(
        403,
        {
            "error": {
                "message": "This API method requires billing to be enabled.",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "BILLING_DISABLED",
                    }
                ],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.secretsmanager.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert get_secrets(secretmanager, "test-project") == []


def test_get_secrets_returns_empty_when_api_disabled(monkeypatch):
    secretmanager, _req = _make_secretmanager_client()
    error = _make_http_error(
        403,
        {
            "error": {
                "message": "Secret Manager API has not been used in project 123 before or it is disabled",
                "errors": [{"reason": "accessNotConfigured"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.secretsmanager.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert get_secrets(secretmanager, "test-project") == []


def test_get_secrets_returns_empty_when_insufficient_permissions(monkeypatch):
    secretmanager, _req = _make_secretmanager_client()
    error = _make_http_error(
        403,
        {
            "error": {
                "message": "User lacks required permissions",
                "errors": [{"reason": "insufficientPermissions"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.secretsmanager.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert get_secrets(secretmanager, "test-project") == []


def test_get_secret_versions_returns_empty_when_iam_permission_denied(monkeypatch):
    secretmanager, _req = _make_secretmanager_client()
    error = _make_http_error(
        403,
        {
            "error": {
                "message": "IAM permission denied",
                "errors": [{"reason": "IAM_PERMISSION_DENIED"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.secretsmanager.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert (
        get_secret_versions(secretmanager, "projects/test-project/secrets/example")
        == []
    )


def test_get_secrets_logs_compact_summary_for_permission_denied(monkeypatch, caplog):
    secretmanager, _req = _make_secretmanager_client()
    error = _make_http_error(
        403,
        {
            "error": {
                "message": "User lacks required permissions",
                "errors": [{"reason": "insufficientPermissions"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.secretsmanager.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with caplog.at_level(logging.WARNING):
        secrets = get_secrets(secretmanager, "test-project")

    assert secrets == []
    assert "HTTP 403 insufficientPermissions" in caplog.text
    assert "googleapiclient.errors.HttpError" not in caplog.text
