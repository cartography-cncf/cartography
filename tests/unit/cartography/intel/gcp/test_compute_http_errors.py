import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.compute import get_gcp_instance_responses
from cartography.intel.gcp.compute import get_gcp_regional_forwarding_rules
from cartography.intel.gcp.compute import get_gcp_subnets
from cartography.intel.gcp.compute import get_zones_in_project
from cartography.intel.gcp.compute import sync
from cartography.intel.gcp.compute import sync_gcp_forwarding_rules


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
            _make_http_error(403, message="Forbidden"),
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


class TestSyncSkipsProjectOnComputeProjectsGetPermissionDenied:
    def test_sync_returns_without_raising_on_forbidden_project_get(self):
        """
        zones.list() succeeding but projects.get() returning a 403 with reason
        'forbidden' used to crash the entire org-wide sync (no try/except existed
        around get_gcp_compute_project_metadata at all). It should instead skip
        just this project's compute sync, the same way get_zones_in_project()
        already does for its own 403s.
        """
        mock_compute = MagicMock()

        zones_request = _make_request(
            response={"items": [{"name": "zone-a", "region": "region-a"}]},
        )
        mock_compute.zones.return_value.list.return_value = zones_request
        mock_compute.zones.return_value.list_next.return_value = None

        projects_get_request = _make_request(
            error=_make_http_error(
                403,
                reason="forbidden",
                message="Required 'compute.projects.get' permission",
            ),
        )
        mock_compute.projects.return_value.get.return_value = projects_get_request

        mock_neo4j_session = MagicMock()

        # Should return cleanly rather than propagate the HttpError.
        sync(mock_neo4j_session, mock_compute, "test-project", 123, {})

        # Confirm we actually stopped right after the permission-denied project
        # metadata call, instead of continuing on to sync VPCs/firewalls/etc.
        mock_compute.networks.assert_not_called()


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

    def test_sync_skips_cleanup_when_regional_listing_raises(self):
        mock_compute = MagicMock()

        with (
            patch(
                "cartography.intel.gcp.compute.get_gcp_global_forwarding_rules",
                return_value={"id": "projects/test-project/global/forwardingRules"},
            ),
            patch(
                "cartography.intel.gcp.compute.get_gcp_regional_forwarding_rules",
                side_effect=_make_http_error(
                    403,
                    reason="forbidden",
                    message="Permission denied",
                ),
            ),
            patch(
                "cartography.intel.gcp.compute.cleanup_gcp_forwarding_rules",
            ) as mock_cleanup,
        ):
            with pytest.raises(HttpError):
                sync_gcp_forwarding_rules(
                    MagicMock(),
                    mock_compute,
                    "test-project",
                    ["us-central1"],
                    123,
                    {"PROJECT_ID": "test-project", "UPDATE_TAG": 123},
                )

        mock_cleanup.assert_not_called()
