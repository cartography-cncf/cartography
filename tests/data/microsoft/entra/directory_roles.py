from msgraph.generated.models.unified_role_assignment import UnifiedRoleAssignment
from msgraph.generated.models.unified_role_definition import UnifiedRoleDefinition

TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c480"
TEST_CLIENT_SECRET = "fake-client-secret"

# Well-known built-in directory role template ids
GLOBAL_ADMIN_ROLE_ID = "62e90394-69f5-4237-9190-012177145e10"
USER_ADMIN_ROLE_ID = "fe930be7-5e62-47db-91af-98c3a49a38b1"

# Principal ids referenced by the mock assignments
TEST_USER_ID = "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
TEST_GROUP_ID = "11111111-2222-3333-4444-555555555555"
TEST_SP_ID = "33333333-4444-5555-6666-777777777777"

MOCK_ROLE_DEFINITIONS = [
    UnifiedRoleDefinition(
        id=GLOBAL_ADMIN_ROLE_ID,
        display_name="Global Administrator",
        description=(
            "Can manage all aspects of Microsoft Entra ID and Microsoft "
            "services that use Microsoft Entra ID identities."
        ),
        is_built_in=True,
        is_enabled=True,
        template_id=GLOBAL_ADMIN_ROLE_ID,
    ),
    UnifiedRoleDefinition(
        id=USER_ADMIN_ROLE_ID,
        display_name="User Administrator",
        description="Can manage all aspects of users and groups.",
        is_built_in=True,
        is_enabled=True,
        template_id=USER_ADMIN_ROLE_ID,
    ),
]

MOCK_ROLE_ASSIGNMENTS = [
    UnifiedRoleAssignment(
        id="assignment-ga-user",
        role_definition_id=GLOBAL_ADMIN_ROLE_ID,
        principal_id=TEST_USER_ID,
        directory_scope_id="/",
        app_scope_id=None,
    ),
    UnifiedRoleAssignment(
        id="assignment-ua-group",
        role_definition_id=USER_ADMIN_ROLE_ID,
        principal_id=TEST_GROUP_ID,
        directory_scope_id="/",
        app_scope_id=None,
    ),
    UnifiedRoleAssignment(
        id="assignment-ga-sp",
        role_definition_id=GLOBAL_ADMIN_ROLE_ID,
        principal_id=TEST_SP_ID,
        directory_scope_id="/",
        app_scope_id=None,
    ),
]
