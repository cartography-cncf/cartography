import pytest

from cartography.intel.runpod.catalog import transform as transform_data_centers
from cartography.intel.runpod.clusters import transform as transform_clusters
from cartography.intel.runpod.pods import transform as transform_pods
from cartography.intel.runpod.serverless import transform as transform_serverless
from cartography.intel.runpod.templates import transform as transform_templates

ACCOUNT_ID = "runpod-test-account"


def test_pod_transform_accepts_documented_v2_shape():
    rows = transform_pods(
        [
            {
                "id": "pod-1",
                "name": "pytorch-training",
                "image": "runpod/pytorch:latest",
                "disk": 50,
                "ports": ["8888/http", "22/tcp"],
                "registry": {"id": "registry-1"},
                "status": "RUNNING",
                "mounts": {
                    "persistent": {"size": 20, "path": "/workspace"},
                    "network": [{"volumeId": "volume-1", "path": "/models"}],
                },
                "gpu": {"id": "NVIDIA GeForce RTX 4090", "count": 1},
                "cpu": {"vcpuCount": 8, "memory": 64},
                "dataCenterId": "US-KS-2",
                "ssh": {
                    "proxy": {"host": "ssh.runpod.io", "command": "ssh pod"},
                    "direct": {"host": "195.26.233.3", "command": "ssh root"},
                },
                "template": "template-1",
                "runtime": {"ports": [{"private": 22, "public": 34446, "type": "tcp"}]},
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["container_disk_in_gb"] == 50
    assert rows[0]["volume_in_gb"] == 20
    assert rows[0]["vcpu_count"] == 8
    assert rows[0]["memory_in_gb"] == 64
    assert rows[0]["volume_mount_path"] == "/workspace"
    assert rows[0]["network_volume_id"] == "volume-1"
    assert rows[0]["registry_id"] == "registry-1"
    assert rows[0]["runtime_ports"] == ["tcp:22:34446"]
    assert "ssh_proxy" not in rows[0]
    assert "ssh_direct" not in rows[0]


def test_pod_transform_preserves_zero_numeric_values_and_unwraps_template():
    rows = transform_pods(
        [
            {
                "id": "pod-1",
                "cpu": {"vcpuCount": 0, "memory": 0},
                "containerDiskInGb": 0,
                "volumeInGb": 0,
                "template": {"id": "template-1", "name": "ignored"},
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["vcpu_count"] == 0
    assert rows[0]["memory_in_gb"] == 0
    assert rows[0]["container_disk_in_gb"] == 0
    assert rows[0]["volume_in_gb"] == 0
    assert rows[0]["template_id"] == "template-1"


def test_pod_transform_uses_openapi_network_mount_volume_id():
    rows = transform_pods(
        [
            {
                "id": "pod-1",
                "mounts": {
                    "network": [{"volumeId": "volume-1", "path": "/models"}],
                },
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["network_volume_id"] == "volume-1"


def test_serverless_transform_accepts_documented_v2_shape():
    rows = transform_serverless(
        [
            {
                "id": "endpoint-1",
                "name": "image-generator",
                "type": "QUEUE",
                "requestUrls": {
                    "run": "https://api.runpod.ai/v2/endpoint-1/run",
                    "runSync": "https://api.runpod.ai/v2/endpoint-1/runsync",
                },
                "image": "runpod/pytorch:latest",
                "gpu": {"pools": ["ADA_24"], "count": 1},
                "workers": {"min": 0, "max": 5, "idleTimeout": 5},
                "scaling": {"type": "QUEUE_DELAY", "queueDelay": 4},
                "dataCenterIds": ["US-KS-2"],
                "networkVolumes": ["volume-1"],
                "ports": ["8000/http"],
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["image_name"] == "runpod/pytorch:latest"
    assert rows[0]["gpu_type_ids"] == ["ADA_24"]
    assert rows[0]["network_volume_ids"] == ["volume-1"]
    assert rows[0]["scaler_type"] == "QUEUE_DELAY"
    assert rows[0]["scaler_value"] == 4
    assert "request_url" not in rows[0]
    assert "request_urls" not in rows[0]


def test_serverless_transform_accepts_object_id_lists():
    rows = transform_serverless(
        [
            {
                "id": "endpoint-1",
                "gpuTypeIds": [{"id": "ADA_24"}],
                "networkVolumeIds": [{"id": "volume-1"}],
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["gpu_type_ids"] == ["ADA_24"]
    assert rows[0]["network_volume_ids"] == ["volume-1"]


def test_serverless_transform_rejects_malformed_object_id_lists():
    endpoint = {"id": "endpoint-1", "gpuTypeIds": [{"name": "ADA_24"}]}

    with pytest.raises(ValueError):
        transform_serverless([endpoint], ACCOUNT_ID)


def test_serverless_transform_preserves_intentionally_empty_new_field():
    rows = transform_serverless(
        [
            {
                "id": "endpoint-1",
                "gpuTypeIds": [],
                "gpuIds": ["legacy-gpu-id"],
                "networkVolumeIds": [],
                "networkVolumes": ["legacy-volume-id"],
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["gpu_type_ids"] == []
    assert rows[0]["network_volume_ids"] == []


def test_template_transform_accepts_documented_v2_shape():
    rows = transform_templates(
        [
            {
                "id": "template-1",
                "name": "PyTorch GPU Template",
                "image": "runpod/pytorch:latest",
                "disk": 50,
                "mounts": {"persistent": {"size": 20, "path": "/workspace"}},
                "ports": ["8888/http"],
                "env": {"JUPYTER_ENABLE_LAB": "yes"},
                "registry": {"id": "registry-1"},
                "serverless": False,
                "public": False,
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["image_name"] == "runpod/pytorch:latest"
    assert rows[0]["container_disk_in_gb"] == 50
    assert rows[0]["volume_in_gb"] == 20
    assert rows[0]["volume_mount_path"] == "/workspace"
    assert rows[0]["registry_id"] == "registry-1"
    assert "env_keys" not in rows[0]


def test_template_transform_preserves_zero_numeric_values():
    rows = transform_templates(
        [
            {
                "id": "template-1",
                "containerDiskInGb": 0,
                "volumeInGb": 0,
                "mounts": {"persistent": {"size": 20}},
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["container_disk_in_gb"] == 0
    assert rows[0]["volume_in_gb"] == 0


def test_cluster_transform_accepts_documented_v2_shape():
    rows = transform_clusters(
        [
            {
                "id": "cluster-1",
                "name": "training-cluster",
                "compute": {"gpuTypeId": "NVIDIA A100", "gpuCountPerPod": 2},
                "pods": {"total": 4, "byStatus": {"RUNNING": 3}},
                "primary": {"podId": "pod-1", "sshEndpoint": "ssh.runpod.io:2200"},
                "template": "template-1",
                "dataCenterId": "US-KS-2",
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["gpu_type_id"] == "NVIDIA A100"
    assert rows[0]["gpu_count"] == 8
    assert rows[0]["pod_count"] == 4
    assert rows[0]["running_pod_count"] == 3
    assert rows[0]["primary_pod_id"] == "pod-1"
    assert rows[0]["template_id"] == "template-1"


def test_cluster_transform_unwraps_nested_template():
    rows = transform_clusters(
        [{"id": "cluster-1", "template": {"id": "template-1", "name": "ignored"}}],
        ACCOUNT_ID,
    )

    assert rows[0]["template_id"] == "template-1"


def test_cluster_transform_handles_non_object_pods_block():
    rows = transform_clusters(
        [
            {
                "id": "cluster-1",
                "compute": {"gpuTypeId": "NVIDIA A100", "gpuCountPerPod": 2},
                "pods": [],
                "podCount": 4,
                "runningPodCount": 3,
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["gpu_count"] == 8
    assert rows[0]["pod_count"] == 4
    assert rows[0]["running_pod_count"] == 3


def test_catalog_transform_accepts_documented_v2_shape():
    rows = transform_data_centers(
        [
            {
                "id": "US-KS-2",
                "name": "US Kansas 2",
                "region": "NORTH_AMERICA",
                "globalNetwork": True,
                "networkVolumeTypes": ["STANDARD", "HIGH_PERFORMANCE"],
                "compliance": ["SOC_2_TYPE_2"],
                "gpuAvailability": [{"id": "NVIDIA GeForce RTX 4090"}],
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["location"] == "NORTH_AMERICA"
    assert rows[0]["global_networking"] is True
    assert rows[0]["volume_types"] == ["STANDARD", "HIGH_PERFORMANCE"]
    assert rows[0]["gpu_type_ids"] == ["NVIDIA GeForce RTX 4090"]


def test_catalog_transform_preserves_intentionally_empty_new_field():
    rows = transform_data_centers(
        [
            {
                "id": "US-KS-2",
                "gpuTypes": [],
                "gpuAvailability": [{"id": "NVIDIA GeForce RTX 4090"}],
                "volumeTypes": [],
                "networkVolumeTypes": ["STANDARD"],
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["gpu_type_ids"] == []
    assert rows[0]["volume_types"] == []
