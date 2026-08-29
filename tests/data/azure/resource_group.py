# Mirrors as_attribute_dict() output (snake_case keys), not the camelCase keys that
# as_dict() returns on azure-mgmt-resource 26.x hybrid models.
MOCK_RESOURCE_GROUPS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
        "name": "TestRG1",
        "location": "eastus",
        "properties": {
            "provisioning_state": "Succeeded",
        },
        "tags": {"env": "prod", "service": "resource-group"},
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG2",
        "name": "TestRG2",
        "location": "westus2",
        "properties": {
            "provisioning_state": "Succeeded",
        },
        "tags": {"env": "prod", "service": "resource-group"},
    },
]
