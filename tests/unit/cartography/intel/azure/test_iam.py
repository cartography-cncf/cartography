from cartography.intel.azure import iam


def test_azure_role_managed_type():
    # Azure built-in roles surface either a roleDefinitions type or an explicit BuiltInRole role_type.
    assert iam._azure_role_managed_type({"type": "Microsoft.Authorization/roleDefinitions"}) == "predefined"
    assert iam._azure_role_managed_type({"role_type": "BuiltInRole"}) == "predefined"
    # Customer-authored roles report CustomRole / roleAssignments.
    assert iam._azure_role_managed_type(
        {"type": "Microsoft.Authorization/roleAssignments", "role_type": "CustomRole"},
    ) == "custom"
    assert iam._azure_role_managed_type({}) == "custom"


def test_azure_service_principal_managed_type():
    # Service principals owned by Microsoft's first-party tenant are provider-managed.
    assert iam._azure_service_principal_managed_type(iam.AZURE_MICROSOFT_TENANT_ID) == "predefined"
    assert iam._azure_service_principal_managed_type(iam.AZURE_MICROSOFT_TENANT_ID.upper()) == "predefined"
    # Customer-owned service principals belong to the customer's own tenant.
    assert iam._azure_service_principal_managed_type("00000000-1111-2222-3333-444444444444") == "custom"
    assert iam._azure_service_principal_managed_type(None) == "custom"
