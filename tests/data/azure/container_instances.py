TEST_GROUP_CONTAINER_DIGEST = (
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
TEST_CONTAINER_GROUP_ID = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci"

MOCK_CONTAINER_GROUP_WITH_CONTAINERS = [
    {
        "id": TEST_CONTAINER_GROUP_ID,
        "name": "my-test-aci",
        "location": "eastus",
        "type": "Microsoft.ContainerInstance/containerGroups",
        "provisioning_state": "Succeeded",
        "os_type": "Linux",
        "containers": [
            {
                "name": "my-container",
                "image": f"myregistry.azurecr.io/myimage@{TEST_GROUP_CONTAINER_DIGEST}",
                "resources": {
                    "requests": {"cpu": 1.0, "memory_in_gb": 1.5},
                    "limits": {"cpu": 2.0, "memory_in_gb": 3.0},
                },
                "instance_view": {
                    "current_state": {
                        "state": "Running",
                    },
                },
            },
        ],
    },
]

MOCK_CONTAINER_GROUPS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
        "name": "my-test-aci",
        "location": "eastus",
        "type": "Microsoft.ContainerInstance/containerGroups",
        "provisioning_state": "Succeeded",
        "ip_address": {
            "ip": "20.245.100.1",
            "type": "Public",
        },
        "os_type": "Linux",
        "tags": {"env": "prod", "service": "container-instance"},
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-private-aci",
        "name": "my-private-aci",
        "location": "eastus",
        "type": "Microsoft.ContainerInstance/containerGroups",
        "provisioning_state": "Succeeded",
        "ip_address": {
            "ip": "10.0.1.5",
            "type": "Private",
        },
        "os_type": "Linux",
        "subnet_ids": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/my-test-subnet",
            },
        ],
        "tags": {"env": "prod", "service": "container-instance"},
    },
]
