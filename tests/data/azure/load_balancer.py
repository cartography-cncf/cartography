MOCK_LOAD_BALANCERS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb",
        "name": "my-test-lb",
        "location": "eastus",
        "sku": {"name": "Standard"},
        "frontend_ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/frontendIPConfigurations/my-lb-frontend",
                "name": "my-lb-frontend",
                "properties": {
                    "private_ip_address": "10.0.0.4",
                    "public_ip_address": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-public-ip"
                    },
                },
            },
        ],
        "backend_address_pools": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/backendAddressPools/my-lb-backend-pool",
                "name": "my-lb-backend-pool",
                "properties": {},
            },
        ],
        "load_balancing_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/loadBalancers/my-test-lb/loadBalancingRules/my-http-rule",
                "name": "my-http-rule",
                "properties": {
                    "protocol": "Tcp",
                    "frontend_port": 80,
                    "backend_port": 80,
                },
                # These objects are at the top level in the real API response
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
                "properties": {
                    "protocol": "Tcp",
                    "frontend_port": 3389,
                    "backend_port": 3389,
                },
            },
        ],
    },
]
