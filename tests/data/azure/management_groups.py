TEST_TENANT_ID = "11111111-2222-3333-4444-555555555555"
TEST_SUBSCRIPTION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

TEST_ROOT_MANAGEMENT_GROUP_ID = (
    f"/providers/Microsoft.Management/managementGroups/{TEST_TENANT_ID}"
)
TEST_PARENT_MANAGEMENT_GROUP_NAME = "test-management-group"
TEST_PARENT_MANAGEMENT_GROUP_ID = (
    "/providers/Microsoft.Management/managementGroups/test-management-group"
)
TEST_CHILD_MANAGEMENT_GROUP_NAME = "test-child-mgmt-group"
TEST_CHILD_MANAGEMENT_GROUP_ID = (
    "/providers/Microsoft.Management/managementGroups/test-child-mgmt-group"
)


# Simulates the expanded payload returned by:
# az account management-group show --name test-management-group --expand --recurse
EXPANDED_PARENT_MANAGEMENT_GROUP = {
    "children": [
        {
            "children": [
                {
                    "children": None,
                    "displayName": "Test Subscription",
                    "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
                    "name": TEST_SUBSCRIPTION_ID,
                    "type": "/subscriptions",
                },
            ],
            "displayName": "test-child-mgmt-group",
            "id": TEST_CHILD_MANAGEMENT_GROUP_ID,
            "name": TEST_CHILD_MANAGEMENT_GROUP_NAME,
            "type": "Microsoft.Management/managementGroups",
        },
    ],
    "details": {
        "managementGroupAncestors": None,
        "managementGroupAncestorsChain": None,
        "parent": {
            "displayName": "Tenant Root Group",
            "id": TEST_ROOT_MANAGEMENT_GROUP_ID,
            "name": TEST_TENANT_ID,
        },
        "path": None,
        "updatedBy": "00000000-1111-2222-3333-444444444444",
        "updatedTime": "2026-05-27T00:00:00.000000+00:00",
        "version": 0,
    },
    "displayName": "test-management-group",
    "id": TEST_PARENT_MANAGEMENT_GROUP_ID,
    "name": TEST_PARENT_MANAGEMENT_GROUP_NAME,
    "tenantId": TEST_TENANT_ID,
    "type": "Microsoft.Management/managementGroups",
}


# Simulates the expanded payload returned by:
# az account management-group show --name test-child-mgmt-group --expand --recurse
EXPANDED_CHILD_MANAGEMENT_GROUP = {
    "children": [
        {
            "children": None,
            "displayName": "Test Subscription",
            "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "name": TEST_SUBSCRIPTION_ID,
            "type": "/subscriptions",
        },
    ],
    "details": {
        "managementGroupAncestors": None,
        "managementGroupAncestorsChain": None,
        "parent": {
            "displayName": "test-management-group",
            "id": TEST_PARENT_MANAGEMENT_GROUP_ID,
            "name": TEST_PARENT_MANAGEMENT_GROUP_NAME,
        },
        "path": None,
        "updatedBy": "00000000-1111-2222-3333-444444444444",
        "updatedTime": "2026-05-27T00:05:00.000000+00:00",
        "version": 0,
    },
    "displayName": "test-child-mgmt-group",
    "id": TEST_CHILD_MANAGEMENT_GROUP_ID,
    "name": TEST_CHILD_MANAGEMENT_GROUP_NAME,
    "tenantId": TEST_TENANT_ID,
    "type": "Microsoft.Management/managementGroups",
}


# Simulates the list[dict] returned by get_azure_management_groups() after the
# per-group expanded fetches succeed.
AZURE_MANAGEMENT_GROUPS = [
    EXPANDED_PARENT_MANAGEMENT_GROUP,
    EXPANDED_CHILD_MANAGEMENT_GROUP,
]


UPDATED_EXPANDED_PARENT_MANAGEMENT_GROUP = {
    "children": [],
    "details": {
        "managementGroupAncestors": None,
        "managementGroupAncestorsChain": None,
        "parent": {
            "displayName": "Tenant Root Group",
            "id": TEST_ROOT_MANAGEMENT_GROUP_ID,
            "name": TEST_TENANT_ID,
        },
        "path": None,
        "updatedBy": "00000000-1111-2222-3333-444444444444",
        "updatedTime": "2026-05-27T01:00:00.000000+00:00",
        "version": 1,
    },
    "displayName": "test-management-group",
    "id": TEST_PARENT_MANAGEMENT_GROUP_ID,
    "name": TEST_PARENT_MANAGEMENT_GROUP_NAME,
    "tenantId": TEST_TENANT_ID,
    "type": "Microsoft.Management/managementGroups",
}


UPDATED_AZURE_MANAGEMENT_GROUPS = [
    UPDATED_EXPANDED_PARENT_MANAGEMENT_GROUP,
]


# Simulates the dedicated management-group subscriptions endpoint payload:
# GET /providers/Microsoft.Management/managementGroups/{groupId}/subscriptions
AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS = [
    {
        "id": (
            f"{TEST_CHILD_MANAGEMENT_GROUP_ID}/subscriptions/{TEST_SUBSCRIPTION_ID}"
        ),
        "name": TEST_SUBSCRIPTION_ID,
        "displayName": "Test Subscription",
        "parent": {
            "id": TEST_CHILD_MANAGEMENT_GROUP_ID,
        },
        "state": "Active",
        "tenant": TEST_TENANT_ID,
        "type": "Microsoft.Management/managementGroups/subscriptions",
        "properties": {
            "parent": {
                "id": TEST_CHILD_MANAGEMENT_GROUP_ID,
            },
        },
    },
]


UPDATED_AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS: list[dict] = []
