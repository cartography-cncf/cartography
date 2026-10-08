from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.router
from cartography.intel.gcp.util import aggregated_response_cleanup_safe
from tests.data.gcp.router import ROUTER_AGGREGATED_RESPONSE
from tests.data.gcp.router import ROUTER_PAGE_1_RESPONSE
from tests.data.gcp.router import ROUTER_PAGE_2_RESPONSE

TEST_PROJECT_ID = "project-abc"


def test_transform_gcp_routers_extracts_routers_and_cloud_nats():
    routers, cloud_nats = cartography.intel.gcp.router.transform_gcp_routers(
        ROUTER_AGGREGATED_RESPONSE,
        TEST_PROJECT_ID,
    )

    assert len(routers) == 2
    assert routers[0]["partial_uri"] == (
        f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-no-nats"
    )
    assert routers[0]["region"] == "us-central1"
    assert routers[0]["network_partial_uri"] == (
        f"projects/{TEST_PROJECT_ID}/global/networks/default"
    )

    assert len(cloud_nats) == 3
    assert cloud_nats[0]["id"] == (
        f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
        "router-with-nats/nats/nat-logging-on"
    )
    assert cloud_nats[0]["log_enabled"] is True
    assert cloud_nats[0]["log_filter"] == "ALL"
    assert cloud_nats[1]["log_enabled"] is False
    assert cloud_nats[1]["log_filter"] == "ERRORS_ONLY"
    assert cloud_nats[2]["log_enabled"] is None
    assert cloud_nats[2]["log_filter"] is None


def test_get_gcp_routers_merges_same_scope_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.routers.return_value.aggregatedList.return_value = request_1
    compute.routers.return_value.aggregatedList_next.side_effect = [
        request_2,
        None,
    ]

    with patch.object(
        cartography.intel.gcp.router,
        "gcp_api_execute_with_retry",
        side_effect=[ROUTER_PAGE_1_RESPONSE, ROUTER_PAGE_2_RESPONSE],
    ):
        response = cartography.intel.gcp.router.get_gcp_routers(
            TEST_PROJECT_ID,
            compute,
        )

    assert response is not None
    assert response["items"]["regions/us-central1"]["routers"] == [
        {"name": "router-page-1"},
        {"name": "router-page-2"},
    ]


def test_get_gcp_routers_preserves_unreachable_warning_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.routers.return_value.aggregatedList.return_value = request_1
    compute.routers.return_value.aggregatedList_next.side_effect = [
        request_2,
        None,
    ]

    page_1 = {
        "items": {
            "regions/us-central1": {
                "warning": {"code": "UNREACHABLE"},
            },
        },
    }
    page_2 = {
        "items": {
            "regions/us-central1": {
                "warning": {"code": "NO_RESULTS_ON_PAGE"},
            },
        },
    }

    with patch.object(
        cartography.intel.gcp.router,
        "gcp_api_execute_with_retry",
        side_effect=[page_1, page_2],
    ):
        response = cartography.intel.gcp.router.get_gcp_routers(
            TEST_PROJECT_ID,
            compute,
        )

    assert response is not None
    assert response["items"]["regions/us-central1"]["warning"] == {
        "code": "UNREACHABLE",
    }
    assert not aggregated_response_cleanup_safe(response)
