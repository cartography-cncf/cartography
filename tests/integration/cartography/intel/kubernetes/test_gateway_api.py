from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.kubernetes.gateway_api
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.gateway_api import load_gateways
from cartography.intel.kubernetes.gateway_api import load_http_routes
from cartography.intel.kubernetes.gateway_api import sync_gateway_api
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.gateway_api import KUBERNETES_GATEWAYS_DATA
from tests.data.kubernetes.gateway_api import KUBERNETES_GATEWAYS_RAW
from tests.data.kubernetes.gateway_api import KUBERNETES_HTTP_ROUTES_DATA
from tests.data.kubernetes.gateway_api import KUBERNETES_HTTP_ROUTES_RAW
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.services import KUBERNETES_SERVICES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_test_cluster(neo4j_session):
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_2_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[1],
        cluster_name=KUBERNETES_CLUSTER_NAMES[1],
    )
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )


def _cleanup_test_cluster(neo4j_session):
    for label in [
        "KubernetesGateway",
        "KubernetesHTTPRoute",
        "KubernetesService",
        "KubernetesNamespace",
        "KubernetesCluster",
    ]:
        neo4j_session.run(f"MATCH (n:{label}) DETACH DELETE n")


def test_gateway_api_relationships(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_http_routes(
            neo4j_session,
            KUBERNETES_HTTP_ROUTES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_gateways(
            neo4j_session,
            KUBERNETES_GATEWAYS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_nodes(neo4j_session, "KubernetesGateway", ["name"]) == {
            ("public-gateway",),
        }
        assert check_nodes(neo4j_session, "KubernetesHTTPRoute", ["name"]) == {
            ("frontend-route",),
        }

        assert check_rels(
            neo4j_session,
            "KubernetesGateway",
            "name",
            "KubernetesHTTPRoute",
            "name",
            "ROUTES",
            rel_direction_right=True,
        ) == {("public-gateway", "frontend-route")}

        assert check_rels(
            neo4j_session,
            "KubernetesHTTPRoute",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
            rel_direction_right=True,
        ) == {
            ("frontend-route", "api-service"),
            ("frontend-route", "app-service"),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)


@patch.object(cartography.intel.kubernetes.gateway_api, "get_gateways")
@patch.object(cartography.intel.kubernetes.gateway_api, "get_http_routes")
def test_sync_gateway_api_end_to_end(
    mock_get_http_routes,
    mock_get_gateways,
    neo4j_session,
):
    _create_test_cluster(neo4j_session)

    try:
        mock_get_gateways.return_value = KUBERNETES_GATEWAYS_RAW
        mock_get_http_routes.return_value = KUBERNETES_HTTP_ROUTES_RAW

        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        }

        sync_gateway_api(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG,
            common_job_parameters=common_job_parameters,
        )

        mock_get_gateways.assert_called_once_with(k8s_client)
        mock_get_http_routes.assert_called_once_with(k8s_client)

        assert check_rels(
            neo4j_session,
            "KubernetesGateway",
            "name",
            "KubernetesHTTPRoute",
            "name",
            "ROUTES",
            rel_direction_right=True,
        ) == {("public-gateway", "frontend-route")}
    finally:
        _cleanup_test_cluster(neo4j_session)
