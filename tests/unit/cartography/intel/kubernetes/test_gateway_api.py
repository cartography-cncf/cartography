from unittest.mock import MagicMock

import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.gateway_api import _list_cluster_custom_objects
from cartography.intel.kubernetes.gateway_api import transform_gateways
from cartography.intel.kubernetes.gateway_api import transform_http_routes
from tests.data.kubernetes.gateway_api import KUBERNETES_HTTP_ROUTES_RAW
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA


def test_list_cluster_custom_objects_returns_empty_on_missing_crd():
    client = MagicMock()
    client.name = "test-cluster"
    client.custom.list_cluster_custom_object.side_effect = ApiException(status=404)

    resources = _list_cluster_custom_objects(
        client,
        group="gateway.networking.k8s.io",
        version="v1",
        plural="gateways",
    )

    assert resources == []


@pytest.mark.parametrize("status", [401, 403])
def test_list_cluster_custom_objects_skips_on_permission_error(status, caplog):
    client = MagicMock()
    client.name = "test-cluster"
    client.custom.list_cluster_custom_object.side_effect = ApiException(status=status)

    with caplog.at_level("WARNING", logger="cartography.intel.kubernetes.gateway_api"):
        resources = _list_cluster_custom_objects(
            client,
            group="gateway.networking.k8s.io",
            version="v1",
            plural="httproutes",
        )

    assert resources == []
    assert any("httproutes" in record.message for record in caplog.records)


def test_list_cluster_custom_objects_raises_on_unexpected_error():
    client = MagicMock()
    client.name = "test-cluster"
    client.custom.list_cluster_custom_object.side_effect = ApiException(status=500)

    with pytest.raises(ApiException):
        _list_cluster_custom_objects(
            client,
            group="gateway.networking.k8s.io",
            version="v1",
            plural="gateways",
        )


def test_transform_gateways_requires_required_metadata_fields():
    gateways = [
        {"metadata": {"uid": "gateway-uid", "namespace": "default"}, "spec": {}}
    ]

    with pytest.raises(KeyError):
        transform_gateways(gateways)


def test_transform_http_routes_uses_qualified_names_and_normalizes_timestamps():
    routes = transform_http_routes(KUBERNETES_HTTP_ROUTES_RAW)

    assert routes == [
        {
            "uid": "hr-uid-001-abcd-1234",
            "name": "frontend-route",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            "qualified_name": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/frontend-route",
            "hostnames": ["app.example.com"],
            "creation_timestamp": 1633587700,
            "deletion_timestamp": None,
            "backend_service_qualified_names": [
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-service",
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/app-service",
            ],
            "parent_gateway_qualified_names": [
                f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/public-gateway",
            ],
        },
    ]


def test_transform_gateways_normalizes_rfc3339_timestamps_to_epoch():
    raw = [
        {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "Gateway",
            "metadata": {
                "name": "gw",
                "namespace": "ns",
                "uid": "uid-1",
                "creationTimestamp": "2021-10-07T06:21:06Z",
                "deletionTimestamp": "2021-10-07T06:21:40+00:00",
            },
            "spec": {"gatewayClassName": "nginx"},
        }
    ]

    [transformed] = transform_gateways(raw)

    assert transformed["creation_timestamp"] == 1633587666
    assert transformed["deletion_timestamp"] == 1633587700
