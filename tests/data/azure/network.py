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


# Mock data for Public IP Addresses
MOCK_PUBLIC_IPS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-1",
        "name": "my-public-ip-1",
        "location": "eastus",
        "ip_address": "20.10.30.40",
        "public_ip_allocation_method": "Static",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-2",
        "name": "my-public-ip-2",
        "location": "eastus",
        "ip_address": "20.10.30.41",
        "public_ip_allocation_method": "Dynamic",
    },
]


# Mock data for Network Interfaces
MOCK_NETWORK_INTERFACES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-1",
        "name": "my-nic-1",
        "location": "eastus",
        "mac_address": "00-0D-3A-1B-C7-21",
        # Reference objects are at top level in SDK response
        "virtual_machine": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/my-vm-1",
        },
        "ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-1/ipConfigurations/ipconfig1",
                "name": "ipconfig1",
                "properties": {
                    "private_ip_address": "10.0.1.4",
                    "subnet": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
                    },
                    "public_ip_address": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-1",
                    },
                },
            },
        ],
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-2",
        "name": "my-nic-2",
        "location": "eastus",
        "mac_address": "00-0D-3A-1B-C7-22",
        "virtual_machine": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/my-vm-2",
        },
        "ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-2/ipConfigurations/ipconfig1",
                "name": "ipconfig1",
                "properties": {
                    "private_ip_address": "10.0.2.4",
                    "subnet": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-without-nsg",
                    },
                    # No public IP for this NIC
                },
            },
        ],
    },
    {
        # NIC without a VM (e.g., unattached NIC)
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-unattached",
        "name": "my-nic-unattached",
        "location": "eastus",
        "mac_address": None,
        "virtual_machine": None,
        "ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-unattached/ipConfigurations/ipconfig1",
                "name": "ipconfig1",
                "properties": {
                    "private_ip_address": "10.0.1.5",
                    "subnet": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
                    },
                    "public_ip_address": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-2",
                    },
                },
            },
        ],
    },
]
