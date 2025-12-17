from cartography.intel.azure.network import transform_public_ip_addresses


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
