MOCK_NAMESPACES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns",
        "name": "my-test-ns",
        "location": "eastus",
        "sku": {
            "name": "Standard",
            "tier": "Standard",
        },
        "properties": {
            "provisioning_state": "Succeeded",
            "is_auto_inflate_enabled": False,
            "maximum_throughput_units": 0,
        },
    },
]

MOCK_EVENT_HUBS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns/eventhubs/my-test-eh",
        "name": "my-test-eh",
        "properties": {
            "status": "Active",
            "partition_count": 2,
            "message_retention_in_days": 1,
        },
    },
]
