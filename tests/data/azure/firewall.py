"""
Test data for Azure Firewalls and Firewall Policies
Matches real Azure API structure (flat, not nested under properties)
"""

# Mock Azure Firewall data - matches actual azure-mgmt-network SDK output
DESCRIBE_FIREWALLS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1",
        "name": "test-firewall-1",
        "type": "Microsoft.Network/azureFirewalls",
        "location": "eastus",
        "etag": 'W/"00000000-0000-0000-0000-000000000000"',
        "zones": ["1", "2", "3"],
        "tags": {
            "environment": "production",
            "team": "security",
        },
        # Real API returns flat structure, not nested under "properties"
        "provisioning_state": "Succeeded",
        "threat_intel_mode": "Alert",
        "sku": {
            "name": "AZFW_VNet",
            "tier": "Premium",
        },
        "firewall_policy": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        },
        "ip_configurations": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig1",
                "name": "ipconfig1",
                "private_ip_address": "10.0.1.4",
                "private_ip_allocation_method": "Dynamic",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
                "etag": 'W/"11111111-1111-1111-1111-111111111111"',
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
                },
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-1",
                },
            },
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/ipconfig2",
                "name": "ipconfig2",
                "private_ip_address": "10.0.1.5",
                "private_ip_allocation_method": "Dynamic",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
                "etag": 'W/"22222222-2222-2222-2222-222222222222"',
                "subnet": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
                },
                "public_ip_address": {
                    "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-pip-2",
                },
            },
        ],
        "management_ip_configuration": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/azureFirewallIpConfigurations/mgmt-ipconfig",
            "name": "mgmt-ipconfig",
            "private_ip_address": "10.0.1.10",
            "private_ip_allocation_method": "Dynamic",
            "provisioning_state": "Succeeded",
            "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
            "etag": 'W/"33333333-3333-3333-3333-333333333333"',
            "subnet": {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/AzureFirewallManagementSubnet",
            },
            "public_ip_address": {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/fw-mgmt-pip",
            },
        },
        "network_rule_collections": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/networkRuleCollections/allow-ssh",
                "name": "allow-ssh",
                "priority": 100,
                "action": {"type": "Allow"},
                "rules": [
                    {
                        "name": "allow-ssh-from-trusted",
                        "description": "Allow SSH from trusted networks",
                        "protocols": ["TCP"],
                        "source_addresses": ["10.0.0.0/8"],
                        "destination_addresses": ["*"],
                        "destination_ports": ["22"],
                    },
                ],
            },
        ],
        "application_rule_collections": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/applicationRuleCollections/allow-web",
                "name": "allow-web",
                "priority": 200,
                "action": {"type": "Allow"},
                "rules": [
                    {
                        "name": "allow-https",
                        "description": "Allow HTTPS traffic",
                        "source_addresses": ["*"],
                        "protocols": [{"protocol_type": "Https", "port": 443}],
                        "target_fqdns": ["*.microsoft.com", "*.azure.com"],
                    },
                ],
            },
        ],
        "nat_rule_collections": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-1/natRuleCollections/dnat-web",
                "name": "dnat-web",
                "priority": 300,
                "action": {"type": "Dnat"},
                "rules": [
                    {
                        "name": "web-dnat",
                        "description": "DNAT for web server",
                        "protocols": ["TCP"],
                        "source_addresses": ["*"],
                        "destination_addresses": ["20.1.2.3"],
                        "destination_ports": ["80", "443"],
                        "translated_address": "10.0.2.10",
                        "translated_port": "80",
                    },
                ],
            },
        ],
        "additional_properties": {},
        "ip_groups": [],
        "autoscale_configuration": {
            "min_capacity": 2,
            "max_capacity": 10,
        },
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/azureFirewalls/test-firewall-2",
        "name": "test-firewall-2",
        "type": "Microsoft.Network/azureFirewalls",
        "location": "westus",
        "provisioning_state": "Succeeded",
        "threat_intel_mode": "Deny",
        "sku": {
            "name": "AZFW_Hub",
            "tier": "Standard",
        },
        "firewall_policy": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
        },
        "virtual_hub": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualHubs/test-vhub",
        },
        "hub_ip_addresses": {
            "private_ip_address": "10.1.0.4",
            "public_ip_addresses": [
                {"address": "40.1.2.3"},
                {"address": "40.1.2.4"},
            ],
        },
        "network_rule_collections": [],
        "application_rule_collections": [],
        "nat_rule_collections": [],
        "additional_properties": {},
    },
]

