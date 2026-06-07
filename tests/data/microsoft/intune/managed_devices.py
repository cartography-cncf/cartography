import datetime

from msgraph.generated.models.compliance_state import ComplianceState
from msgraph.generated.models.device_enrollment_type import DeviceEnrollmentType
from msgraph.generated.models.device_registration_state import DeviceRegistrationState
from msgraph.generated.models.managed_device import ManagedDevice
from msgraph.generated.models.managed_device_owner_type import ManagedDeviceOwnerType
from msgraph.generated.models.management_agent_type import ManagementAgentType

TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_USER_ID_1 = "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
TEST_USER_ID_2 = "11dca63b-cb03-4e53-bb75-fa8060285550"

MOCK_MANAGED_DEVICES = [
    ManagedDevice(
        id="device-001",
        device_name="Shyam's MacBook Pro",
        user_id=TEST_USER_ID_1,
        user_principal_name="shyam@subimage.io",
        managed_device_owner_type=ManagedDeviceOwnerType.Personal,
        operating_system="macOS",
        os_version="26.3.1",
        compliance_state=ComplianceState.Compliant,
        is_encrypted=True,
        jail_broken="Unknown",
        management_agent=ManagementAgentType.Mdm,
        manufacturer="Apple",
        model="MacBook Pro (16-inch, 2024)",
        serial_number="LL4KTK2PGD",
        imei="",
        meid="",
        wi_fi_mac_address="AA:BB:CC:DD:EE:01",
        ethernet_mac_address=None,
        azure_a_d_device_id="c384a93c-3ce3-49c2-9491-e784c12a609a",
        azure_a_d_registered=True,
        device_enrollment_type=DeviceEnrollmentType.UserEnrollment,
        device_registration_state=DeviceRegistrationState.Registered,
        is_supervised=True,
        enrolled_date_time=datetime.datetime(
            2026, 3, 18, 23, 14, 56, tzinfo=datetime.timezone.utc
        ),
        last_sync_date_time=datetime.datetime(
            2026, 3, 19, 19, 1, 22, tzinfo=datetime.timezone.utc
        ),
        eas_activated=False,
        eas_device_id="ApplLL4KTK2PGD",
        total_storage_space_in_bytes=512000000000,
        free_storage_space_in_bytes=256000000000,
        physical_memory_in_bytes=36000000000,
    ),
    ManagedDevice(
        id="device-002",
        device_name="Test Windows Laptop",
        user_id=TEST_USER_ID_2,
        user_principal_name="testuser@subimage.io",
        managed_device_owner_type=ManagedDeviceOwnerType.Company,
        operating_system="Windows",
        os_version="11.0.22631",
        compliance_state=ComplianceState.Noncompliant,
        is_encrypted=False,
        jail_broken="False",
        management_agent=ManagementAgentType.Mdm,
        manufacturer="Dell",
        model="Latitude 5540",
        serial_number="DELL12345",
        imei="",
        meid="",
        wi_fi_mac_address="AA:BB:CC:DD:EE:02",
        ethernet_mac_address="FF:GG:HH:II:JJ:02",
        azure_a_d_device_id="d495b04d-4df4-5ad3-a502-f895d23b710b",
        azure_a_d_registered=True,
        device_enrollment_type=DeviceEnrollmentType.WindowsAzureADJoin,
        device_registration_state=DeviceRegistrationState.Registered,
        is_supervised=False,
        enrolled_date_time=datetime.datetime(
            2026, 3, 10, 10, 0, 0, tzinfo=datetime.timezone.utc
        ),
        last_sync_date_time=datetime.datetime(
            2026, 3, 19, 12, 0, 0, tzinfo=datetime.timezone.utc
        ),
        eas_activated=False,
        eas_device_id=None,
        total_storage_space_in_bytes=256000000000,
        free_storage_space_in_bytes=100000000000,
        physical_memory_in_bytes=16000000000,
    ),
]
