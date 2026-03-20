import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.compute import get_gcp_instance_responses
from cartography.intel.gcp.compute import get_gcp_regional_forwarding_rules
from cartography.intel.gcp.compute import get_gcp_subnets
from cartography.intel.gcp.compute import get_zones_in_project


def _make_http_error(status: int) -> HttpError:
    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps({"error": {"code": status}}).encode())


class TestGetZonesInProjectHttpErrors:
    @pytest.mark.parametrize("category", ["api_disabled", "forbidden", "not_found"])
    def test_returns_none_for_expected_skip_categories(self, category):
        mock_compute = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            assert get_zones_in_project("test-project", mock_compute) is None

    @pytest.mark.parametrize("category", ["transient", "invalid", "unknown"])
    def test_reraises_unexpected_categories(self, category):
        mock_compute = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(500),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            with pytest.raises(HttpError):
                get_zones_in_project("test-project", mock_compute)


class TestGetGcpInstanceResponsesHttpErrors:
    def test_skips_zone_for_transient_errors(self):
        mock_compute = MagicMock()
        zones = [{"name": "zone-a"}, {"name": "zone-b"}]
        success_response = {"id": "projects/test-project/zones/zone-b/instances"}
        mock_compute.instances().list.side_effect = [MagicMock(), MagicMock()]

        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=[_make_http_error(503), success_response],
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value="transient",
            ),
        ):
            assert get_gcp_instance_responses("test-project", zones, mock_compute) == [
                success_response
            ]

    @pytest.mark.parametrize("category", ["forbidden", "invalid", "unknown"])
    def test_reraises_non_transient_errors(self, category):
        mock_compute = MagicMock()
        zones = [{"name": "zone-a"}]
        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            with pytest.raises(HttpError):
                get_gcp_instance_responses("test-project", zones, mock_compute)


class TestGetGcpSubnetsHttpErrors:
    def test_returns_none_for_invalid_region_during_request_creation(self):
        mock_compute = MagicMock()
        mock_compute.subnetworks().list.side_effect = _make_http_error(400)

        with patch(
            "cartography.intel.gcp.compute.classify_gcp_http_error",
            return_value="invalid",
        ):
            assert get_gcp_subnets("test-project", "bad-region", mock_compute) is None

    def test_returns_none_for_invalid_region_during_pagination(self):
        mock_compute = MagicMock()
        request = MagicMock()
        mock_compute.subnetworks().list.return_value = request

        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(400),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value="invalid",
            ),
        ):
            assert get_gcp_subnets("test-project", "bad-region", mock_compute) is None

    def test_preserves_partial_data_on_timeout(self):
        mock_compute = MagicMock()
        request = MagicMock()
        next_request = MagicMock()
        mock_compute.subnetworks().list.return_value = request
        mock_compute.subnetworks().list_next.side_effect = [next_request, None]

        first_page = {"id": "subnet-page", "items": [{"name": "subnet-a"}]}
        with patch(
            "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
            side_effect=[first_page, TimeoutError()],
        ):
            assert get_gcp_subnets("test-project", "us-central1", mock_compute) == {
                "id": "subnet-page",
                "items": [{"name": "subnet-a"}],
            }

    @pytest.mark.parametrize("category", ["forbidden", "transient", "unknown"])
    def test_reraises_non_invalid_http_errors(self, category):
        mock_compute = MagicMock()
        request = MagicMock()
        mock_compute.subnetworks().list.return_value = request

        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            with pytest.raises(HttpError):
                get_gcp_subnets("test-project", "us-central1", mock_compute)


class TestGetGcpRegionalForwardingRulesHttpErrors:
    def test_returns_none_for_invalid_region(self):
        mock_compute = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(400),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value="invalid",
            ),
        ):
            assert (
                get_gcp_regional_forwarding_rules(
                    "test-project",
                    "bad-region",
                    mock_compute,
                )
                is None
            )

    @pytest.mark.parametrize("category", ["forbidden", "transient", "unknown"])
    def test_reraises_non_invalid_categories(self, category):
        mock_compute = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.compute.gcp_api_execute_with_retry",
                side_effect=_make_http_error(500),
            ),
            patch(
                "cartography.intel.gcp.compute.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            with pytest.raises(HttpError):
                get_gcp_regional_forwarding_rules(
                    "test-project",
                    "us-central1",
                    mock_compute,
                )
