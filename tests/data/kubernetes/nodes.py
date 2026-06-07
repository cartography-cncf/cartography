from types import SimpleNamespace
from uuid import uuid4

from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES

CLUSTER_NAME = KUBERNETES_CLUSTER_NAMES[0]

RAW_NODES = [
    SimpleNamespace(
        metadata=SimpleNamespace(name="my-node"),
        status=SimpleNamespace(
            node_info=SimpleNamespace(
                architecture="amd64",
                operating_system="linux",
                os_image="Ubuntu 22.04.3 LTS",
                kernel_version="5.15.0-1034-aws",
                container_runtime_version="containerd://1.7.0",
                kubelet_version="v1.27.1",
            )
        ),
    ),
    SimpleNamespace(
        metadata=SimpleNamespace(name="my-arm-node"),
        status=SimpleNamespace(
            node_info=SimpleNamespace(
                architecture="arm64",
                operating_system="linux",
                os_image="Ubuntu 22.04.3 LTS",
                kernel_version="5.15.0-1034-aws",
                container_runtime_version="containerd://1.7.0",
                kubelet_version="v1.27.1",
            )
        ),
    ),
]

RAW_PODS = [
    SimpleNamespace(
        metadata=SimpleNamespace(
            uid=uuid4().hex,
            name="node-test-pod",
            namespace="default",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[
                SimpleNamespace(
                    name="node-test-container",
                    image="node-test:latest",
                    image_pull_policy="IfNotPresent",
                    resources=None,
                    env=None,
                    env_from=None,
                ),
            ],
            volumes=[],
            node_name="my-node",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="running", container_statuses=[]),
    ),
]

KUBERNETES_NODE_DATA = [
    {
        "id": f"{CLUSTER_NAME}/my-node",
        "name": "my-node",
        "architecture": "amd64",
        "architecture_normalized": "amd64",
        "os": "linux",
        "os_image": "Ubuntu 22.04.3 LTS",
        "kernel_version": "5.15.0-1034-aws",
        "container_runtime_version": "containerd://1.7.0",
        "kubelet_version": "v1.27.1",
    },
    {
        "id": f"{CLUSTER_NAME}/my-arm-node",
        "name": "my-arm-node",
        "architecture": "arm64",
        "architecture_normalized": "arm64",
        "os": "linux",
        "os_image": "Ubuntu 22.04.3 LTS",
        "kernel_version": "5.15.0-1034-aws",
        "container_runtime_version": "containerd://1.7.0",
        "kubelet_version": "v1.27.1",
    },
]
