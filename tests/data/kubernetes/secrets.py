from uuid import uuid4

from tests.data.kubernetes.namespaces import GET_CLUSTER_DATA
from tests.data.kubernetes.namespaces import GET_NAMESPACES_DATA

GET_SECRETS_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-secret",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": GET_NAMESPACES_DATA[-1]["name"],
        "cluster_uid": GET_CLUSTER_DATA["uid"],
        "type": "Opaque",
    },
]
