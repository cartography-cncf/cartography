from uuid import uuid4

from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_SECRETS_DATA = [
    {
        "composite_id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/my-secret-1",
        "uid": uuid4().hex,
        "name": "my-secret-1",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/my-secret-2",
        "uid": uuid4().hex,
        "name": "my-secret-2",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-key",
        "uid": uuid4().hex,
        "name": "api-key",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_NAMES[0]}/{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/oauth-token",
        "uid": uuid4().hex,
        "name": "oauth-token",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "Opaque",
    },
]
