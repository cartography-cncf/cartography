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

_AGW_ID = MOCK_APPLICATION_GATEWAYS[0]["id"]

# The same gateway as an ARM response body, which is what azure-mgmt-network 31+
# hands back from as_dict(): camelCase keys nested under "properties".
MOCK_APPLICATION_GATEWAY_ARM = {
    "id": _AGW_ID,
    "name": "my-test-appgw",
    "location": "eastus",
    "tags": {"env": "prod", "service": "application-gateway"},
    "properties": {
        "sku": {"name": "WAF_v2", "tier": "WAF_v2", "capacity": 2},
        "operationalState": "Running",
        "provisioningState": "Succeeded",
        "enableHttp2": True,
        "firewallPolicy": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies/my-waf-policy",
        },
        "gatewayIPConfigurations": [
            {
                "id": f"{_AGW_ID}/gatewayIPConfigurations/my-gw-ip",
                "name": "my-gw-ip",
                "properties": {
                    "subnet": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-vnet/subnets/my-appgw-subnet",
                    },
                },
            },
        ],
        "frontendIPConfigurations": [
            {
                "id": f"{_AGW_ID}/frontendIPConfigurations/my-appgw-frontend",
                "name": "my-appgw-frontend",
                "properties": {
                    "privateIPAllocationMethod": "Dynamic",
                    "publicIPAddress": {
                        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-appgw-public-ip",
                    },
                },
            },
        ],
        "frontendPorts": [
            {
                "id": f"{_AGW_ID}/frontendPorts/port-443",
                "name": "port-443",
                "properties": {"port": 443},
            },
        ],
        "backendAddressPools": [
            {
                "id": f"{_AGW_ID}/backendAddressPools/my-appgw-backend-pool",
                "name": "my-appgw-backend-pool",
                "properties": {
                    "backendAddresses": [
                        {"fqdn": "backend.example.com"},
                        {"ipAddress": "10.0.1.4"},
                    ],
                    "backendIPConfigurations": [
                        {
                            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-appgw-nic/ipConfigurations/ipconfig1",
                        },
                    ],
                },
            },
        ],
        "backendHttpSettingsCollection": [
            {
                "id": f"{_AGW_ID}/backendHttpSettingsCollection/my-https-settings",
                "name": "my-https-settings",
                "properties": {
                    "protocol": "Https",
                    "port": 443,
                    "cookieBasedAffinity": "Disabled",
                    "requestTimeout": 30,
                    "pickHostNameFromBackendAddress": True,
                },
            },
        ],
        "httpListeners": [
            {
                "id": f"{_AGW_ID}/httpListeners/my-https-listener",
                "name": "my-https-listener",
                "properties": {
                    "protocol": "Https",
                    "hostName": "app.example.com",
                    "hostNames": ["app.example.com"],
                    "requireServerNameIndication": True,
                    "frontendIPConfiguration": {
                        "id": f"{_AGW_ID}/frontendIPConfigurations/my-appgw-frontend",
                    },
                    "frontendPort": {"id": f"{_AGW_ID}/frontendPorts/port-443"},
                    "sslCertificate": {"id": f"{_AGW_ID}/sslCertificates/my-cert"},
                },
            },
        ],
        "requestRoutingRules": [
            {
                "id": f"{_AGW_ID}/requestRoutingRules/my-routing-rule",
                "name": "my-routing-rule",
                "properties": {
                    "ruleType": "Basic",
                    "priority": 100,
                    "httpListener": {
                        "id": f"{_AGW_ID}/httpListeners/my-https-listener",
                    },
                    "backendAddressPool": {
                        "id": f"{_AGW_ID}/backendAddressPools/my-appgw-backend-pool",
                    },
                    "backendHttpSettings": {
                        "id": f"{_AGW_ID}/backendHttpSettingsCollection/my-https-settings",
                    },
                },
            },
            {
                "id": f"{_AGW_ID}/requestRoutingRules/my-path-routing-rule",
                "name": "my-path-routing-rule",
                "properties": {
                    "ruleType": "PathBasedRouting",
                    "priority": 200,
                    "httpListener": {
                        "id": f"{_AGW_ID}/httpListeners/my-https-listener",
                    },
                    "urlPathMap": {"id": f"{_AGW_ID}/urlPathMaps/my-path-map"},
                },
            },
        ],
    },
}
