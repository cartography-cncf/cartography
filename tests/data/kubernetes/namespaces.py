from uuid import uuid4

GET_NAMESPACES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "kube-system",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
    },
    {
        "uid": uuid4().hex,
        "name": "my-namespace",
        "creation_timestamp": 1633581667,
        "deletion_timestamp": None,
    },
]


GET_CLUSTER_DATA = {
    "uid": GET_NAMESPACES_DATA[0]["uid"],
    "name": "my-cluster",
}
