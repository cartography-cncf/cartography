from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES

KUBERNETES_CLUSTER_1_NAMESPACE_IDS = [
    "6071ed5a-9143-49b2-9a13-5daa89b28f79",
    "facef6c5-5766-41c9-bed0-d8d5261b0b94",
]
KUBERNETES_CLUSTER_1_NAMESPACES_DATA = [
    {
        "uid": KUBERNETES_CLUSTER_1_NAMESPACE_IDS[0],
        "name": "kube-system",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
    {
        "uid": KUBERNETES_CLUSTER_1_NAMESPACE_IDS[1],
        "name": "my-namespace",
        "creation_timestamp": 1633581667,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
]

KUBERNETES_CLUSTER_2_NAMESPACE_IDS = [
    "67dda55a-849f-498a-aca8-a4fe0bd10521",
    "4625bf85-0fd5-40d5-b79b-c02285c2634c",
]
KUBERNETES_CLUSTER_2_NAMESPACES_DATA = [
    {
        "uid": KUBERNETES_CLUSTER_2_NAMESPACE_IDS[0],
        "name": "kube-system",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "status_phase": "Active",
        "cluster_name": KUBERNETES_CLUSTER_NAMES[1],
    },
    {
        "uid": KUBERNETES_CLUSTER_2_NAMESPACE_IDS[1],
        "name": "my-namespace",
        "creation_timestamp": 1633581667,
        "deletion_timestamp": None,
        "status_phase": "Active",
        "cluster_name": KUBERNETES_CLUSTER_NAMES[1],
    },
]
