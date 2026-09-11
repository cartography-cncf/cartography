# Payloads in the shape azure-mgmt-eventhub 12.0.0 hybrid models return from
# `as_dict()`: the ARM wire format, with resource-specific fields under
# `properties` in camelCase.
MOCK_NAMESPACES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns",
        "name": "my-test-ns",
        "type": "Microsoft.EventHub/Namespaces",
        "location": "eastus",
        "sku": {
            "name": "Standard",
            "tier": "Standard",
            "capacity": 1,
        },
        "properties": {
            "provisioningState": "Succeeded",
            "isAutoInflateEnabled": True,
            "maximumThroughputUnits": 10,
            "serviceBusEndpoint": "https://my-test-ns.servicebus.windows.net:443/",
        },
    },
]

MOCK_EVENT_HUBS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns/eventhubs/my-test-eh",
        "name": "my-test-eh",
        "type": "Microsoft.EventHub/Namespaces/EventHubs",
        "properties": {
            "status": "Active",
            "partitionCount": 4,
            "messageRetentionInDays": 7,
        },
    },
]
