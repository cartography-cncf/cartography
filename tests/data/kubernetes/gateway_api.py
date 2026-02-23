from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_GATEWAYS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "public-gateway",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "gateway_class_name": "nginx",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "attached_route_names": ["frontend-route"],
        "attached_route_namespaces": [
            KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        ],
    },
]

KUBERNETES_HTTP_ROUTES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "frontend-route",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "hostnames": ["app.example.com"],
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "backend_service_names": ["api-service", "app-service"],
        "backend_service_namespaces": [
            KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        ],
        "parent_gateway_names": ["public-gateway"],
        "parent_gateway_namespaces": [
            KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
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
