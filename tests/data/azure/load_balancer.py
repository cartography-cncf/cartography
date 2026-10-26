MOCK_LOAD_BALANCERS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb",
        "name": "my-test-lb",
        "location": "eastus",
        "sku": {"name": "Standard"},
        "tags": {"env": "prod", "service": "load-balancer"},
        "frontend_ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/frontendIPConfigurations/my-lb-frontend",
                "name": "my-lb-frontend",
                "private_ip_address": "10.0.0.4",
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip",
                },
            },
        ],
        "backend_address_pools": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/backendAddressPools/my-lb-backend-pool",
                "name": "my-lb-backend-pool",
                "backend_ip_configurations": [
                    {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-test-nic/ipConfigurations/ipconfig1",
                    },
                ],
            },
        ],
        "load_balancing_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/loadBalancingRules/my-http-rule",
                "name": "my-http-rule",
                "protocol": "Tcp",
                "frontend_port": 80,
                "backend_port": 80,
                "frontend_ip_configuration": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/frontendIPConfigurations/my-lb-frontend",
                },
                "backend_address_pool": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/backendAddressPools/my-lb-backend-pool",
                },
            },
        ],
        "inbound_nat_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/inboundNatRules/my-rdp-rule",
                "name": "my-rdp-rule",
                "protocol": "Tcp",
                "frontend_port": 3389,
                "backend_port": 3389,
            },
        ],
    },
]

_LB_ID = MOCK_LOAD_BALANCERS[0]["id"]

# The same load balancer as an ARM response body, which is what azure-mgmt-network
# 31+ hands back from as_dict(): camelCase keys nested under "properties".
MOCK_LOAD_BALANCER_ARM = {
    "id": _LB_ID,
    "name": "my-test-lb",
    "location": "eastus",
    "sku": {"name": "Standard"},
    "tags": {"env": "prod", "service": "load-balancer"},
    "properties": {
        "frontendIPConfigurations": [
            {
                "id": f"{_LB_ID}/frontendIPConfigurations/my-lb-frontend",
                "name": "my-lb-frontend",
                "properties": {
                    "privateIPAddress": "10.0.0.4",
                    "publicIPAddress": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip",
                    },
                },
            },
        ],
        "backendAddressPools": [
            {
                "id": f"{_LB_ID}/backendAddressPools/my-lb-backend-pool",
                "name": "my-lb-backend-pool",
                "properties": {
                    "backendIPConfigurations": [
                        {
                            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-test-nic/ipConfigurations/ipconfig1",
                        },
                    ],
                },
            },
        ],
        "loadBalancingRules": [
            {
                "id": f"{_LB_ID}/loadBalancingRules/my-http-rule",
                "name": "my-http-rule",
                "properties": {
                    "protocol": "Tcp",
                    "frontendPort": 80,
                    "backendPort": 80,
                    "frontendIPConfiguration": {
                        "id": f"{_LB_ID}/frontendIPConfigurations/my-lb-frontend",
                    },
                    "backendAddressPool": {
                        "id": f"{_LB_ID}/backendAddressPools/my-lb-backend-pool",
                    },
                },
            },
        ],
        "inboundNatRules": [
            {
                "id": f"{_LB_ID}/inboundNatRules/my-rdp-rule",
                "name": "my-rdp-rule",
                "properties": {
                    "protocol": "Tcp",
                    "frontendPort": 3389,
                    "backendPort": 3389,
                },
            },
        ],
    },
}
