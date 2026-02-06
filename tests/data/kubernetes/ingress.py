import json
from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

# Shared ALB DNS name for ingress group testing
SHARED_ALB_DNS_NAME = "k8s-shared-alb-abc123-1234567890.us-west-2.elb.amazonaws.com"

KUBERNETES_INGRESS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-ingress",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps({"nginx.ingress.kubernetes.io/rewrite-target": "/"}),
        "ingress_class_name": "nginx",
        "rules": json.dumps(
            [
                {
                    "host": "example.com",
                    "paths": [
                        {
                            "path": "/api",
                            "path_type": "Prefix",
                            "backend_service_name": "api-service",
                            "backend_service_port_name": "http",
                            "backend_service_port_number": 80,
                        },
                        {
                            "path": "/app",
                            "path_type": "Prefix",
                            "backend_service_name": "app-service",
                            "backend_service_port_name": "http",
                            "backend_service_port_number": 8080,
                        },
                    ],
                },
                {
                    "host": "api.example.com",
                    "paths": [
                        {
                            "path": "/",
                            "path_type": "Prefix",
                            "backend_service_name": "api-service",
                            "backend_service_port_name": "http",
                            "backend_service_port_number": 80,
                        },
                    ],
                },
            ]
        ),
        "target_services": ["api-service", "app-service"],
        "ingress_group_name": None,
        "load_balancer_dns_names": [],
    },
    {
        "uid": uuid4().hex,
        "name": "simple-ingress",
        "creation_timestamp": 1633581700,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps({}),
        "ingress_class_name": "nginx",
        "rules": json.dumps(
            [
                {
                    "host": "simple.example.com",
                    "paths": [
                        {
                            "path": "/",
                            "path_type": "Prefix",
                            "backend_service_name": "simple-service",
                            "backend_service_port_number": 8080,
                        },
                    ],
                },
            ]
        ),
        "target_services": ["simple-service"],
        "ingress_group_name": None,
        "load_balancer_dns_names": [],
    },
]

# Test data for AWS ALB Ingress Controller with ingress groups
# These ingresses share the same ALB via the group.name annotation
KUBERNETES_ALB_INGRESS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "alb-ingress-api",
        "creation_timestamp": 1633581800,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps(
            {
                "alb.ingress.kubernetes.io/group.name": "shared-alb",
                "alb.ingress.kubernetes.io/scheme": "internet-facing",
                "alb.ingress.kubernetes.io/target-type": "ip",
            }
        ),
        "ingress_class_name": "alb",
        "rules": json.dumps(
            [
                {
                    "host": "api.myapp.example.com",
                    "paths": [
                        {
                            "path": "/",
                            "path_type": "Prefix",
                            "backend_service_name": "api-service",
                            "backend_service_port_number": 80,
                        },
                    ],
                },
            ]
        ),
        "default_backend": json.dumps({}),
        "target_services": ["api-service"],
        "ingress_group_name": "shared-alb",
        "load_balancer_dns_names": [SHARED_ALB_DNS_NAME],
    },
    {
        "uid": uuid4().hex,
        "name": "alb-ingress-web",
        "creation_timestamp": 1633581900,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps(
            {
                "alb.ingress.kubernetes.io/group.name": "shared-alb",
                "alb.ingress.kubernetes.io/scheme": "internet-facing",
                "alb.ingress.kubernetes.io/target-type": "ip",
            }
        ),
        "ingress_class_name": "alb",
        "rules": json.dumps(
            [
                {
                    "host": "www.myapp.example.com",
                    "paths": [
                        {
                            "path": "/",
                            "path_type": "Prefix",
                            "backend_service_name": "web-service",
                            "backend_service_port_number": 8080,
                        },
                    ],
                },
            ]
        ),
        "default_backend": json.dumps({}),
        "target_services": ["web-service"],
        "ingress_group_name": "shared-alb",
        "load_balancer_dns_names": [SHARED_ALB_DNS_NAME],
    },
]
