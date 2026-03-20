import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.compute import get_gcp_instance_responses
from cartography.intel.gcp.compute import get_gcp_regional_forwarding_rules
from cartography.intel.gcp.compute import get_gcp_subnets
from cartography.intel.gcp.compute import get_zones_in_project


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


def _make_request(*, response=None, error: Exception | None = None) -> MagicMock:
    request = MagicMock()
    if error is not None:
        request.execute.side_effect = error
    else:
        request.execute.return_value = response
    return request


class TestGetZonesInProjectHttpErrors:
    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(
                403,
                reason="accessNotConfigured",
                message="Compute Engine API has not been used in project",
            ),
            _make_http_error(403, reason="forbidden", message="Permission denied"),
            _make_http_error(404, reason="notFound", message="Project not found"),
        ],
    )
    def test_returns_none_for_expected_skip_categories(self, error):
        mock_compute = MagicMock()
        request = _make_request(error=error)
        mock_compute.zones.return_value.list.return_value = request

        assert get_zones_in_project("test-project", mock_compute) is None

    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(503, reason="backendError", message="Backend error"),
            _make_http_error(400, reason="invalid", message="Invalid request"),
            _make_http_error(418, message="Unexpected response"),
        ],
    )
    def test_reraises_unexpected_categories(self, error):
        mock_compute = MagicMock()
        request = _make_request(error=error)
        mock_compute.zones.return_value.list.return_value = request

        with patch("time.sleep", return_value=None):
            with pytest.raises(HttpError):
                get_zones_in_project("test-project", mock_compute)


class TestGetGcpInstanceResponsesHttpErrors:
    def test_skips_zone_for_transient_errors(self):
        mock_compute = MagicMock()
        zones = [{"name": "zone-a"}, {"name": "zone-b"}]

        first_request = _make_request(
            error=_make_http_error(
                503,
                reason="backendError",
                message="The service is currently unavailable",
            ),
        )
        success_response = {"id": "projects/test-project/zones/zone-b/instances"}
        second_request = _make_request(response=success_response)
        mock_compute.instances.return_value.list.side_effect = [
            first_request,
            second_request,
        ]

        with patch("time.sleep", return_value=None):
            assert get_gcp_instance_responses("test-project", zones, mock_compute) == [
                success_response
            ]

    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(403, reason="forbidden", message="Permission denied"),
            _make_http_error(400, reason="invalid", message="Invalid request"),
            _make_http_error(418, message="Unexpected response"),
        ],
    )
    def test_reraises_non_transient_errors(self, error):
        mock_compute = MagicMock()
        zones = [{"name": "zone-a"}]
        request = _make_request(error=error)
        mock_compute.instances.return_value.list.return_value = request

        with pytest.raises(HttpError):
            get_gcp_instance_responses("test-project", zones, mock_compute)


class TestGetGcpSubnetsHttpErrors:
    def test_returns_none_for_invalid_region_during_request_creation(self):
        mock_compute = MagicMock()
        mock_compute.subnetworks.return_value.list.side_effect = _make_http_error(
            400,
            reason="invalid",
            message="Invalid value for field 'region'",
        )

        assert get_gcp_subnets("test-project", "bad-region", mock_compute) is None

    def test_returns_none_for_invalid_region_during_pagination(self):
        mock_compute = MagicMock()
        request = _make_request(
            error=_make_http_error(
                400,
                reason="invalid",
                message="Invalid value for field 'region'",
            ),
        )
        mock_compute.subnetworks.return_value.list.return_value = request

        assert get_gcp_subnets("test-project", "bad-region", mock_compute) is None

    def test_preserves_partial_data_on_timeout(self):
        mock_compute = MagicMock()
        first_request = _make_request(
            response={"id": "subnet-page", "items": [{"name": "subnet-a"}]},
        )
        second_request = _make_request(error=TimeoutError())
        mock_compute.subnetworks.return_value.list.return_value = first_request
        mock_compute.subnetworks.return_value.list_next.side_effect = [
            second_request,
            None,
        ]

        assert get_gcp_subnets("test-project", "us-central1", mock_compute) == {
            "id": "subnet-page",
            "items": [{"name": "subnet-a"}],
        }

    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(403, reason="forbidden", message="Permission denied"),
            _make_http_error(503, reason="backendError", message="Backend error"),
            _make_http_error(418, message="Unexpected response"),
        ],
    )
    def test_reraises_non_invalid_http_errors(self, error):
        mock_compute = MagicMock()
        request = _make_request(error=error)
        mock_compute.subnetworks.return_value.list.return_value = request

        with patch("time.sleep", return_value=None):
            with pytest.raises(HttpError):
                get_gcp_subnets("test-project", "us-central1", mock_compute)


class TestGetGcpRegionalForwardingRulesHttpErrors:
    def test_returns_none_for_invalid_region(self):
        mock_compute = MagicMock()
        request = _make_request(
            error=_make_http_error(
                400,
                reason="invalid",
                message="Invalid value for field 'region'",
            ),
        )
        mock_compute.forwardingRules.return_value.list.return_value = request

        assert (
            get_gcp_regional_forwarding_rules(
                "test-project",
                "bad-region",
                mock_compute,
            )
            is None
        )

    @pytest.mark.parametrize(
        "error",
        [
            _make_http_error(403, reason="forbidden", message="Permission denied"),
            _make_http_error(503, reason="backendError", message="Backend error"),
            _make_http_error(418, message="Unexpected response"),
        ],
    )
    def test_reraises_non_invalid_categories(self, error):
        mock_compute = MagicMock()
        request = _make_request(error=error)
        mock_compute.forwardingRules.return_value.list.return_value = request

        with patch("time.sleep", return_value=None):
            with pytest.raises(HttpError):
                get_gcp_regional_forwarding_rules(
                    "test-project",
                    "us-central1",
                    mock_compute,
                )
