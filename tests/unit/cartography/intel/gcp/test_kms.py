import json
import logging
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.gcp import kms
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


def test_sync_kms_billing_disabled_key_rings_skips_cleanup(monkeypatch, caplog):
    neo4j_session = MagicMock()
    client = MagicMock()
    request = MagicMock()
    client.projects.return_value.locations.return_value.keyRings.return_value.list.return_value = (
        request
    )

    cleanup_called = False
    load_key_rings_called = False
    load_crypto_keys_called = False

    billing_error = _make_http_error(
        400,
        {
            "error": {
                "message": "Billing is disabled for project 123456789",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "BILLING_DISABLED",
                    }
                ],
            }
        },
    )

    def _mock_cleanup(*args, **kwargs):
        nonlocal cleanup_called
        cleanup_called = True

    def _mock_load_key_rings(*args, **kwargs):
        nonlocal load_key_rings_called
        load_key_rings_called = True

    def _mock_load_crypto_keys(*args, **kwargs):
        nonlocal load_crypto_keys_called
        load_crypto_keys_called = True

    monkeypatch.setattr(
        "cartography.intel.gcp.kms.get_kms_locations",
        lambda _client, _project_id: [{"locationId": "us-central1"}],
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.kms.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(billing_error),
    )
    monkeypatch.setattr("cartography.intel.gcp.kms.cleanup_kms", _mock_cleanup)
    monkeypatch.setattr(
        "cartography.intel.gcp.kms.load_key_rings",
        _mock_load_key_rings,
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.kms.load_crypto_keys",
        _mock_load_crypto_keys,
    )

    with caplog.at_level(logging.WARNING):
        kms.sync(
            neo4j_session,
            client,
            "test-project",
            123,
            {"PROJECT_ID": "test-project", "UPDATE_TAG": 123},
        )

    assert not cleanup_called
    assert not load_key_rings_called
    assert not load_crypto_keys_called
    assert (
        "Billing is disabled for project test-project while listing KMS key rings. "
        "Skipping KMS sync to preserve existing data."
    ) in caplog.text
    assert "HTTP 400 BILLING_DISABLED" in caplog.text
    assert "googleapiclient.errors.HttpError" not in caplog.text


def test_sync_kms_api_disabled_locations_skips_cleanup(monkeypatch, caplog):
    cleanup_called = False
    load_key_rings_called = False

    def _mock_cleanup(*args, **kwargs):
        nonlocal cleanup_called
        cleanup_called = True

    def _mock_load_key_rings(*args, **kwargs):
        nonlocal load_key_rings_called
        load_key_rings_called = True

    monkeypatch.setattr(
        "cartography.intel.gcp.kms.get_kms_locations",
        lambda _client, _project_id: None,
    )
    monkeypatch.setattr("cartography.intel.gcp.kms.cleanup_kms", _mock_cleanup)
    monkeypatch.setattr(
        "cartography.intel.gcp.kms.load_key_rings",
        _mock_load_key_rings,
    )

    with caplog.at_level(logging.INFO):
        kms.sync(
            MagicMock(),
            MagicMock(),
            "test-project",
            123,
            {"PROJECT_ID": "test-project", "UPDATE_TAG": 123},
        )

    assert not cleanup_called
    assert not load_key_rings_called