# Mock Azure Firewall Policy data - matches real API structure (flat)
DESCRIBE_FIREWALL_POLICIES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        "name": "test-policy-1",
        "type": "Microsoft.Network/firewallPolicies",
        "location": "eastus",
        "etag": 'W/"00000000-0000-0000-0000-000000000000"',
        "tags": {
            "environment": "production",
        },
        # Real API returns flat structure
        "provisioning_state": "Succeeded",
        "threat_intel_mode": "Alert",
        "size": "1.5MB",
        "sku": {
            "tier": "Premium",
        },
        "dns_settings": {
            "servers": ["8.8.8.8", "1.1.1.1"],
            "enable_proxy": True,
            "require_proxy_for_network_rules": False,
        },
        "sql": {
            "allow_sql_redirect": True,
        },
        "snat": {
            "private_ranges": ["10.0.0.0/8", "172.16.0.0/12"],
            "auto_learn_private_ranges": "Enabled",
        },
        "explicit_proxy": {
            "enable_explicit_proxy": True,
            "http_port": 8080,
            "https_port": 8443,
            "enable_pac_file": False,
        },
        "intrusion_detection": {
            "mode": "Alert",
            "profile": "Advanced",
            "configuration": {
                "signature_overrides": [
                    {
                        "id": "2525004",
                        "mode": "Deny",
                    },
                ],
                "bypass_traffic_settings": [
                    {
                        "name": "bypass-internal",
                        "description": "Bypass IDS for internal traffic",
                        "protocol": "Any",
                        "source_addresses": ["10.0.0.0/8"],
                        "destination_addresses": ["10.0.0.0/8"],
                        "destination_ports": ["*"],
                    },
                ],
                "private_ranges": ["192.168.0.0/16"],
            },
        },
        "insights": {
            "is_enabled": True,
            "retention_days": 90,
        },
        "transport_security": {
            "certificate_authority": {
                "name": "root-ca",
                "key_vault_secret_id": "https://myvault.vault.azure.net/secrets/root-ca",
            },
        },
        "threat_intel_whitelist": {
            "ip_addresses": ["20.3.4.5", "30.4.5.6"],
            "fqdns": ["trusted.example.com", "*.safe-domain.com"],
        },
        "rule_collection_groups": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1/ruleCollectionGroups/default-rules",
            },
        ],
        "firewalls": [],
        "child_policies": [],
    },
    {
        # Real API returns flat structure, not nested under 'properties'
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-2",
        "name": "test-policy-2",
        "type": "Microsoft.Network/firewallPolicies",
        "location": "westus",
        "provisioning_state": "Succeeded",
        "threat_intel_mode": "Deny",
        "sku": {
            "tier": "Standard",
        },
        "base_policy": {
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/firewallPolicies/test-policy-1",
        },
        "rule_collection_groups": [],
        "firewalls": [],
    },
]

_RG = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network"
_FW1 = f"{_RG}/azureFirewalls/test-firewall-1"

