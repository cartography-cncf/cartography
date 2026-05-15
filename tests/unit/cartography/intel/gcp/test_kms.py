import json
import logging
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.gcp.kms import get_kms_locations


def _make_http_error(status: int, payload: dict) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


def test_get_kms_locations_api_disabled_logs_concisely(monkeypatch, caplog):
    client = MagicMock()
    request = MagicMock()
    client.projects.return_value.locations.return_value.list.return_value = request

    error = _make_http_error(
        403,
        {
            "error": {
                "message": "Cloud KMS API has not been used in project 123 before or it is disabled",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "SERVICE_DISABLED",
                    }
                ],
            }
        },
    )

    monkeypatch.setattr(
        "cartography.intel.gcp.kms.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with caplog.at_level(logging.WARNING):
        locations = get_kms_locations(client, "test-project")

    assert locations is None
    assert "HTTP 403 SERVICE_DISABLED" in caplog.text
    assert "googleapiclient.errors.HttpError" not in caplog.text
