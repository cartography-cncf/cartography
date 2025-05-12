import datetime

from msgraph.generated.models.administrative_unit import AdministrativeUnit

# Use the same test tenant ID for consistency
TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_SECRET = "abcdefghijklmnopqrstuvwxyz"

MOCK_ENTRA_OUS = [
    AdministrativeUnit(
        id="a8f9e4b2-1234-5678-9abc-def012345678",
        odata_type="#microsoft.graph.administrativeUnit",
        deleted_date_time=None,
        display_name="Finance Department",
        description="Handles financial operations and budgeting",
        visibility="Public",
        membership_type="Dynamic",
        membership_rule='user.department -eq "Finance"',
        is_member_management_restricted=False,
    ),
    AdministrativeUnit(
        id="b6c5d3e4-5678-90ab-cdef-1234567890ab",
        odata_type="#microsoft.graph.administrativeUnit",
        deleted_date_time=datetime.datetime(
            2025, 3, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
        ),
        display_name="IT Operations",
        description="Manages IT infrastructure and support",
        visibility="Private",
        membership_type="Assigned",
        membership_rule=None,
        membership_rule_processing_state=None,
        is_member_management_restricted=True,
    ),
]

# Example of an OU with nested structure
MOCK_NESTED_OU = AdministrativeUnit(
    id="c7d8e9f0-1234-5678-90ab-cdef12345678",
    odata_type="#microsoft.graph.administrativeUnit",
    display_name="EMEA Region",
    description="European, Middle Eastern, and African operations",
    visibility="HiddenMembership",
    membership_type="Dynamic",
    membership_rule='user.country -in ["GB", "DE", "AE", "ZA"]',
    membership_rule_processing_state="On",
    additional_data={
        "parentUnit": {
            "id": "a8f9e4b2-1234-5678-9abc-def012345678",
            "display_name": "Finance Department",
        },
    },
)
