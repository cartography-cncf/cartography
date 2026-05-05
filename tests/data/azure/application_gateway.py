MOCK_APPLICATION_GATEWAYS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw",
        "name": "my-test-appgw",
        "location": "eastus",
        "sku": {"name": "WAF_v2", "tier": "WAF_v2", "capacity": 2},
        "operational_state": "Running",
        "provisioning_state": "Succeeded",
        "enable_http2": True,
        "tags": {"env": "prod", "service": "application-gateway"},
        "firewall_policy": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies/my-waf-policy",
        },
        "gateway_ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/gatewayIPConfigurations/my-gw-ip",
                "name": "my-gw-ip",
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-vnet/subnets/my-appgw-subnet",
                },
            },
        ],
        "frontend_ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/frontendIPConfigurations/my-appgw-frontend",
                "name": "my-appgw-frontend",
                "private_ip_allocation_method": "Dynamic",
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-appgw-public-ip",
                },
            },
        ],
        "frontend_ports": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/frontendPorts/port-443",
                "name": "port-443",
                "port": 443,
            },
        ],
        "backend_address_pools": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendAddressPools/my-appgw-backend-pool",
                "name": "my-appgw-backend-pool",
                "backend_addresses": [
                    {"fqdn": "backend.example.com"},
                    {"ip_address": "10.0.1.4"},
                ],
                "backend_ip_configurations": [
                    {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-appgw-nic/ipConfigurations/ipconfig1",
                    },
                ],
            },
        ],
        "backend_http_settings_collection": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendHttpSettingsCollection/my-https-settings",
                "name": "my-https-settings",
                "protocol": "Https",
                "port": 443,
                "cookie_based_affinity": "Disabled",
                "request_timeout": 30,
                "pick_host_name_from_backend_address": True,
            },
        ],
        "http_listeners": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/httpListeners/my-https-listener",
                "name": "my-https-listener",
                "protocol": "Https",
                "host_name": "app.example.com",
                "host_names": ["app.example.com"],
                "require_server_name_indication": True,
                "frontend_ip_configuration": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/frontendIPConfigurations/my-appgw-frontend",
                },
                "frontend_port": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/frontendPorts/port-443",
                },
                "ssl_certificate": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/sslCertificates/my-cert",
                },
            },
        ],
        "url_path_maps": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/urlPathMaps/my-path-map",
                "name": "my-path-map",
                "default_backend_address_pool": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendAddressPools/my-appgw-backend-pool",
                },
                "default_backend_http_settings": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendHttpSettingsCollection/my-https-settings",
                },
            },
        ],
        "request_routing_rules": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/requestRoutingRules/my-routing-rule",
                "name": "my-routing-rule",
                "rule_type": "Basic",
                "priority": 100,
                "http_listener": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/httpListeners/my-https-listener",
                },
                "backend_address_pool": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendAddressPools/my-appgw-backend-pool",
                },
                "backend_http_settings": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/backendHttpSettingsCollection/my-https-settings",
                },
            },
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/requestRoutingRules/my-path-routing-rule",
                "name": "my-path-routing-rule",
                "rule_type": "PathBasedRouting",
                "priority": 200,
                "http_listener": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/httpListeners/my-https-listener",
                },
                "url_path_map": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/applicationGateways/my-test-appgw/urlPathMaps/my-path-map",
                },
            },
        ],
    },
]
