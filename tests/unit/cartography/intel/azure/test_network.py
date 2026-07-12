from cartography.intel.azure.network import transform_network_interfaces
from cartography.intel.azure.network import transform_network_security_rules
from cartography.intel.azure.network import transform_public_ip_addresses
from cartography.intel.azure.network import transform_subnets
from cartography.intel.azure.network import transform_virtual_networks


def test_transform_public_ip_addresses_handles_flattened_fields():
    data = transform_public_ip_addresses(
        [
            {
                "id": "public-ip-1",
                "name": "my-public-ip-1",
                "location": "eastus",
                "ip_address": "20.10.30.40",
                "public_ip_allocation_method": "Static",
            },
        ],
    )

    assert data == [
        {
            "id": "public-ip-1",
            "name": "my-public-ip-1",
            "location": "eastus",
            "ip_address": "20.10.30.40",
            "public_ip_allocation_method": "Static",
        },
    ]


def test_transform_public_ip_addresses_handles_nested_properties_fields():
    data = transform_public_ip_addresses(
        [
            {
                "id": "public-ip-1",
                "name": "my-public-ip-1",
                "location": "eastus",
                "properties": {
                    "ip_address": "20.10.30.40",
                    "public_ip_allocation_method": "Static",
                },
            },
        ],
    )

    assert data == [
        {
            "id": "public-ip-1",
            "name": "my-public-ip-1",
            "location": "eastus",
            "ip_address": "20.10.30.40",
            "public_ip_allocation_method": "Static",
        },
    ]


def test_transform_network_resources_handles_sdk_31_camel_properties():
    vnets = transform_virtual_networks(
        [
            {
                "id": "vnet-id",
                "name": "vnet",
                "location": "eastus",
                "properties": {"provisioningState": "Succeeded"},
            }
        ]
    )
    subnets = transform_subnets(
        [
            {
                "id": "subnet-id",
                "name": "subnet",
                "properties": {
                    "addressPrefix": "10.0.0.0/24",
                    "networkSecurityGroup": {"id": "nsg-id"},
                },
            }
        ]
    )
    public_ips = transform_public_ip_addresses(
        [
            {
                "id": "public-ip-1",
                "name": "my-public-ip-1",
                "location": "eastus",
                "properties": {
                    "ipAddress": "20.10.30.40",
                    "publicIPAllocationMethod": "Static",
                },
            },
        ],
    )

    assert vnets[0]["provisioning_state"] == "Succeeded"
    assert subnets[0]["address_prefix"] == "10.0.0.0/24"
    assert subnets[0]["nsg_id"] == "nsg-id"
    assert public_ips[0]["ip_address"] == "20.10.30.40"
    assert public_ips[0]["public_ip_allocation_method"] == "Static"


def test_transform_network_security_rules_handles_sdk_31_camel_properties():
    rules = transform_network_security_rules(
        [
            {
                "id": "nsg-id",
                "properties": {
                    "securityRules": [
                        {
                            "id": "rule-id",
                            "name": "allow-https",
                            "properties": {
                                "protocol": "Tcp",
                                "direction": "Inbound",
                                "access": "Allow",
                                "priority": 100,
                                "sourcePortRange": "*",
                                "destinationPortRange": "443",
                                "sourceAddressPrefix": "*",
                                "destinationAddressPrefix": "*",
                            },
                        }
                    ],
                    "defaultSecurityRules": [],
                },
            }
        ]
    )

    assert rules == [
        {
            "id": "rule-id",
            "name": "allow-https",
            "nsg_id": "nsg-id",
            "description": None,
            "protocol": "Tcp",
            "direction": "Inbound",
            "access": "Allow",
            "priority": 100,
            "source_port_range": "*",
            "source_port_ranges": None,
            "destination_port_range": "443",
            "destination_port_ranges": None,
            "source_address_prefix": "*",
            "source_address_prefixes": None,
            "destination_address_prefix": "*",
            "destination_address_prefixes": None,
            "is_default": False,
        }
    ]


def test_transform_network_interfaces_handles_sdk_31_camel_properties():
    interfaces = transform_network_interfaces(
        [
            {
                "id": "nic-id",
                "name": "nic",
                "location": "eastus",
                "properties": {
                    "ipConfigurations": [
                        {
                            "properties": {
                                "subnet": {"id": "subnet-id"},
                                "publicIPAddress": {"id": "public-ip-id"},
                                "privateIPAddress": "10.0.0.4",
                            },
                        }
                    ],
                    "networkSecurityGroup": {"id": "nsg-id"},
                    "virtualMachine": {"id": "VM-ID"},
                },
            }
        ]
    )

    assert interfaces[0]["SUBNET_IDS"] == ["subnet-id"]
    assert interfaces[0]["PUBLIC_IP_IDS"] == ["public-ip-id"]
    assert interfaces[0]["private_ip_addresses"] == ["10.0.0.4"]
    assert interfaces[0]["NSG_ID"] == "nsg-id"
    assert interfaces[0]["VIRTUAL_MACHINE_ID"] == "vm-id"
