from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

KUBERNETES_SECRETS_DATA = [
    {
        "composite_id": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/db-credentials",
        "uid": uuid4().hex,
        "name": "db-credentials",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "owner_references": None,
        "type": "Opaque",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/tls-cert",
        "uid": uuid4().hex,
        "name": "tls-cert",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "owner_references": None,
        "type": "kubernetes.io/tls",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/api-key",
        "uid": uuid4().hex,
        "name": "api-key",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "owner_references": None,
        "type": "Opaque",
    },
    {
        "composite_id": f"{KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]['name']}/oauth-token",
        "uid": uuid4().hex,
        "name": "oauth-token",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "owner_references": None,
        "type": "Opaque",
    },
]
