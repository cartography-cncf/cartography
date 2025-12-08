import json
from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

RANDOM_ID = [uuid4().hex, uuid4().hex]


KUBERNETES_CONTAINER_DATA = [
    {
        "name": "my-pod-container",
        "image": "my-image",
        "uid": f"{RANDOM_ID[0]}-my-pod-container",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "pod_id": RANDOM_ID[0],
        "imagePullPolicy": "always",
        "status_image_id": "my-image-id",
        "status_image_sha": "my-image-sha",
        "status_ready": True,
        "status_started": True,
        "status_state": "running",
        "memory_request": "128Mi",
        "cpu_request": "100m",
        "memory_limit": "256Mi",
        "cpu_limit": "500m",
    },
    {
        "name": "my-service-pod-container",
        "image": "my-image-1:latest",
        "uid": f"{RANDOM_ID[1]}-my-pod-container",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "pod_id": RANDOM_ID[1],
        "imagePullPolicy": "always",
        "status_image_id": "my-image-id",
        "status_image_sha": "my-image-sha",
        "status_ready": False,
        "status_started": True,
        "status_state": "terminated",
        "memory_request": "64Mi",
        "cpu_request": "50m",
        "memory_limit": "128Mi",
        "cpu_limit": "200m",
    },
]


KUBERNETES_PODS_DATA = [
    {
        "uid": RANDOM_ID[0],
        "name": "my-pod",
        "status_phase": "running",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "node": "my-node",
        "labels": json.dumps(
            {
                "key1": "val1",
                "key2": "val2",
            }
        ),
        "containers": [
            KUBERNETES_CONTAINER_DATA[0],
        ],
    },
    {
        "uid": RANDOM_ID[1],
        "name": "my-service-pod",
        "status_phase": "running",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "node": "my-node",
        "labels": json.dumps(
            {
                "key1": "val3",
                "key2": "val4",
            }
        ),
        "containers": [
            KUBERNETES_CONTAINER_DATA[1],
        ],
    },
]
