from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_SECRETS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-secret-1",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
    {
        "uid": uuid4().hex,
        "name": "my-secret-2",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
]
