from datetime import datetime
from datetime import timezone
from uuid import UUID

from msgraph.generated.models.app_role_assignment import AppRoleAssignment
from msgraph.generated.models.application import Application
from msgraph.generated.models.service_principal import ServicePrincipal
from msgraph.generated.models.web_application import WebApplication

TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_SECRET = "abcdefghijklmnopqrstuvwxyz"

MOCK_ENTRA_APPLICATIONS = [
    Application(
        id="11111111-1111-1111-1111-111111111111",
        odata_type="#microsoft.graph.application",
        app_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        created_date_time=datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        display_name="Finance Tracker",
        publisher_domain="example.com",
        sign_in_audience="AzureADMyOrg",
        web=WebApplication(redirect_uris=["https://finance.example.com/callback"]),
    ),
    Application(
        id="22222222-2222-2222-2222-222222222222",
        odata_type="#microsoft.graph.application",
        app_id="ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        created_date_time=datetime(2025, 5, 2, 8, 30, 0, tzinfo=timezone.utc),
        display_name="HR Portal",
        publisher_domain="example.org",
        sign_in_audience="AzureADMultipleOrgs",
        web=WebApplication(redirect_uris=["https://hr.example.org/login"]),
    ),
]

# New dict-based mock data for the refactored API functions
MOCK_ENTRA_APPLICATIONS_DICT = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "app_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "display_name": "Finance Tracker",
        "publisher_domain": "example.com",
        "sign_in_audience": "AzureADMyOrg",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "app_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        "display_name": "HR Portal",
        "publisher_domain": "example.org",
        "sign_in_audience": "AzureADMultipleOrgs",
    },
]

MOCK_APP_ROLE_ASSIGNMENTS = [
    AppRoleAssignment(
        id="assignment-1",
        app_role_id=UUID("00000000-0000-0000-0000-000000000000"),
        principal_id=UUID(
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
        ),  # matches existing user
        principal_display_name="Test User 1",
        principal_type="User",
        resource_id=UUID(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        ),  # matches first app's app_id
        resource_display_name="Finance Tracker",
        created_date_time=datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
    ),
    AppRoleAssignment(
        id="assignment-2",
        app_role_id=UUID("00000000-0000-0000-0000-000000000000"),
        principal_id=UUID(
            "11dca63b-cb03-4e53-bb75-fa8060285550"
        ),  # matches existing user
        principal_display_name="Test User 2",
        principal_type="User",
        resource_id=UUID(
            "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb"
        ),  # matches second app's app_id
        resource_display_name="HR Portal",
        created_date_time=datetime(2025, 5, 2, 8, 30, 0, tzinfo=timezone.utc),
    ),
    AppRoleAssignment(
        id="assignment-3",
        app_role_id=UUID("00000000-0000-0000-0000-000000000000"),
        principal_id=UUID("11111111-2222-3333-4444-555555555555"),  # group ID
        principal_display_name="Finance Team",
        principal_type="Group",
        resource_id=UUID(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        ),  # matches first app's app_id
        resource_display_name="Finance Tracker",
        created_date_time=datetime(2025, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
    ),
    AppRoleAssignment(
        id="assignment-4",
        app_role_id=UUID("00000000-0000-0000-0000-000000000000"),
        principal_id=UUID("22222222-3333-4444-5555-666666666666"),  # group ID
        principal_display_name="HR Team",
        principal_type="Group",
        resource_id=UUID(
            "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb"
        ),  # matches second app's app_id
        resource_display_name="HR Portal",
        created_date_time=datetime(2025, 5, 4, 14, 30, 0, tzinfo=timezone.utc),
    ),
]

# New dict-based mock data for the refactored API functions
MOCK_APP_ROLE_ASSIGNMENTS_DICT = [
    {
        "id": "assignment-1",
        "app_role_id": "00000000-0000-0000-0000-000000000000",
        "created_date_time": datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        "principal_id": "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
        "principal_display_name": "Test User 1",
        "principal_type": "User",
        "resource_display_name": "Finance Tracker",
        "resource_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "application_app_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    },
    {
        "id": "assignment-2",
        "app_role_id": "00000000-0000-0000-0000-000000000000",
        "created_date_time": datetime(2025, 5, 2, 8, 30, 0, tzinfo=timezone.utc),
        "principal_id": "11dca63b-cb03-4e53-bb75-fa8060285550",
        "principal_display_name": "Test User 2",
        "principal_type": "User",
        "resource_display_name": "HR Portal",
        "resource_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        "application_app_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
    },
    {
        "id": "assignment-3",
        "app_role_id": "00000000-0000-0000-0000-000000000000",
        "created_date_time": datetime(2025, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        "principal_id": "11111111-2222-3333-4444-555555555555",
        "principal_display_name": "Finance Team",
        "principal_type": "Group",
        "resource_display_name": "Finance Tracker",
        "resource_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "application_app_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    },
    {
        "id": "assignment-4",
        "app_role_id": "00000000-0000-0000-0000-000000000000",
        "created_date_time": datetime(2025, 5, 4, 14, 30, 0, tzinfo=timezone.utc),
        "principal_id": "22222222-3333-4444-5555-666666666666",
        "principal_display_name": "HR Team",
        "principal_type": "Group",
        "resource_display_name": "HR Portal",
        "resource_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        "application_app_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
    },
]

MOCK_SERVICE_PRINCIPALS = [
    ServicePrincipal(
        id="sp-11111111-1111-1111-1111-111111111111",
        app_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        display_name="Finance Tracker Service Principal",
        reply_urls=[
            "https://finance.example.com/callback",
            "https://d-1234567890.awsapps.com/start",
        ],
        account_enabled=True,
        service_principal_type="Application",
        login_url="https://d-1234567890.awsapps.com/start",
        sign_in_audience="AzureADMyOrg",
    ),
    ServicePrincipal(
        id="sp-22222222-2222-2222-2222-222222222222",
        app_id="ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        display_name="HR Portal Service Principal",
        reply_urls=["https://hr.example.org/login"],
        account_enabled=True,
        service_principal_type="Application",
        login_url="https://hr.example.org/login",
        sign_in_audience="AzureADMultipleOrgs",
    ),
]

MOCK_SERVICE_PRINCIPALS_DICT = [
    {
        "id": "sp-11111111-1111-1111-1111-111111111111",
        "app_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "display_name": "Finance Tracker Service Principal",
        "reply_urls": [
            "https://finance.example.com/callback",
            "https://d-1234567890.awsapps.com/start",
        ],
        "aws_identity_center_instance_id": "d-1234567890",
        "account_enabled": True,
        "service_principal_type": "Application",
        "login_url": "https://d-1234567890.awsapps.com/start",
        "sign_in_audience": "AzureADMyOrg",
    },
    {
        "id": "sp-22222222-2222-2222-2222-222222222222",
        "app_id": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
        "display_name": "HR Portal Service Principal",
        "reply_urls": ["https://hr.example.org/login"],
        "aws_identity_center_instance_id": None,
        "account_enabled": True,
        "service_principal_type": "Application",
        "login_url": "https://hr.example.org/login",
        "sign_in_audience": "AzureADMultipleOrgs",
    },
]
