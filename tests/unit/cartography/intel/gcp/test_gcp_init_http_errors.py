import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

import cartography.intel.gcp


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


def _make_serviceusage_client(enabled_services: list[str] | None = None) -> MagicMock:
    client = MagicMock()
    request = MagicMock()
    request.execute.return_value = {
        "services": [
            {"config": {"name": service_name}}
            for service_name in (enabled_services or [])
        ]
    }
    client.services.return_value.list.return_value = request
    client.services.return_value.list_next.return_value = None
    return client


def _make_serviceusage_client_error(error: HttpError) -> MagicMock:
    client = MagicMock()
    request = MagicMock()
    request.execute.side_effect = error
    client.services.return_value.list.return_value = request
    return client


def _make_cai_client_error(error: HttpError) -> MagicMock:
    client = MagicMock()
    request = MagicMock()
    request.execute.side_effect = error
    client.assets.return_value.list.return_value = request
    return client


class TestServicesEnabledOnProjectHttpErrors:
    def test_returns_empty_set_for_http_error(self):
        serviceusage = _make_serviceusage_client_error(
            _make_http_error(403, reason="forbidden", message="Permission denied"),
        )

        assert (
            cartography.intel.gcp._services_enabled_on_project(
                serviceusage,
                "test-project",
            )
            == set()
        )


class TestSyncProjectResourcesCaiFallbackHttpErrors:
    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(403, reason="forbidden", message="Permission denied"),
            _make_http_error(
                403,
                reason="accessNotConfigured",
                message="Cloud Asset API is disabled",
            ),
            _make_http_error(
                403,
                reason="rateLimitExceeded",
                message="Quota exceeded for quota metric",
            ),
        ],
    )
    def test_skips_cai_fallback_without_cleanup(self, error):
        common_job_parameters = {"UPDATE_TAG": 123}
        credentials = MagicMock()
        neo4j_session = MagicMock()

        serviceusage_client = _make_serviceusage_client()
        cai_client = _make_cai_client_error(error)

        def _build_client(service_name, version, credentials):
            if service_name == "serviceusage":
                return serviceusage_client
            if service_name == "cloudasset":
                return cai_client
            raise AssertionError(f"Unexpected client request: {service_name} {version}")

        with patch("cartography.intel.gcp.build_client", side_effect=_build_client):
            cartography.intel.gcp._sync_project_resources(
                neo4j_session,
                [{"projectId": "test-project"}],
                123,
                common_job_parameters,
                credentials,
                requested_syncs={"iam"},
            )

        assert neo4j_session.mock_calls == []
        assert "PROJECT_ID" not in common_job_parameters

    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(500, message="Internal error"),
            _make_http_error(503, reason="backendError", message="Backend error"),
        ],
    )
    def test_reraises_unexpected_cai_fallback_errors(self, error):
        common_job_parameters = {"UPDATE_TAG": 123}
        credentials = MagicMock()

        serviceusage_client = _make_serviceusage_client()
        cai_client = _make_cai_client_error(error)

        def _build_client(service_name, version, credentials):
            if service_name == "serviceusage":
                return serviceusage_client
            if service_name == "cloudasset":
                return cai_client
            raise AssertionError(f"Unexpected client request: {service_name} {version}")

        with patch("cartography.intel.gcp.build_client", side_effect=_build_client):
            with pytest.raises(HttpError):
                cartography.intel.gcp._sync_project_resources(
                    MagicMock(),
                    [{"projectId": "test-project"}],
                    123,
                    common_job_parameters,
                    credentials,
                    requested_syncs={"iam"},
                )
