KUBERNETES_CLUSTER_IDS = [
    "d3492d6f-e73b-4a7c-80b5-878ede16f459",
    "701314e6-f4c5-47d1-8658-e5bf3a0a76e9",
]
KUBERNETES_CLUSTER_NAMES = ["my-cluster-1", "my-cluster-2"]

KUBERNETES_CLUSTER_DATA = [
    {
        "id": KUBERNETES_CLUSTER_IDS[0],
        "name": KUBERNETES_CLUSTER_NAMES[0],
        "creation_timestamp": 1234567890,
        "external_id": f"arn:aws:eks::1234567890:cluster/{KUBERNETES_CLUSTER_NAMES[0]}",
        "git_version": "v1.30.0",
        "version_major": 1,
        "version_minor": 30,
        "go_version": "go1.16.5",
        "compiler": "gc",
        "platform": "linux/amd64",
    },
    {
        "id": KUBERNETES_CLUSTER_IDS[1],
        "name": KUBERNETES_CLUSTER_NAMES[1],
        "creation_timestamp": 1234567890,
        "external_id": f"arn:aws:eks::1234567890:cluster/{KUBERNETES_CLUSTER_NAMES[1]}",
        "git_version": "v1.30.0",
        "version_major": 1,
        "version_minor": 30,
        "go_version": "go1.16.5",
        "compiler": "gc",
        "platform": "linux/amd64",
    },
]
