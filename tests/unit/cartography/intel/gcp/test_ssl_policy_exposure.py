import json
from unittest.mock import MagicMock
from unittest.mock import patch

from googleapiclient.errors import HttpError

import cartography.intel.gcp.ssl_policy
import cartography.intel.gcp.target_https_proxy
import cartography.intel.gcp.target_ssl_proxy
from tests.data.gcp.ssl_policy_exposure import REGIONAL_SSL_POLICY_RESPONSE
from tests.data.gcp.ssl_policy_exposure import REGIONAL_TARGET_HTTPS_PROXY_RESPONSE
from tests.data.gcp.ssl_policy_exposure import SSL_POLICY_RESPONSE
from tests.data.gcp.ssl_policy_exposure import TARGET_HTTPS_PROXY_RESPONSE
from tests.data.gcp.ssl_policy_exposure import TARGET_SSL_PROXY_RESPONSE

TEST_PROJECT_ID = "sample-project-123456"


def _make_http_error(reason: str) -> HttpError:
    resp = MagicMock()
    resp.status = 403
    return HttpError(
        resp=resp,
        content=json.dumps(
            {
                "error": {
                    "message": "Permission denied",
                    "errors": [{"reason": reason}],
                },
            }
        ).encode("utf-8"),
    )


def test_transform_gcp_ssl_policies():
    policies = cartography.intel.gcp.ssl_policy.transform_gcp_ssl_policies(
        SSL_POLICY_RESPONSE, TEST_PROJECT_ID
    )
    assert len(policies) == 1

    policy = policies[0]
    assert (
        policy["partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/sslPolicies/legacy-ssl-policy"
    )
    assert policy["project_id"] == TEST_PROJECT_ID
    assert policy["profile"] == "CUSTOM"
    assert policy["min_tls_version"] == "TLS_1_0"
    assert policy["enabled_features"] == ["TLS_RSA_WITH_3DES_EDE_CBC_SHA"]
    assert policy["custom_features"] == ["TLS_RSA_WITH_3DES_EDE_CBC_SHA"]


def test_transform_gcp_ssl_policies_sets_region_for_regional_policies():
    policies = cartography.intel.gcp.ssl_policy.transform_gcp_ssl_policies(
        REGIONAL_SSL_POLICY_RESPONSE, TEST_PROJECT_ID
    )
    assert len(policies) == 1

    policy = policies[0]
    assert (
        policy["partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/regions/us-central1/sslPolicies/"
        "regional-modern-ssl-policy"
    )
    assert policy["region"] == "us-central1"
    assert policy["profile"] == "MODERN"


def test_transform_gcp_target_https_proxies_parses_ssl_policy_to_partial_uri():
    proxies = (
        cartography.intel.gcp.target_https_proxy.transform_gcp_target_https_proxies(
            TARGET_HTTPS_PROXY_RESPONSE, TEST_PROJECT_ID
        )
    )
    assert len(proxies) == 1

    proxy = proxies[0]
    assert (
        proxy["partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/targetHttpsProxies/test-https-proxy"
    )
    assert (
        proxy["ssl_policy_partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/sslPolicies/legacy-ssl-policy"
    )
    assert (
        proxy["url_map_partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/urlMaps/test-url-map"
    )


def test_transform_gcp_target_https_proxies_sets_region_for_regional_proxies():
    proxies = (
        cartography.intel.gcp.target_https_proxy.transform_gcp_target_https_proxies(
            REGIONAL_TARGET_HTTPS_PROXY_RESPONSE, TEST_PROJECT_ID
        )
    )
    assert len(proxies) == 1

    proxy = proxies[0]
    assert (
        proxy["partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/regions/us-central1/targetHttpsProxies/"
        "regional-https-proxy"
    )
    assert proxy["region"] == "us-central1"
    assert (
        proxy["ssl_policy_partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/regions/us-central1/sslPolicies/"
        "regional-modern-ssl-policy"
    )


def test_get_gcp_ssl_policies_merges_same_scope_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.sslPolicies.return_value.aggregatedList.return_value = request_1
    compute.sslPolicies.return_value.aggregatedList_next.side_effect = [
        request_2,
        None,
    ]

    page_1 = {
        "id": "projects/sample-project-123456/aggregated/sslPolicies",
        "items": {
            "global": {
                "sslPolicies": [
                    {
                        "name": "policy-page-1",
                    },
                ],
            },
        },
    }
    page_2 = {
        "id": "projects/sample-project-123456/aggregated/sslPolicies",
        "items": {
            "global": {
                "sslPolicies": [
                    {
                        "name": "policy-page-2",
                    },
                ],
            },
        },
    }

    with patch.object(
        cartography.intel.gcp.ssl_policy,
        "gcp_api_execute_with_retry",
        side_effect=[page_1, page_2],
    ):
        response = cartography.intel.gcp.ssl_policy.get_gcp_ssl_policies(
            TEST_PROJECT_ID,
            compute,
        )

    assert response is not None
    assert response["items"]["global"]["sslPolicies"] == [
        {"name": "policy-page-1"},
        {"name": "policy-page-2"},
    ]


def test_get_gcp_target_https_proxies_merges_same_scope_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.targetHttpsProxies.return_value.aggregatedList.return_value = request_1
    compute.targetHttpsProxies.return_value.aggregatedList_next.side_effect = [
        request_2,
        None,
    ]

    page_1 = {
        "id": "projects/sample-project-123456/aggregated/targetHttpsProxies",
        "items": {
            "global": {
                "targetHttpsProxies": [
                    {
                        "name": "proxy-page-1",
                    },
                ],
            },
        },
    }
    page_2 = {
        "id": "projects/sample-project-123456/aggregated/targetHttpsProxies",
        "items": {
            "global": {
                "targetHttpsProxies": [
                    {
                        "name": "proxy-page-2",
                    },
                ],
            },
        },
    }

    with patch.object(
        cartography.intel.gcp.target_https_proxy,
        "gcp_api_execute_with_retry",
        side_effect=[page_1, page_2],
    ):
        response = (
            cartography.intel.gcp.target_https_proxy.get_gcp_target_https_proxies(
                TEST_PROJECT_ID,
                compute,
            )
        )

    assert response is not None
    assert response["items"]["global"]["targetHttpsProxies"] == [
        {"name": "proxy-page-1"},
        {"name": "proxy-page-2"},
    ]


def test_get_gcp_ssl_policies_preserves_unreachable_warning_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.sslPolicies.return_value.aggregatedList.return_value = request_1
    compute.sslPolicies.return_value.aggregatedList_next.side_effect = [
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
        cartography.intel.gcp.ssl_policy,
        "gcp_api_execute_with_retry",
        side_effect=[page_1, page_2],
    ):
        response = cartography.intel.gcp.ssl_policy.get_gcp_ssl_policies(
            TEST_PROJECT_ID,
            compute,
        )

    assert response is not None
    assert response["items"]["regions/us-central1"]["warning"] == {
        "code": "UNREACHABLE",
    }
    assert not cartography.intel.gcp.ssl_policy.aggregated_response_cleanup_safe(
        response,
    )


def test_get_gcp_target_https_proxies_preserves_unreachable_warning_across_pages():
    compute = MagicMock()
    request_1 = MagicMock()
    request_2 = MagicMock()
    compute.targetHttpsProxies.return_value.aggregatedList.return_value = request_1
    compute.targetHttpsProxies.return_value.aggregatedList_next.side_effect = [
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
        cartography.intel.gcp.target_https_proxy,
        "gcp_api_execute_with_retry",
        side_effect=[page_1, page_2],
    ):
        response = (
            cartography.intel.gcp.target_https_proxy.get_gcp_target_https_proxies(
                TEST_PROJECT_ID,
                compute,
            )
        )

    assert response is not None
    assert response["items"]["regions/us-central1"]["warning"] == {
        "code": "UNREACHABLE",
    }
    assert (
        not cartography.intel.gcp.target_https_proxy.aggregated_response_cleanup_safe(
            response,
        )
    )


def test_sync_gcp_ssl_policies_skips_cleanup_when_global_list_denied():
    compute = MagicMock()

    with (
        patch.object(
            cartography.intel.gcp.ssl_policy,
            "gcp_api_execute_with_retry",
            side_effect=_make_http_error("vpcServiceControls"),
        ),
        patch.object(
            cartography.intel.gcp.ssl_policy,
            "cleanup_gcp_ssl_policies",
        ) as mock_cleanup,
    ):
        cartography.intel.gcp.ssl_policy.sync_gcp_ssl_policies(
            MagicMock(),
            compute,
            TEST_PROJECT_ID,
            123,
            {"PROJECT_ID": TEST_PROJECT_ID, "UPDATE_TAG": 123},
        )

    mock_cleanup.assert_not_called()


def test_sync_gcp_target_https_proxies_skips_cleanup_when_global_list_denied():
    compute = MagicMock()

    with (
        patch.object(
            cartography.intel.gcp.target_https_proxy,
            "gcp_api_execute_with_retry",
            side_effect=_make_http_error("forbidden"),
        ),
        patch.object(
            cartography.intel.gcp.target_https_proxy,
            "cleanup_gcp_target_https_proxies",
        ) as mock_cleanup,
    ):
        cartography.intel.gcp.target_https_proxy.sync_gcp_target_https_proxies(
            MagicMock(),
            compute,
            TEST_PROJECT_ID,
            123,
            {"PROJECT_ID": TEST_PROJECT_ID, "UPDATE_TAG": 123},
        )

    mock_cleanup.assert_not_called()


def test_sync_gcp_target_ssl_proxies_skips_cleanup_when_list_denied():
    compute = MagicMock()

    with (
        patch.object(
            cartography.intel.gcp.target_ssl_proxy,
            "gcp_api_execute_with_retry",
            side_effect=_make_http_error("forbidden"),
        ),
        patch.object(
            cartography.intel.gcp.target_ssl_proxy,
            "cleanup_gcp_target_ssl_proxies",
        ) as mock_cleanup,
    ):
        cartography.intel.gcp.target_ssl_proxy.sync_gcp_target_ssl_proxies(
            MagicMock(),
            compute,
            TEST_PROJECT_ID,
            123,
            {"PROJECT_ID": TEST_PROJECT_ID, "UPDATE_TAG": 123},
        )

    mock_cleanup.assert_not_called()


def test_transform_gcp_target_ssl_proxies_handles_missing_ssl_policy():
    """
    A target proxy with no `sslPolicy` field has no SSL policy configured.
    ssl_policy_partial_uri should come back None, not raise, so the USES
    relationship simply doesn't get created for that proxy.
    """
    proxies = cartography.intel.gcp.target_ssl_proxy.transform_gcp_target_ssl_proxies(
        TARGET_SSL_PROXY_RESPONSE, TEST_PROJECT_ID
    )
    assert len(proxies) == 1

    proxy = proxies[0]
    assert (
        proxy["partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/targetSslProxies/test-ssl-proxy"
    )
    assert proxy["ssl_policy_partial_uri"] is None
    assert (
        proxy["service_partial_uri"]
        == f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service"
    )
