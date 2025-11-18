# flake8: noqa
MOCK_STORAGE_BUCKETS = {
    "kind": "storage#buckets",
    "items": [
        {
            "kind": "storage#bucket",
            "id": "test-bucket",
            "selfLink": "https://www.googleapis.com/storage/v1/b/test-bucket",
            "projectNumber": 123456789,
            "name": "test-bucket",
            "timeCreated": "2023-01-01T00:00:00.000Z",
            "updated": "2023-01-01T00:00:00.000Z",
            "metageneration": "1",
            "iamConfiguration": {
                "bucketPolicyOnly": {
                    "enabled": False,
                },
                "uniformBucketLevelAccess": {
                    "enabled": False,
                },
            },
            "location": "US",
            "locationType": "multi-region",
            "defaultEventBasedHold": False,
            "storageClass": "STANDARD",
            "etag": "CAE=",
        },
    ],
}

MOCK_COMPUTE_INSTANCES = {
    "id": "projects/project-123/zones/us-east1-b/instances",
    "items": [
        {
            "canIpForward": False,
            "cpuPlatform": "Intel Haswell",
            "creationTimestamp": "2023-01-01T00:00:00.000Z",
            "description": "Test compute instance",
            "disks": [
                {
                    "autoDelete": True,
                    "boot": True,
                    "deviceName": "instance-1",
                    "index": 0,
                    "interface": "SCSI",
                    "kind": "compute#attachedDisk",
                    "mode": "READ_WRITE",
                    "source": "https://www.googleapis.com/compute/v1/projects/project-123/zones/us-east1-b/disks/instance-1",
                    "type": "PERSISTENT",
                },
            ],
            "id": "123456789",
            "kind": "compute#instance",
            "machineType": "https://www.googleapis.com/compute/v1/projects/project-123/zones/us-east1-b/machineTypes/n1-standard-1",
            "name": "instance-1",
            "networkInterfaces": [
                {
                    "accessConfigs": [
                        {
                            "kind": "compute#accessConfig",
                            "name": "External NAT",
                            "natIP": "1.2.3.4",
                            "networkTier": "PREMIUM",
                            "type": "ONE_TO_ONE_NAT",
                        },
                    ],
                    "kind": "compute#networkInterface",
                    "name": "nic0",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-123/global/networks/default",
                    "networkIP": "10.0.0.1",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-123/regions/us-east1/subnetworks/default",
                },
            ],
            "scheduling": {
                "automaticRestart": True,
                "onHostMaintenance": "MIGRATE",
                "preemptible": False,
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-123/zones/us-east1-b/instances/instance-1",
            "serviceAccounts": [
                {
                    "email": "sa@project-123.iam.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                    ],
                },
            ],
            "status": "RUNNING",
            "zone": "https://www.googleapis.com/compute/v1/projects/project-123/zones/us-east1-b",
        },
    ],
    "kind": "compute#instanceList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-123/zones/us-east1-b/instances",
}

MOCK_PERMISSION_RELATIONSHIPS_YAML = [
    {
        "target_label": "GCPBucket",
        "permissions": [
            "storage.objects.get",
        ],
        "relationship_name": "CAN_READ",
    },
    {
        "target_label": "GCPInstance",
        "permissions": [
            "compute.acceleratorTypes.get",
        ],
        "relationship_name": "CAN_GET_ACCELERATOR_TYPES",
    },
]
