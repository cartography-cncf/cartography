import datetime
import uuid

from msgraph.generated.models.assigned_plan import AssignedPlan
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.user import User
from msgraph.generated.models.verified_domain import VerifiedDomain

# some fake tenant guid
TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"

MOCK_ENTRA_TENANT = Organization(
    additional_data={
        "isMultipleDataLocationsForServicesEnabled": None,
        "directorySizeQuota": {"used": 277, "total": 300000},
        "onPremisesSyncStatus": [
            {
                "attributeSetName": "iab",
                "state": "enabled",
                "version": 2,
            }
        ],
    },
    id=TEST_TENANT_ID,
    odata_type="#microsoft.graph.organization",
    deleted_date_time=None,
    assigned_plans=[
        AssignedPlan(
            additional_data={},
            assigned_date_time=datetime.datetime(
                2025, 4, 7, 18, 52, 15, tzinfo=datetime.timezone.utc
            ),
            capability_status="Enabled",
            odata_type=None,
            service="WindowsAzure",
            service_plan_id=uuid.UUID("9c37ad68-ecb9-4d64-ba09-f296d92d9e55"),
        ),
    ],
    city="San Francisco",
    country=None,
    country_letter_code="US",
    created_date_time=datetime.datetime(
        2025, 4, 5, 2, 8, 28, tzinfo=datetime.timezone.utc
    ),
    default_usage_location=None,
    display_name="Springfield Nuclear Power Plant",
    marketing_notification_emails=[],
    mobile_device_management_authority=None,
    on_premises_last_sync_date_time=datetime.datetime(
        2025, 4, 16, 3, 44, 33, tzinfo=datetime.timezone.utc
    ),
    on_premises_sync_enabled=True,
    partner_tenant_type=None,
    postal_code="12345",
    preferred_language="en",
    state="ca",
    street="742 Evergreen Terrace",
    tenant_type="AAD",
    verified_domains=[
        VerifiedDomain(
            additional_data={},
            capabilities="Email, OfficeCommunicationsOnline",
            is_default=True,
            is_initial=True,
            name="mycompany.onmicrosoft.com",
            odata_type=None,
            type="Managed",
        ),
    ],
)

MOCK_ENTRA_USERS = [
    User(
        id="ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
        odata_type="#microsoft.graph.user",
        display_name="Homer Simpson",
        given_name="Homer",
        mail="hjsimpson@simpson.corp",
        surname="Simpson",
        department="Operations",
        manager=DirectoryObject(id="11dca63b-cb03-4e53-bb75-fa8060285550"),
        user_principal_name="hjsimpson@simpson.corp",
    ),
    User(
        id="11dca63b-cb03-4e53-bb75-fa8060285550",
        odata_type="#microsoft.graph.user",
        display_name="Entra Test User 1",
        department="Engineering",
        user_principal_name="entra-test-user-1@mycompany.onmicrosoft.com",
    ),
]
