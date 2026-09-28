from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.backendservice
import cartography.intel.gcp.compute
import cartography.intel.gcp.ssl_policy
import cartography.intel.gcp.target_https_proxy
import cartography.intel.gcp.target_ssl_proxy
from tests.data.gcp.compute_exposure import BACKEND_SERVICE_RESPONSE
from tests.data.gcp.ssl_policy_exposure import HTTPS_FORWARDING_RULE_RESPONSE
from tests.data.gcp.ssl_policy_exposure import REGIONAL_HTTPS_FORWARDING_RULE_RESPONSE
from tests.data.gcp.ssl_policy_exposure import SSL_POLICY_AGGREGATED_RESPONSE
from tests.data.gcp.ssl_policy_exposure import TARGET_HTTPS_PROXY_AGGREGATED_RESPONSE
from tests.data.gcp.ssl_policy_exposure import TARGET_SSL_PROXY_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "sample-project-123456"
TEST_REGION = "us-central1"


def _create_test_project(neo4j_session, project_id: str, update_tag: int) -> None:
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


@patch.object(
    cartography.intel.gcp.backendservice,
    "get_gcp_global_backend_services",
    return_value=BACKEND_SERVICE_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.ssl_policy,
    "get_gcp_ssl_policies",
    return_value=SSL_POLICY_AGGREGATED_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.target_https_proxy,
    "get_gcp_target_https_proxies",
    return_value=TARGET_HTTPS_PROXY_AGGREGATED_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.target_ssl_proxy,
    "get_gcp_target_ssl_proxies",
    return_value=TARGET_SSL_PROXY_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=HTTPS_FORWARDING_RULE_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=REGIONAL_HTTPS_FORWARDING_RULE_RESPONSE,
)
def test_sync_gcp_ssl_policy_and_target_proxies(
    mock_get_regional_forwarding_rules,
    mock_get_forwarding_rules,
    mock_get_target_ssl_proxies,
    mock_get_target_https_proxies,
    mock_get_ssl_policies,
    mock_get_backend_services,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act -- mirrors the dependency order wired into compute.py's sync().
    cartography.intel.gcp.backendservice.sync_gcp_backend_services(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        [],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.ssl_policy.sync_gcp_ssl_policies(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.target_https_proxy.sync_gcp_target_https_proxies(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.target_ssl_proxy.sync_gcp_target_ssl_proxies(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        [TEST_REGION],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert -- nodes
    assert check_nodes(
        neo4j_session,
        "GCPSslPolicy",
        ["id", "name", "profile", "min_tls_version", "region"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/sslPolicies/legacy-ssl-policy",
            "legacy-ssl-policy",
            "CUSTOM",
            "TLS_1_0",
            None,
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/sslPolicies/"
            "regional-modern-ssl-policy",
            "regional-modern-ssl-policy",
            "MODERN",
            "TLS_1_2",
            TEST_REGION,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPTargetHttpsProxy",
        ["id", "name", "region"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/targetHttpsProxies/test-https-proxy",
            "test-https-proxy",
            None,
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/targetHttpsProxies/"
            "regional-https-proxy",
            "regional-https-proxy",
            TEST_REGION,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPTargetSslProxy",
        ["id", "name"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/targetSslProxies/test-ssl-proxy",
            "test-ssl-proxy",
        ),
    }

    # Assert -- relationships
    assert check_rels(
        neo4j_session,
        "GCPTargetHttpsProxy",
        "id",
        "GCPSslPolicy",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/targetHttpsProxies/test-https-proxy",
            f"projects/{TEST_PROJECT_ID}/global/sslPolicies/legacy-ssl-policy",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/targetHttpsProxies/"
            "regional-https-proxy",
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/sslPolicies/"
            "regional-modern-ssl-policy",
        ),
    }

    # SSL proxy has no sslPolicy set -> no USES edge at all.
    assert (
        check_rels(
            neo4j_session,
            "GCPTargetSslProxy",
            "id",
            "GCPSslPolicy",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == set()
    )

    # SSL proxy still routes to its backend service.
    assert check_rels(
        neo4j_session,
        "GCPTargetSslProxy",
        "id",
        "GCPBackendService",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/targetSslProxies/test-ssl-proxy",
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
        ),
    }

    # Forwarding rules route traffic to their target HTTPS proxies.
    assert check_rels(
        neo4j_session,
        "GCPForwardingRule",
        "id",
        "GCPTargetHttpsProxy",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/forwardingRules/https-fr",
            f"projects/{TEST_PROJECT_ID}/global/targetHttpsProxies/test-https-proxy",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/forwardingRules/"
            "regional-https-fr",
            f"projects/{TEST_PROJECT_ID}/regions/{TEST_REGION}/targetHttpsProxies/"
            "regional-https-proxy",
        ),
    }
