from uuid import uuid4

from tests.data.kubernetes.namespaces import GET_CLUSTER_DATA
from tests.data.kubernetes.namespaces import GET_NAMESPACES_DATA
from tests.data.kubernetes.pods import GET_PODS_DATA

GET_SERVICES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-service",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": 1633581966,
        "namespace": GET_NAMESPACES_DATA[-1]["name"],
        "cluster_uid": GET_CLUSTER_DATA["uid"],
        "type": "ClusterIP",
        "pods": [
            {
                "uid": GET_PODS_DATA[-1]["uid"],
                "name": GET_PODS_DATA[-1]["name"],
            },
        ],
        "load_balancer_ip": "1.1.1.1",
        "ingress_host": "myhost.local",
    },
]
