from types import SimpleNamespace
from uuid import uuid4

from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES

CLUSTER_NAME = KUBERNETES_CLUSTER_NAMES[0]

RAW_NODES = [
    SimpleNamespace(
        metadata=SimpleNamespace(
            name="my-node",
            labels={
                "nvidia.com/gpu.present": "true",
                "nvidia.com/gpu.product": "NVIDIA-H200",
            },
        ),
        spec=SimpleNamespace(
            provider_id="aws:///us-east-1a/i-0123456789abcdef0",
        ),
        status=SimpleNamespace(
            capacity={"cpu": "128", "memory": "2Ti", "nvidia.com/gpu": "8"},
            allocatable={
                "cpu": "127",
                "memory": "1900Gi",
                "nvidia.com/gpu": "8",
            },
            node_info=SimpleNamespace(
                architecture="amd64",
                operating_system="linux",
                os_image="Ubuntu 22.04.3 LTS",
                kernel_version="5.15.0-1034-aws",
                container_runtime_version="containerd://1.7.0",
                kubelet_version="v1.27.1",
            ),
        ),
    ),
    SimpleNamespace(
        metadata=SimpleNamespace(name="my-arm-node", labels={}),
        spec=SimpleNamespace(provider_id=None),
        status=SimpleNamespace(
            capacity={"cpu": "4", "memory": "16Gi"},
            allocatable={"cpu": "3900m", "memory": "15Gi"},
            node_info=SimpleNamespace(
                architecture="arm64",
                operating_system="linux",
                os_image="Ubuntu 22.04.3 LTS",
                kernel_version="5.15.0-1034-aws",
                container_runtime_version="containerd://1.7.0",
                kubelet_version="v1.27.1",
            ),
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
                    volume_mounts=None,
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
        "provider_id": "aws:///us-east-1a/i-0123456789abcdef0",
        "instance_id": "i-0123456789abcdef0",
        "labels": '{"nvidia.com/gpu.present": "true", "nvidia.com/gpu.product": "NVIDIA-H200"}',
        "capacity": '{"cpu": "128", "memory": "2Ti", "nvidia.com/gpu": "8"}',
        "allocatable": '{"cpu": "127", "memory": "1900Gi", "nvidia.com/gpu": "8"}',
        "gpu_capacity": 8,
        "gpu_allocatable": 8,
        "gpu_product": "NVIDIA-H200",
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
        "provider_id": None,
        "instance_id": None,
        "labels": "{}",
        "capacity": '{"cpu": "4", "memory": "16Gi"}',
        "allocatable": '{"cpu": "3900m", "memory": "15Gi"}',
        "gpu_capacity": None,
        "gpu_allocatable": None,
        "gpu_product": None,
        "architecture": "arm64",
        "architecture_normalized": "arm64",
        "os": "linux",
        "os_image": "Ubuntu 22.04.3 LTS",
        "kernel_version": "5.15.0-1034-aws",
        "container_runtime_version": "containerd://1.7.0",
        "kubelet_version": "v1.27.1",
    },
]
