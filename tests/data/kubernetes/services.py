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
]
