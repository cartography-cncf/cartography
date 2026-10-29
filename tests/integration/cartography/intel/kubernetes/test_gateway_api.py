from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest
from kubernetes.client.exceptions import ApiException

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


def test_gateway_api_relationships_preserve_namespace_name_pairs(neo4j_session):
    _create_test_cluster(neo4j_session)

    cross_namespace_services = deepcopy(KUBERNETES_SERVICES_DATA) + [
        {
            "uid": uuid4().hex,
            "name": "api-service",
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]['name']}/api-service",
            "creation_timestamp": 1633581700,
            "deletion_timestamp": None,
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]["name"],
            "type": "ClusterIP",
            "selector": "{}",
            "cluster_ip": "10.0.2.1",
            "pod_ids": [],
            "load_balancer_ip": None,
        },
        {
            "uid": uuid4().hex,
            "name": "simple-service",
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]['name']}/simple-service",
            "creation_timestamp": 1633581710,
            "deletion_timestamp": None,
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]["name"],
            "type": "ClusterIP",
            "selector": "{}",
            "cluster_ip": "10.0.2.2",
            "pod_ids": [],
            "load_balancer_ip": None,
        },
    ]
    cross_namespace_routes = [
        {
            "uid": uuid4().hex,
            "name": "frontend-route",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
            "hostnames": ["app.example.com"],
            "creation_timestamp": 1633587700,
            "deletion_timestamp": None,
            "backend_service_qualified_names": [
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-service",
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]['name']}/simple-service",
            ],
            "parent_gateway_qualified_names": [
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/public-gateway",
            ],
        },
    ]
    cross_namespace_gateways = [
        {
            "uid": uuid4().hex,
            "name": "public-gateway",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/public-gateway",
            "gateway_class_name": "nginx",
            "creation_timestamp": 1633587666,
            "deletion_timestamp": None,
            "attached_route_qualified_names": [
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
            ],
        },
        {
            "uid": uuid4().hex,
            "name": "public-gateway",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]["name"],
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]['name']}/public-gateway",
            "gateway_class_name": "nginx",
            "creation_timestamp": 1633587726,
            "deletion_timestamp": None,
            "attached_route_qualified_names": [],
        },
    ]

    try:
        load_services(
            neo4j_session,
            cross_namespace_services,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_http_routes(
            neo4j_session,
            cross_namespace_routes,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_gateways(
            neo4j_session,
            cross_namespace_gateways,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_rels(
            neo4j_session,
            "KubernetesHTTPRoute",
            "qualified_name",
            "KubernetesService",
            "qualified_name",
            "TARGETS",
            rel_direction_right=True,
        ) == {
            (
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-service",
            ),
            (
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[0]['name']}/simple-service",
            ),
        }

        assert check_rels(
            neo4j_session,
            "KubernetesGateway",
            "qualified_name",
            "KubernetesHTTPRoute",
            "qualified_name",
            "ROUTES",
            rel_direction_right=True,
        ) == {
            (
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/public-gateway",
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
            ),
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
        namespace = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]
        false_match_service = {
            "uid": uuid4().hex,
            "name": "not-a-service",
            "qualified_name": f"{namespace}/not-a-service",
            "creation_timestamp": 1633581720,
            "deletion_timestamp": None,
            "namespace": namespace,
            "type": "ClusterIP",
            "selector": "{}",
            "cluster_ip": "10.0.2.3",
            "pod_ids": [],
            "load_balancer_ip": None,
        }
        load_services(
            neo4j_session,
            [false_match_service],
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        gateways_raw = deepcopy(KUBERNETES_GATEWAYS_RAW) + [
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "Gateway",
                "metadata": {
                    "name": "not-a-gateway-parent",
                    "namespace": namespace,
                    "uid": "gw-uid-002-abcd-1234",
                    "creationTimestamp": "2021-10-07T06:22:06+00:00",
                },
                "spec": {"gatewayClassName": "nginx"},
            },
        ]
        routes_raw = deepcopy(KUBERNETES_HTTP_ROUTES_RAW)
        routes_raw[0]["spec"]["parentRefs"].append(
            {
                "group": "",
                "kind": "Service",
                "name": "not-a-gateway-parent",
            },
        )
        routes_raw[0]["spec"]["rules"][0]["backendRefs"].append(
            {
                "group": "example.com",
                "kind": "ExternalBackend",
                "name": "not-a-service",
            },
        )

        mock_get_gateways.return_value = gateways_raw
        mock_get_http_routes.return_value = routes_raw

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
def test_sync_gateway_api_cleans_up_stale_nodes_and_rels(
    mock_get_http_routes,
    mock_get_gateways,
    neo4j_session,
):
    """A second sync where a Gateway and an HTTPRoute have disappeared from the
    cluster should remove the stale nodes and their ROUTES/TARGETS rels."""
    _create_test_cluster(neo4j_session)

    try:
        namespace = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        }
        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        first_gateways = deepcopy(KUBERNETES_GATEWAYS_RAW) + [
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "Gateway",
                "metadata": {
                    "name": "stale-gateway",
                    "namespace": namespace,
                    "uid": "gw-uid-stale-1",
                    "creationTimestamp": "2021-10-07T06:21:06Z",
                },
                "spec": {"gatewayClassName": "nginx"},
            },
        ]
        first_routes = deepcopy(KUBERNETES_HTTP_ROUTES_RAW) + [
            {
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "HTTPRoute",
                "metadata": {
                    "name": "stale-route",
                    "namespace": namespace,
                    "uid": "hr-uid-stale-1",
                    "creationTimestamp": "2021-10-07T06:21:40Z",
                },
                "spec": {
                    "parentRefs": [{"name": "stale-gateway"}],
                    "rules": [{"backendRefs": [{"name": "api-service"}]}],
                },
            },
        ]
        mock_get_gateways.return_value = first_gateways
        mock_get_http_routes.return_value = first_routes

        sync_gateway_api(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG,
            common_job_parameters=common_job_parameters,
        )

        assert check_nodes(neo4j_session, "KubernetesGateway", ["name"]) == {
            ("public-gateway",),
            ("stale-gateway",),
        }
        assert check_nodes(neo4j_session, "KubernetesHTTPRoute", ["name"]) == {
            ("frontend-route",),
            ("stale-route",),
        }

        next_update_tag = TEST_UPDATE_TAG + 1
        common_job_parameters["UPDATE_TAG"] = next_update_tag
        mock_get_gateways.return_value = deepcopy(KUBERNETES_GATEWAYS_RAW)
        mock_get_http_routes.return_value = deepcopy(KUBERNETES_HTTP_ROUTES_RAW)

        sync_gateway_api(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=next_update_tag,
            common_job_parameters=common_job_parameters,
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


@pytest.mark.parametrize("status", [401, 403])
@patch.object(cartography.intel.kubernetes.gateway_api, "get_gateways")
@patch.object(cartography.intel.kubernetes.gateway_api, "get_http_routes")
def test_sync_gateway_api_preserves_existing_data_on_permission_error(
    mock_get_http_routes,
    mock_get_gateways,
    status,
    neo4j_session,
):
    """If RBAC for gateway-api is revoked between syncs, the next sync must
    preserve the previously ingested KubernetesGateway / KubernetesHTTPRoute
    nodes (rather than wiping them via the cleanup step)."""
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

        mock_get_gateways.side_effect = ApiException(status=status)
        mock_get_http_routes.side_effect = ApiException(status=status)

        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        sync_gateway_api(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG + 1,
            common_job_parameters={
                "UPDATE_TAG": TEST_UPDATE_TAG + 1,
                "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
            },
        )

        assert check_nodes(neo4j_session, "KubernetesGateway", ["name"]) == {
            ("public-gateway",),
        }
        assert check_nodes(neo4j_session, "KubernetesHTTPRoute", ["name"]) == {
            ("frontend-route",),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)
