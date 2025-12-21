import json
from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA

KUBERNETES_SERVICES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-service",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": 1633581966,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "ClusterIP",
        "selector": json.dumps({"app": "my-app"}),
        "cluster_ip": "1.1.1.1",
        "pod_ids": [
            KUBERNETES_PODS_DATA[0]["uid"],
        ],
        "load_balancer_ip": "1.1.1.1",
    },
    {
        "uid": uuid4().hex,
        "name": "api-service",
        "creation_timestamp": 1633581600,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "ClusterIP",
        "selector": json.dumps({"app": "api"}),
        "cluster_ip": "10.0.1.1",
        "pod_ids": [],
        "load_balancer_ip": None,
    },
    {
        "uid": uuid4().hex,
        "name": "app-service",
        "creation_timestamp": 1633581610,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "ClusterIP",
        "selector": json.dumps({"app": "app"}),
        "cluster_ip": "10.0.1.2",
        "pod_ids": [],
        "load_balancer_ip": None,
    },
    {
        "uid": uuid4().hex,
        "name": "simple-service",
        "creation_timestamp": 1633581620,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "ClusterIP",
        "selector": json.dumps({"app": "simple"}),
        "cluster_ip": "10.0.1.3",
        "pod_ids": [],
        "load_balancer_ip": None,
    },
]
