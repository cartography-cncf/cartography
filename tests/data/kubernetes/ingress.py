import json
from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_INGRESS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-ingress",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps({"nginx.ingress.kubernetes.io/rewrite-target": "/"}),
        "ingress_class_name": "nginx",
        "rules": json.dumps([
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
        ]),
        "target_services": ["api-service", "app-service"],
    },
    {
        "uid": uuid4().hex,
        "name": "simple-ingress",
        "creation_timestamp": 1633581700,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "annotations": json.dumps({}),
        "ingress_class_name": "nginx",
        "rules": json.dumps([
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
        ]),
        "target_services": ["simple-service"],
    },
]
