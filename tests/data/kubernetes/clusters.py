from uuid import uuid4


KUBERNETES_CLUSTER_ID = uuid4().hex
KUBERNETES_CLUSTER_NAME = "my-cluster"

KUBERNETES_CLUSTER_DATA = [
    {
        "id": KUBERNETES_CLUSTER_ID,
        "name": KUBERNETES_CLUSTER_NAME,
        "creation_timestamp": 12345678901,
        "external_id": f"arn:aws:eks::1234567890:cluster/{KUBERNETES_CLUSTER_NAME}",
        "git_version": "v1.30.0",
        "version_major": 1,
        "version_minor": 30,
        "go_version": "go1.16.5",
        "compiler": "gc",
        "platform": "linux/amd64",
    },
]
