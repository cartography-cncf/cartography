from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_GATEWAYS_DATA = [
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
]

KUBERNETES_HTTP_ROUTES_DATA = [
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
            f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/app-service",
        ],
        "parent_gateway_qualified_names": [
            f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/public-gateway",
        ],
    },
]

KUBERNETES_GATEWAYS_RAW = [
    {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "Gateway",
        "metadata": {
            "name": "public-gateway",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            "uid": "gw-uid-001-abcd-1234",
            "creationTimestamp": "2021-10-07T06:21:06+00:00",
        },
        "spec": {
            "gatewayClassName": "nginx",
        },
    },
]

KUBERNETES_HTTP_ROUTES_RAW = [
    {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "HTTPRoute",
        "metadata": {
            "name": "frontend-route",
            "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            "uid": "hr-uid-001-abcd-1234",
            "creationTimestamp": "2021-10-07T06:21:40+00:00",
        },
        "spec": {
            "parentRefs": [
                {
                    "name": "public-gateway",
                },
            ],
            "hostnames": ["app.example.com"],
            "rules": [
                {
                    "backendRefs": [
                        {"name": "api-service"},
                        {"name": "app-service"},
                    ],
                },
            ],
        },
    },
]
