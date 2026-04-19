import json
from datetime import datetime
from uuid import uuid4

from kubernetes.client import V1HTTPIngressPath
from kubernetes.client import V1HTTPIngressRuleValue
from kubernetes.client import V1Ingress
from kubernetes.client import V1IngressBackend
from kubernetes.client import V1IngressLoadBalancerIngress
from kubernetes.client import V1IngressLoadBalancerStatus
from kubernetes.client import V1IngressRule
from kubernetes.client import V1IngressServiceBackend
from kubernetes.client import V1IngressSpec
from kubernetes.client import V1IngressStatus
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1ServiceBackendPort

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

# Shared ALB DNS name for ingress group testing
# This matches the ALB DNS name in tests/data/aws/ec2/load_balancer_v2s.py
SHARED_ALB_DNS_NAME = "test-alb-1234567890.us-east-1.elb.amazonaws.com"

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

# Raw V1Ingress data as returned by Kubernetes API (for sync_ingress tests)
KUBERNETES_INGRESS_RAW = [
    V1Ingress(
        metadata=V1ObjectMeta(
            name="my-ingress",
            namespace=KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            uid="ing-uid-001-abcd-1234",
            creation_timestamp=datetime.fromisoformat("2021-10-07T06:21:06+00:00"),
            deletion_timestamp=None,
            annotations={"nginx.ingress.kubernetes.io/rewrite-target": "/"},
        ),
        spec=V1IngressSpec(
            ingress_class_name="nginx",
            rules=[
                V1IngressRule(
                    host="example.com",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/api",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="api-service",
                                        port=V1ServiceBackendPort(
                                            name="http",
                                            number=80,
                                        ),
                                    ),
                                ),
                            ),
                            V1HTTPIngressPath(
                                path="/app",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="app-service",
                                        port=V1ServiceBackendPort(
                                            name="http",
                                            number=8080,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
                V1IngressRule(
                    host="api.example.com",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="api-service",
                                        port=V1ServiceBackendPort(
                                            name="http",
                                            number=80,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(ingress=None),
        ),
    ),
    V1Ingress(
        metadata=V1ObjectMeta(
            name="simple-ingress",
            namespace=KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            uid="ing-uid-002-efgh-5678",
            creation_timestamp=datetime.fromisoformat("2021-10-07T06:21:40+00:00"),
            deletion_timestamp=None,
            annotations={},
        ),
        spec=V1IngressSpec(
            ingress_class_name="nginx",
            rules=[
                V1IngressRule(
                    host="simple.example.com",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="simple-service",
                                        port=V1ServiceBackendPort(
                                            number=8080,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(ingress=None),
        ),
    ),
]

# Raw V1Ingress data for ALB ingresses with load balancer status
KUBERNETES_ALB_INGRESS_RAW = [
    V1Ingress(
        metadata=V1ObjectMeta(
            name="alb-ingress-api",
            namespace=KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            uid="alb-ing-uid-001-ijkl-9012",
            creation_timestamp=datetime.fromisoformat("2021-10-07T06:22:00+00:00"),
            deletion_timestamp=None,
            annotations={
                "alb.ingress.kubernetes.io/group.name": "shared-alb",
                "alb.ingress.kubernetes.io/scheme": "internet-facing",
                "alb.ingress.kubernetes.io/target-type": "ip",
            },
        ),
        spec=V1IngressSpec(
            ingress_class_name="alb",
            rules=[
                V1IngressRule(
                    host="api.myapp.example.com",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="api-service",
                                        port=V1ServiceBackendPort(
                                            number=80,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(
                ingress=[
                    V1IngressLoadBalancerIngress(
                        hostname=SHARED_ALB_DNS_NAME,
                    ),
                ],
            ),
        ),
    ),
    V1Ingress(
        metadata=V1ObjectMeta(
            name="alb-ingress-web",
            namespace=KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
            uid="alb-ing-uid-002-mnop-3456",
            creation_timestamp=datetime.fromisoformat("2021-10-07T06:22:30+00:00"),
            deletion_timestamp=None,
            annotations={
                "alb.ingress.kubernetes.io/group.name": "shared-alb",
                "alb.ingress.kubernetes.io/scheme": "internet-facing",
                "alb.ingress.kubernetes.io/target-type": "ip",
            },
        ),
        spec=V1IngressSpec(
            ingress_class_name="alb",
            rules=[
                V1IngressRule(
                    host="www.myapp.example.com",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=V1IngressBackend(
                                    service=V1IngressServiceBackend(
                                        name="web-service",
                                        port=V1ServiceBackendPort(
                                            number=8080,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(
                ingress=[
                    V1IngressLoadBalancerIngress(
                        hostname=SHARED_ALB_DNS_NAME,
                    ),
                ],
            ),
        ),
    ),
]
