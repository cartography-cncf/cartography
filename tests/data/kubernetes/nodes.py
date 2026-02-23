KUBERNETES_CLUSTER_1_NODE_IDS = [
    "1da01014-2cb6-4e32-896f-aa2c7f0bc8f0",
]
KUBERNETES_CLUSTER_1_NODES_DATA = [
    {
        "uid": KUBERNETES_CLUSTER_1_NODE_IDS[0],
        "name": "my-node",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "architecture": "arm64",
        "operating_system": "linux",
        "os_image": "Amazon Linux 2",
        "kernel_version": "5.10.0",
        "container_runtime_version": "containerd://1.7.27",
        "kubelet_version": "v1.29.15-eks",
        "provider_id": "aws:///us-east-1f/i-00000000000000000",
        "ready": True,
    },
]


# Redacted from live `kubectl get nodes -o json` payloads.
KUBERNETES_NODES_LIVE_REDACTED_DATA = [
    {
        "uid": "00000000-0000-0000-0000-000000000000",
        "name": "ip-172-31-76-117.ec2.internal",
        "creation_timestamp": 1738223742,
        "deletion_timestamp": None,
        "architecture": "amd64",
        "operating_system": "linux",
        "os_image": "Amazon Linux 2",
        "kernel_version": "5.10.238-231.953.amzn2.x86_64",
        "container_runtime_version": "containerd://1.7.27",
        "kubelet_version": "v1.29.15-eks-473151a",
        "provider_id": "aws:///us-east-1f/i-00000000000000000",
        "ready": True,
    },
]
