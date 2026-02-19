MOCK_CONTAINER_GROUPS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
        "name": "my-test-aci",
        "location": "eastus",
        "type": "Microsoft.ContainerInstance/containerGroups",
        "properties": {
            "provisioning_state": "Succeeded",
            "ip_address": {
                "ip": "20.245.100.1",
            },
            "os_type": "Linux",
            "containers": [
                {
                    "name": "app",
                    "image": "mcr.microsoft.com/oss/nginx/nginx:1.25.3-amd64",
                },
                {
                    "name": "worker",
                    "image": "myregistry.azurecr.io/team/worker@sha256:abc123",
                },
            ],
        },
        "tags": {"env": "prod", "service": "container-instance"},
    },
]
