from uuid import uuid4

from tests.data.kubernetes.namespaces import GET_CLUSTER_DATA
from tests.data.kubernetes.namespaces import GET_NAMESPACES_DATA

RANDOM_ID = [uuid4().hex, uuid4().hex]
GET_PODS_DATA = [
    {
        "uid": RANDOM_ID[0],
        "name": "my-pod",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": GET_NAMESPACES_DATA[-1]["name"],
        "node": "my-node",
        "cluster_uid": GET_CLUSTER_DATA["uid"],
        "labels": {
            "key1": "val1",
            "key2": "val2",
        },
        "containers": [
            {
                "name": "my-pod-container",
                "image": "my-image",
                "uid": f"{RANDOM_ID[0]}-my-pod-container",
            },
        ],
    },
    {
        "uid": RANDOM_ID[1],
        "name": "my-service-pod",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": GET_NAMESPACES_DATA[-1]["name"],
        "node": "my-node",
        "cluster_uid": GET_CLUSTER_DATA["uid"],
        "labels": {
            "key1": "val3",
            "key2": "val4",
        },
        "containers": [
            {
                "name": "my-service-pod-container",
                "image": "my-image",
                "uid": f"{RANDOM_ID[1]}-my-pod-container",
            },
        ],
    },
]
