import datetime

from msgraph.generated.models.device_and_app_management_assignment_target import (
    DeviceAndAppManagementAssignmentTarget,
)
from msgraph.generated.models.device_compliance_policy import DeviceCompliancePolicy
from msgraph.generated.models.device_compliance_policy_assignment import (
    DeviceCompliancePolicyAssignment,
)
from msgraph.generated.models.group_assignment_target import GroupAssignmentTarget

TEST_GROUP_ID = "18feec2a-b1e5-4e73-bbbb-8cae11678441"

MOCK_COMPLIANCE_POLICIES = [
    DeviceCompliancePolicy(
        id="policy-001",
        odata_type="#microsoft.graph.macOSCompliancePolicy",
        display_name="macOS Compliance Policy",
        description="Require encryption and minimum OS version for macOS devices",
        version=1,
        created_date_time=datetime.datetime(
            2026, 3, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
        ),
        last_modified_date_time=datetime.datetime(
            2026, 3, 15, 8, 30, 0, tzinfo=datetime.timezone.utc
        ),
        assignments=[
            DeviceCompliancePolicyAssignment(
                id="policy-001_" + TEST_GROUP_ID,
                target=GroupAssignmentTarget(
                    odata_type="#microsoft.graph.groupAssignmentTarget",
                    group_id=TEST_GROUP_ID,
                ),
            ),
        ],
    ),
    DeviceCompliancePolicy(
        id="policy-002",
        odata_type="#microsoft.graph.androidCompliancePolicy",
        display_name="Android Compliance Policy",
        description="Default compliance for Android devices",
        version=1,
        created_date_time=datetime.datetime(
            2026, 3, 5, 10, 0, 0, tzinfo=datetime.timezone.utc
        ),
        last_modified_date_time=datetime.datetime(
            2026, 3, 5, 10, 0, 0, tzinfo=datetime.timezone.utc
        ),
        assignments=[
            DeviceCompliancePolicyAssignment(
                id="policy-002_all_devices",
                target=DeviceAndAppManagementAssignmentTarget(
                    odata_type="#microsoft.graph.allDevicesAssignmentTarget",
                ),
            ),
        ],
    ),
]
