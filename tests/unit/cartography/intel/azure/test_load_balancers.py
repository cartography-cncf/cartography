from cartography.intel.azure.load_balancers import transform_frontend_ips


def test_transform_frontend_ips_extracts_nested_public_ip_id() -> None:
    load_balancer = {
        "frontend_ip_configurations": [
            {
                "id": "fip-1",
                "name": "frontend-1",
                "properties": {
                    "private_ip_address": "10.0.0.5",
                    "public_ip_address": {"id": "pip-1"},
                },
            },
        ],
    }

    assert transform_frontend_ips(load_balancer) == [
        {
            "id": "fip-1",
            "name": "frontend-1",
            "private_ip_address": "10.0.0.5",
            "public_ip_address_id": "pip-1",
        },
    ]