# The same firewalls and policies as ARM response bodies, which is what
# azure-mgmt-network 31+ hands back from as_dict(): camelCase keys nested under
# "properties". The firewall IP configuration has no allocation method on the wire.
DESCRIBE_FIREWALLS_ARM = [
    {
        "id": _FW1,
        "name": "test-firewall-1",
        "type": "Microsoft.Network/azureFirewalls",
        "location": "eastus",
        "etag": 'W/"00000000-0000-0000-0000-000000000000"',
        "zones": ["1", "2", "3"],
        "tags": {"environment": "production", "team": "security"},
        "properties": {
            "provisioningState": "Succeeded",
            "threatIntelMode": "Alert",
            "sku": {"name": "AZFW_VNet", "tier": "Premium"},
            "firewallPolicy": {"id": f"{_RG}/firewallPolicies/test-policy-1"},
            "ipConfigurations": [
                {
                    "id": f"{_FW1}/azureFirewallIpConfigurations/ipconfig1",
                    "name": "ipconfig1",
                    "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
                    "etag": 'W/"11111111-1111-1111-1111-111111111111"',
                    "properties": {
                        "privateIPAddress": "10.0.1.4",
                        "provisioningState": "Succeeded",
                        "subnet": {
                            "id": f"{_RG}/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
                        },
                        "publicIPAddress": {"id": f"{_RG}/publicIPAddresses/fw-pip-1"},
                    },
                },
                {
                    "id": f"{_FW1}/azureFirewallIpConfigurations/ipconfig2",
                    "name": "ipconfig2",
                    "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
                    "etag": 'W/"22222222-2222-2222-2222-222222222222"',
                    "properties": {
                        "privateIPAddress": "10.0.1.5",
                        "provisioningState": "Succeeded",
                        "subnet": {
                            "id": f"{_RG}/virtualNetworks/test-vnet/subnets/AzureFirewallSubnet",
                        },
                        "publicIPAddress": {"id": f"{_RG}/publicIPAddresses/fw-pip-2"},
                    },
                },
            ],
            "managementIpConfiguration": {
                "id": f"{_FW1}/azureFirewallIpConfigurations/mgmt-ipconfig",
                "name": "mgmt-ipconfig",
                "type": "Microsoft.Network/azureFirewalls/azureFirewallIpConfigurations",
                "etag": 'W/"33333333-3333-3333-3333-333333333333"',
                "properties": {
                    "privateIPAddress": "10.0.1.10",
                    "provisioningState": "Succeeded",
                    "subnet": {
                        "id": f"{_RG}/virtualNetworks/test-vnet/subnets/AzureFirewallManagementSubnet",
                    },
                    "publicIPAddress": {"id": f"{_RG}/publicIPAddresses/fw-mgmt-pip"},
                },
            },
            "networkRuleCollections": [
                {
                    "id": f"{_FW1}/networkRuleCollections/allow-ssh",
                    "name": "allow-ssh",
                    "properties": {
                        "priority": 100,
                        "action": {"type": "Allow"},
                        "rules": [
                            {
                                "name": "allow-ssh-from-trusted",
                                "description": "Allow SSH from trusted networks",
                                "protocols": ["TCP"],
                                "sourceAddresses": ["10.0.0.0/8"],
                                "destinationAddresses": ["*"],
                                "destinationPorts": ["22"],
                            },
                        ],
                    },
                },
            ],
            "applicationRuleCollections": [
                {
                    "id": f"{_FW1}/applicationRuleCollections/allow-web",
                    "name": "allow-web",
                    "properties": {
                        "priority": 200,
                        "action": {"type": "Allow"},
                        "rules": [
                            {
                                "name": "allow-https",
                                "description": "Allow HTTPS traffic",
                                "sourceAddresses": ["*"],
                                "protocols": [{"protocolType": "Https", "port": 443}],
                                "targetFqdns": ["*.microsoft.com", "*.azure.com"],
                            },
                        ],
                    },
                },
            ],
            "natRuleCollections": [
                {
                    "id": f"{_FW1}/natRuleCollections/dnat-web",
                    "name": "dnat-web",
                    "properties": {
                        "priority": 300,
                        "action": {"type": "Dnat"},
                        "rules": [
                            {
                                "name": "web-dnat",
                                "description": "DNAT for web server",
                                "protocols": ["TCP"],
                                "sourceAddresses": ["*"],
                                "destinationAddresses": ["20.1.2.3"],
                                "destinationPorts": ["80", "443"],
                                "translatedAddress": "10.0.2.10",
                                "translatedPort": "80",
                            },
                        ],
                    },
                },
            ],
            "additionalProperties": {},
            "ipGroups": [],
            "autoscaleConfiguration": {"minCapacity": 2, "maxCapacity": 10},
        },
    },
    {
        "id": f"{_RG}/azureFirewalls/test-firewall-2",
        "name": "test-firewall-2",
        "type": "Microsoft.Network/azureFirewalls",
        "location": "westus",
        "properties": {
            "provisioningState": "Succeeded",
            "threatIntelMode": "Deny",
            "sku": {"name": "AZFW_Hub", "tier": "Standard"},
            "firewallPolicy": {"id": f"{_RG}/firewallPolicies/test-policy-2"},
            "virtualHub": {"id": f"{_RG}/virtualHubs/test-vhub"},
            "hubIPAddresses": {
                "privateIPAddress": "10.1.0.4",
                "publicIPs": {
                    "addresses": [{"address": "40.1.2.3"}, {"address": "40.1.2.4"}],
                    "count": 2,
                },
            },
            "networkRuleCollections": [],
            "applicationRuleCollections": [],
            "natRuleCollections": [],
            "additionalProperties": {},
        },
    },
]

