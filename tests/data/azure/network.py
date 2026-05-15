# Mock data for Virtual Networks
# Structure matches Azure SDK's .as_dict() output (flattened, not nested under "properties")
MOCK_VNETS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet",
        "name": "my-test-vnet",
        "location": "eastus",
        "properties": {
            "provisioning_state": "Succeeded",
        },
        "tags": {"env": "prod", "service": "vnet"},
    },
]

# Mock data for Network Security Groups
MOCK_NSGS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg",
        "name": "my-test-nsg",
        "location": "eastus",
        "tags": {"env": "prod", "service": "nsg"},
        "security_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg/securityRules/allow-ssh-from-internet",
                "name": "allow-ssh-from-internet",
                "description": "Allow SSH from the internet",
                "protocol": "Tcp",
                "direction": "Inbound",
                "access": "Allow",
                "priority": 100,
                "source_port_range": "*",
                "destination_port_range": "22",
                "source_address_prefix": "*",
                "destination_address_prefix": "*",
            },
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg/securityRules/deny-rdp",
                "name": "deny-rdp",
                "properties": {
                    "protocol": "Tcp",
                    "direction": "Inbound",
                    "access": "Deny",
                    "priority": 200,
                    "source_port_range": "*",
                    "destination_port_ranges": ["3389"],
                    "source_address_prefix": "Internet",
                    "destination_address_prefix": "*",
                },
            },
        ],
        "default_security_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg/defaultSecurityRules/AllowVnetInBound",
                "name": "AllowVnetInBound",
                "protocol": "*",
                "direction": "Inbound",
                "access": "Allow",
                "priority": 65000,
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": "VirtualNetwork",
                "destination_address_prefix": "VirtualNetwork",
            },
        ],
    },
]

# Mock data for Subnets
# Structure matches Azure SDK's .as_dict() output (flattened, not nested under "properties")
MOCK_SUBNETS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
        "name": "subnet-with-nsg",
        "address_prefix": "10.0.1.0/24",
        "network_security_group": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg",
        },
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-without-nsg",
        "name": "subnet-without-nsg",
        "address_prefix": "10.0.2.0/24",
        "network_security_group": None,
    },
]


# Mock data for Public IP Addresses
# This fixture includes both shapes that Azure SDK's .as_dict() may return:
# - flattened fields at the top level
# - fields nested under "properties"
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
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-3",
        "name": "my-public-ip-3",
        "location": "eastus",
        "properties": {
            "ip_address": "20.10.30.42",
            "public_ip_allocation_method": "Static",
        },
    },
]


# Mock data for Network Interfaces
# Structure matches Azure SDK's .as_dict() output (flattened, not nested under "properties")
MOCK_NETWORK_INTERFACES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-1",
        "name": "my-nic-1",
        "location": "eastus",
        "mac_address": "00-0D-3A-1B-C7-21",
        "virtual_machine": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/my-vm-1",
        },
        "network_security_group": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkSecurityGroups/my-test-nsg",
        },
        "ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-nic-1/ipConfigurations/ipconfig1",
                "name": "ipconfig1",
                "private_ip_address": "10.0.1.4",
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
                },
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-1",
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
                "private_ip_address": "10.0.2.4",
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-without-nsg",
                },
                # No public IP for this NIC
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
                "private_ip_address": "10.0.1.5",
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-test-vnet/subnets/subnet-with-nsg",
                },
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip-2",
                },
            },
        ],
    },
]
