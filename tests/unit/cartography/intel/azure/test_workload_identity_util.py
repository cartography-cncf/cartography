from cartography.intel.azure.util.common import extract_identity_principal_ids


def test_extract_identity_principal_ids_system_and_user_assigned():
    identity = {
        "type": "SystemAssigned, UserAssigned",
        "principalId": "system-pid",
        "userAssignedIdentities": {
            "/subscriptions/s/resourceGroups/rg/.../ua1": {
                "principalId": "ua-pid-1",
                "clientId": "ua-cid-1",
            },
            "/subscriptions/s/resourceGroups/rg/.../ua2": {
                "principalId": "ua-pid-2",
            },
        },
    }
    assert extract_identity_principal_ids(identity) == [
        "system-pid",
        "ua-pid-1",
        "ua-pid-2",
    ]


def test_extract_identity_principal_ids_dedupes_and_handles_missing():
    # No identity block, or a scalar/None, yields no principals.
    assert extract_identity_principal_ids(None) == []
    assert extract_identity_principal_ids("SystemAssigned") == []
    assert extract_identity_principal_ids({"type": "None"}) == []
    # Same principal id appearing twice collapses to one.
    identity = {
        "principalId": "pid",
        "userAssignedIdentities": {"ua": {"principalId": "pid"}},
    }
    assert extract_identity_principal_ids(identity) == ["pid"]
