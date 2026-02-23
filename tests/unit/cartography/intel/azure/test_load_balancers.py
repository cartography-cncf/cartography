from cartography.intel.azure.load_balancers import transform_backend_pools
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


def test_transform_backend_pools_ignores_missing_ip_config_id() -> None:
    load_balancer = {
        "backend_address_pools": [
            {
                "id": "pool-1",
                "name": "backend-1",
                "backend_ip_configurations": [
                    {"name": "missing-id"},
                    {"id": None},
                ],
            },
        ],
    }

    assert transform_backend_pools(load_balancer) == [
        {"id": "pool-1", "name": "backend-1", "NIC_IDS": []},
    ]
