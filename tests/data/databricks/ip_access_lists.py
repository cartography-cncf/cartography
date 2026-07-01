DATABRICKS_IP_ACCESS_LISTS = [
    {
        "list_id": "0303-iplist-aaaa",
        "label": "office",
        "list_type": "ALLOW",
        "enabled": True,
        "address_count": 2,
        "ip_addresses": ["198.51.100.0/24", "203.0.113.42"],
        "created_at": 1700000500000,
        "updated_at": 1700000600000,
    },
    {
        "list_id": "0303-iplist-bbbb",
        "label": "blocked-ranges",
        "list_type": "BLOCK",
        "enabled": False,
        "address_count": 1,
        "ip_addresses": ["10.0.0.0/8"],
        "created_at": 1700000700000,
        "updated_at": 1700000700000,
    },
]
