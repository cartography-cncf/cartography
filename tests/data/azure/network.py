# Mock data for Virtual Networks
MOCK_VNETS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet",
        "name": "my-test-vnet",
        "location": "eastus",
        "properties": {
            "provisioning_state": "Succeeded",
        },
    },
]

# Mock data for Network Security Groups
MOCK_NSGS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg",
        "name": "my-test-nsg",
        "location": "eastus",
    },
]

# Mock data for Subnets
MOCK_SUBNETS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
        "name": "subnet-with-nsg",
        "properties": {
            "address_prefix": "10.0.1.0/24",
        },
        # This object MUST be at the top level to match the real API
        "network_security_group": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg",
        },
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-without-nsg",
        "name": "subnet-without-nsg",
        "properties": {
            "address_prefix": "10.0.2.0/24",
        },
        "network_security_group": None,
    },
]
