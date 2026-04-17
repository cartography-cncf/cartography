from cartography.intel.azure.firewall import transform_firewall_policies
from cartography.intel.azure.firewall import transform_firewalls
from cartography.intel.azure.firewall import transform_ip_configurations


def test_transform_firewalls():
    """Test that firewall transformation extracts all required fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "name": "fw1",
            "location": "eastus",
            "type": "Microsoft.Network/azureFirewalls",
            "provisioning_state": "Succeeded",
            "threat_intel_mode": "Alert",
            "sku": {
                "name": "AZFW_VNet",
                "tier": "Premium",
            },
            "firewall_policy": {
                "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1",
            },
            "ip_configurations": [
                {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1",
                    "name": "ipconfig1",
                    "subnet": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallSubnet",
                    },
                },
            ],
        },
    ]

    result = transform_firewalls(raw_data)

    assert len(result) == 1
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1"
    )
    assert result[0]["name"] == "fw1"
    assert result[0]["location"] == "eastus"
    assert result[0]["sku_name"] == "AZFW_VNet"
    assert result[0]["sku_tier"] == "Premium"
    assert result[0]["threat_intel_mode"] == "Alert"
    assert result[0]["provisioning_state"] == "Succeeded"
    assert (
        result[0]["firewall_policy_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1"
    )
    assert (
        result[0]["vnet_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1"
    )
    assert result[0]["ip_configuration_count"] == 1


def test_transform_firewalls_handles_missing_optional_fields():
    """Test that firewall transformation handles missing optional fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "name": "fw1",
            "location": "eastus",
        },
    ]

    result = transform_firewalls(raw_data)

    assert len(result) == 1
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1"
    )
    assert result[0]["name"] == "fw1"
    assert result[0]["sku_name"] is None
    assert result[0]["firewall_policy_id"] is None
    assert result[0]["vnet_id"] is None


def test_transform_firewall_policies():
    """Test that firewall policy transformation extracts all required fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1",
            "name": "policy1",
            "location": "eastus",
            "type": "Microsoft.Network/firewallPolicies",
            "provisioning_state": "Succeeded",
            "threat_intel_mode": "Alert",
            "sku": {
                "tier": "Premium",
            },
            "base_policy": {
                "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/parent-policy",
            },
            "dns_settings": {
                "enable_proxy": True,
                "servers": ["8.8.8.8", "8.8.4.4"],
            },
        },
    ]

    result = transform_firewall_policies(raw_data)

    assert len(result) == 1
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1"
    )
    assert result[0]["name"] == "policy1"
    assert result[0]["location"] == "eastus"
    assert result[0]["sku_tier"] == "Premium"
    assert result[0]["threat_intel_mode"] == "Alert"
    assert result[0]["provisioning_state"] == "Succeeded"
    assert (
        result[0]["base_policy_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/parent-policy"
    )
    assert result[0]["dns_enable_proxy"] is True
    assert result[0]["dns_servers"] is not None


def test_transform_firewall_policies_handles_missing_optional_fields():
    """Test that firewall policy transformation handles missing optional fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1",
            "name": "policy1",
            "location": "eastus",
        },
    ]

    result = transform_firewall_policies(raw_data)

    assert len(result) == 1
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/firewallPolicies/policy1"
    )
    assert result[0]["name"] == "policy1"
    assert result[0]["sku_tier"] is None
    assert result[0]["base_policy_id"] is None
    assert result[0]["dns_enable_proxy"] is None


def test_transform_ip_configurations():
    """Test that IP configuration transformation extracts all required fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "ip_configurations": [
                {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1",
                    "name": "ipconfig1",
                    "private_ip_address": "10.0.1.4",
                    "private_ip_allocation_method": "Dynamic",
                    "provisioning_state": "Succeeded",
                    "subnet": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallSubnet",
                    },
                    "public_ip_address": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/pip1",
                    },
                },
                {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig2",
                    "name": "ipconfig2",
                    "private_ip_address": "10.0.1.5",
                    "subnet": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallSubnet",
                    },
                    "public_ip_address": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/pip2",
                    },
                },
            ],
        },
    ]

    result = transform_ip_configurations(raw_data)

    assert len(result) == 2

    # Check first IP configuration
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1"
    )
    assert result[0]["name"] == "ipconfig1"
    assert result[0]["private_ip_address"] == "10.0.1.4"
    assert result[0]["private_ip_allocation_method"] == "Dynamic"
    assert result[0]["provisioning_state"] == "Succeeded"
    assert (
        result[0]["subnet_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallSubnet"
    )
    assert (
        result[0]["public_ip_address_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/pip1"
    )
    assert (
        result[0]["firewall_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1"
    )

    # Check second IP configuration
    assert (
        result[1]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig2"
    )
    assert result[1]["name"] == "ipconfig2"
    assert result[1]["private_ip_address"] == "10.0.1.5"


def test_transform_ip_configurations_includes_management_ip():
    """Test that management IP configuration is included in the transformation"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "ip_configurations": [
                {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1",
                    "name": "ipconfig1",
                    "private_ip_address": "10.0.1.4",
                    "subnet": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallSubnet",
                    },
                    "public_ip_address": {
                        "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/pip1",
                    },
                },
            ],
            "management_ip_configuration": {
                "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/mgmt-ipconfig",
                "name": "mgmt-ipconfig",
                "private_ip_address": "10.0.1.10",
                "subnet": {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallManagementSubnet",
                },
                "public_ip_address": {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/mgmt-pip",
                },
            },
        },
    ]

    result = transform_ip_configurations(raw_data)

    assert len(result) == 2

    # Check that management IP is included
    mgmt_ips = [ip for ip in result if ip["name"] == "mgmt-ipconfig"]
    assert len(mgmt_ips) == 1
    assert mgmt_ips[0]["private_ip_address"] == "10.0.1.10"
    assert (
        mgmt_ips[0]["subnet_id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/AzureFirewallManagementSubnet"
    )


def test_transform_ip_configurations_handles_missing_optional_fields():
    """Test that IP configuration transformation handles missing optional fields"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "ip_configurations": [
                {
                    "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1",
                    "name": "ipconfig1",
                },
            ],
        },
    ]

    result = transform_ip_configurations(raw_data)

    assert len(result) == 1
    assert (
        result[0]["id"]
        == "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1/azureFirewallIpConfigurations/ipconfig1"
    )
    assert result[0]["name"] == "ipconfig1"
    assert result[0]["private_ip_address"] is None
    assert result[0]["subnet_id"] is None
    assert result[0]["public_ip_address_id"] is None


def test_transform_ip_configurations_empty_list():
    """Test that transformation handles firewalls with no IP configurations"""
    raw_data = [
        {
            "id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Network/azureFirewalls/fw1",
            "ip_configurations": [],
        },
    ]

    result = transform_ip_configurations(raw_data)

    assert len(result) == 0
