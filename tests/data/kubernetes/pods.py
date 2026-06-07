import json
from uuid import uuid4

from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

RANDOM_ID = [uuid4().hex, uuid4().hex]


KUBERNETES_CONTAINER_DATA = [
    {
        "name": "my-pod-container",
        "image": "my-image",
        "uid": f"{RANDOM_ID[0]}-my-pod-container",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "pod_id": RANDOM_ID[0],
        "image_pull_policy": "always",
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
        "image_pull_policy": "always",
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
        "service_account_name": "default",
        "service_account_id": (
            f"{KUBERNETES_CLUSTER_NAMES[0]}/"
            f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/default"
        ),
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
        "secret_volume_ids": [
            f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/my-secret-1",
            f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/my-secret-2",
        ],
        "secret_env_ids": [],
    },
    {
        "uid": RANDOM_ID[1],
        "name": "my-service-pod",
        "status_phase": "running",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "service_account_name": "workload-sa",
        "service_account_id": (
            f"{KUBERNETES_CLUSTER_NAMES[0]}/"
            f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/workload-sa"
        ),
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
        "secret_volume_ids": [],
        "secret_env_ids": [
            f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-key",
            f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/oauth-token",
        ],
    },
]


KUBERNETES_POD_SERVICE_ACCOUNTS_DATA = [
    {
        "id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/default",
        "name": "default",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "uid": "my-namespace-default-sa-uid",
        "creation_timestamp": 1633581666,
        "resource_version": "1001",
    },
    {
        "id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/workload-sa",
        "name": "workload-sa",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "uid": "my-namespace-workload-sa-uid",
        "creation_timestamp": 1633581667,
        "resource_version": "1002",
    },
]


KUBERNETES_CLUSTER_2_POD_SERVICE_ACCOUNTS_DATA = [
    {
        "id": f"{KUBERNETES_CLUSTER_NAMES[1]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/default",
        "name": "default",
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "uid": "cluster-2-my-namespace-default-sa-uid",
        "creation_timestamp": 1633581668,
        "resource_version": "2001",
    },
]
