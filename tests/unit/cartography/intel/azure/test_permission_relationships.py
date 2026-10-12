import pytest

from cartography.intel.azure import permission_relationships

SUBSCRIPTION_SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000000"
STORAGE_ACCOUNT_ID = (
    f"{SUBSCRIPTION_SCOPE}/resourceGroups/rg/providers/"
    "Microsoft.Storage/storageAccounts/acct"
)
BLOB_READ = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"


def _assignment(
    actions: list[str],
    data_actions: list[str],
    not_data_actions: list[str] | None = None,
) -> dict:
    return {
        "assignment": {
            "permissions": permission_relationships.compile_permissions(
                {
                    "actions": actions,
                    "not_actions": [],
                    "data_actions": data_actions,
                    "not_data_actions": not_data_actions or [],
                },
            ),
            "scope": permission_relationships.compile_azure_regex(
                permission_relationships.resolve_azure_scope(SUBSCRIPTION_SCOPE),
            ),
            "principal_type": "User",
        },
    }


@pytest.mark.parametrize(
    ("role", "assignment", "expected"),
    [
        ("Reader", _assignment(["*/read"], []), False),
        ("Contributor", _assignment(["*"], []), False),
        ("Storage Blob Data Reader", _assignment([], [BLOB_READ]), True),
        (
            "data wildcard minus blob read",
            _assignment([], ["*"], not_data_actions=[BLOB_READ]),
            False,
        ),
    ],
)
def test_data_permissions_only_match_data_actions(role, assignment, expected):
    assert (
        permission_relationships.principal_allowed_on_resource(
            assignment,
            STORAGE_ACCOUNT_ID,
            [],
            data_permissions=[BLOB_READ],
        )
        is expected
    ), role


@pytest.mark.parametrize(
    ("rpr", "expected"),
    [
        (
            {
                "target_label": "AzureKeyVault",
                "data_permissions": [
                    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
                ],
                "relationship_name": "CAN_READ",
            },
            True,
        ),
        (
            {"target_label": "AzureKeyVault", "relationship_name": "CAN_READ"},
            False,
        ),
        (
            {
                "target_label": "AzureKeyVault",
                "data_permissions": "Microsoft.KeyVault/vaults/secrets/getSecret/action",
                "relationship_name": "CAN_READ",
            },
            False,
        ),
        (
            {
                "target_label": "AzureKeyVault",
                "data_permissions": [None],
                "relationship_name": "CAN_READ",
            },
            False,
        ),
    ],
)
def test_rpr_needs_permissions_or_data_permissions(rpr, expected):
    assert permission_relationships.is_valid_azure_rpr(rpr) is expected


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        (
            "/providers/Microsoft.Management/managementGroups/platform",
            f"{SUBSCRIPTION_SCOPE}/*",
        ),
        ("/", "/*"),
        (
            f"{SUBSCRIPTION_SCOPE}/resourceGroups/rg",
            f"{SUBSCRIPTION_SCOPE}/resourceGroups/rg/*",
        ),
        (STORAGE_ACCOUNT_ID, STORAGE_ACCOUNT_ID),
    ],
)
def test_resolve_azure_scope(scope, expected):
    subscription_id = SUBSCRIPTION_SCOPE.removeprefix("/subscriptions/")
    assert (
        permission_relationships.resolve_azure_scope(scope, subscription_id) == expected
    )


def test_management_group_assignment_reaches_resources_in_subscription():
    subscription_id = SUBSCRIPTION_SCOPE.removeprefix("/subscriptions/")
    assignment = {
        "assignment": {
            "permissions": permission_relationships.compile_permissions(
                {
                    "actions": ["*"],
                    "not_actions": [],
                    "data_actions": [],
                    "not_data_actions": [],
                },
            ),
            "scope": permission_relationships.compile_azure_regex(
                permission_relationships.resolve_azure_scope(
                    "/providers/Microsoft.Management/managementGroups/platform",
                    subscription_id,
                ),
            ),
            "principal_type": "User",
        },
    }

    assert permission_relationships.principal_allowed_on_resource(
        assignment,
        STORAGE_ACCOUNT_ID,
        ["Microsoft.Storage/storageAccounts/listKeys/action"],
    )
