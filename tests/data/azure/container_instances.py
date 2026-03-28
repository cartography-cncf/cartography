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