DESCRIBE_FIREWALL_POLICIES_ARM = [
    {
        "id": f"{_RG}/firewallPolicies/test-policy-1",
        "name": "test-policy-1",
        "type": "Microsoft.Network/firewallPolicies",
        "location": "eastus",
        "etag": 'W/"00000000-0000-0000-0000-000000000000"',
        "tags": {"environment": "production"},
        "properties": {
            "provisioningState": "Succeeded",
            "threatIntelMode": "Alert",
            "size": "1.5MB",
            "sku": {"tier": "Premium"},
            "dnsSettings": {
                "servers": ["8.8.8.8", "1.1.1.1"],
                "enableProxy": True,
                "requireProxyForNetworkRules": False,
            },
            "sql": {"allowSqlRedirect": True},
            "snat": {
                "privateRanges": ["10.0.0.0/8", "172.16.0.0/12"],
                "autoLearnPrivateRanges": "Enabled",
            },
            "explicitProxy": {
                "enableExplicitProxy": True,
                "httpPort": 8080,
                "httpsPort": 8443,
                "enablePacFile": False,
            },
            "intrusionDetection": {
                "mode": "Alert",
                "profile": "Advanced",
                "configuration": {
                    "signatureOverrides": [{"id": "2525004", "mode": "Deny"}],
                    "bypassTrafficSettings": [
                        {
                            "name": "bypass-internal",
                            "description": "Bypass IDS for internal traffic",
                            "protocol": "Any",
                            "sourceAddresses": ["10.0.0.0/8"],
                            "destinationAddresses": ["10.0.0.0/8"],
                            "destinationPorts": ["*"],
                        },
                    ],
                    "privateRanges": ["192.168.0.0/16"],
                },
            },
            "insights": {"isEnabled": True, "retentionDays": 90},
            "transportSecurity": {
                "certificateAuthority": {
                    "name": "root-ca",
                    "keyVaultSecretId": "https://myvault.vault.azure.net/secrets/root-ca",
                },
            },
            "threatIntelWhitelist": {
                "ipAddresses": ["20.3.4.5", "30.4.5.6"],
                "fqdns": ["trusted.example.com", "*.safe-domain.com"],
            },
            "ruleCollectionGroups": [
                {
                    "id": f"{_RG}/firewallPolicies/test-policy-1/ruleCollectionGroups/default-rules"
                },
            ],
            "firewalls": [],
            "childPolicies": [],
        },
    },
    {
        "id": f"{_RG}/firewallPolicies/test-policy-2",
        "name": "test-policy-2",
        "type": "Microsoft.Network/firewallPolicies",
        "location": "westus",
        "properties": {
            "provisioningState": "Succeeded",
            "threatIntelMode": "Deny",
            "sku": {"tier": "Standard"},
            "basePolicy": {"id": f"{_RG}/firewallPolicies/test-policy-1"},
            "ruleCollectionGroups": [],
            "firewalls": [],
        },
    },
]
