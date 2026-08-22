TEST_ACCOUNT_ID = "runpod-test-account"
TEST_UPDATE_TAG = 123456789

SSH_KEYS_RESPONSE = [
    "ssh-rsa AQID laptop@example",
]

REGISTRIES_RESPONSE = [
    {
        "id": "registry-1",
        "name": "private-registry",
    }
]

NETWORK_VOLUMES_RESPONSE = [
    {
        "id": "volume-1",
        "name": "models",
        "size": 100,
        "type": "network",
        "dataCenterId": "EU-SE-1",
        "createdAt": "2026-08-01T00:00:00Z",
    }
]

TEMPLATES_RESPONSE = [
    {
        "id": "template-1",
        "name": "pytorch-ssh",
        "imageName": "runpod/pytorch:latest",
        "containerDiskInGb": 40,
        "volumeInGb": 10,
        "volumeMountPath": "/workspace",
        "containerRegistryId": "registry-1",
        "isPublic": False,
        "serverless": False,
        "category": "gpu",
        "startSsh": True,
        "startJupyter": False,
        "ports": [{"privatePort": 22, "protocol": "tcp"}],
        "env": {"HF_TOKEN": "discarded"},
    }
]

PODS_RESPONSE = [
    {
        "id": "pod-1",
        "name": "training-pod",
        "status": "RUNNING",
        "imageName": "runpod/pytorch:latest",
        "machineId": "machine-1",
        "dataCenterId": "EU-SE-1",
        "gpu": {"id": "NVIDIA A100", "count": 1},
        "cpu": {"vcpuCount": 8, "memory": 64},
        "containerDiskInGb": 40,
        "volumeInGb": 10,
        "volumeMountPath": "/workspace",
        "mounts": {"network": [{"volumeId": "volume-1", "path": "/models"}]},
        "template": "template-1",
        "registry": "registry-1",
        "globalNetworking": {"enabled": True},
        "ports": [{"privatePort": 8888, "publicPort": 12345, "protocol": "http"}],
        "runtime": {
            "publicIp": "203.0.113.10",
            "ports": [{"privatePort": 22, "publicPort": 30022, "protocol": "tcp"}],
            "ssh": {"proxy": "ssh.runpod.io:22", "direct": "203.0.113.10:30022"},
        },
        "createdAt": "2026-08-01T00:00:00Z",
        "startedAt": "2026-08-01T00:05:00Z",
    }
]

SERVERLESS_RESPONSE = [
    {
        "id": "endpoint-1",
        "name": "inference",
        "type": "serverless",
        "imageName": "registry.example.com/inference:latest",
        "gpuTypeIds": ["NVIDIA A40"],
        "dataCenterIds": ["EU-SE-1"],
        "networkVolumeIds": ["volume-1"],
        "workers": {"min": 0, "max": 3, "idleTimeout": 5},
        "scaler": {"type": "QUEUE_DELAY", "value": 4},
        "timeout": 60,
        "requestUrl": "https://api.runpod.ai/v2/endpoint-1/runsync",
        "requestUrls": ["https://api.runpod.ai/v2/endpoint-1/run"],
        "ports": [{"privatePort": 8080, "protocol": "http"}],
        "createdAt": "2026-08-01T00:00:00Z",
    }
]

CLUSTERS_RESPONSE = [
    {
        "id": "cluster-1",
        "name": "training-cluster",
        "dataCenterId": "EU-SE-1",
        "gpu": {"id": "NVIDIA A100", "count": 8},
        "pods": {"count": 4, "running": 4},
        "primaryPod": {"id": "pod-1", "sshEndpoint": "ssh.runpod.io:2200"},
        "templateId": "template-1",
        "createdAt": "2026-08-01T00:00:00Z",
    }
]

DATA_CENTERS_RESPONSE = [
    {
        "id": "EU-SE-1",
        "name": "EU Sweden 1",
        "location": "Sweden",
        "countryCode": "SE",
        "gpuTypes": [{"id": "NVIDIA A100"}],
        "compliance": ["ISO27001"],
        "volumeTypes": ["network"],
        "globalNetworking": True,
    }
]
