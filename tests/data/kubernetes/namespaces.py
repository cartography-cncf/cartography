from uuid import uuid4


KUBERNETES_NAMESPACES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "kube-system",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
    {
        "uid": uuid4().hex,
        "name": "my-namespace",
        "creation_timestamp": 1633581667,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
]
