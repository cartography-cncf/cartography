import uuid

from msgraph.generated.models.assigned_license import AssignedLicense
from msgraph.generated.models.license_units_detail import LicenseUnitsDetail
from msgraph.generated.models.service_plan_info import ServicePlanInfo
from msgraph.generated.models.subscribed_sku import SubscribedSku

# SKU IDs — stable UUIDs for test assertions
SKU_ID_E5 = uuid.UUID("c7df2760-2c81-4ef7-b578-5b5392b571df")
SKU_ID_EMS = uuid.UUID("725422ed-e205-400e-ab0a-3899d8a398ca")

# Service plan IDs
SP_EXCHANGE = uuid.UUID("efb87545-963c-4e0d-99df-69c6916d9eb0")
SP_SHAREPOINT = uuid.UUID("5dbe027f-2339-4123-9542-606e4d348a72")
SP_TEAMS = uuid.UUID("57ff2da0-773e-42df-b2af-ffb7a2317929")
SP_INTUNE = uuid.UUID("c1ec4a95-1f05-45b3-a911-aa3fa01094f5")

# SubscribedSku mock data

MOCK_SUBSCRIBED_SKUS = [
    SubscribedSku(
        id="tenant-sku-e5",
        sku_id=SKU_ID_E5,
        sku_part_number="ENTERPRISEPREMIUM",
        capability_status="Enabled",
        applies_to="User",
        consumed_units=2,
        prepaid_units=LicenseUnitsDetail(
            enabled=25,
            suspended=0,
            warning=0,
        ),
        service_plans=[
            ServicePlanInfo(
                service_plan_id=SP_EXCHANGE,
                service_plan_name="EXCHANGE_S_ENTERPRISE",
                provisioning_status="Success",
                applies_to="User",
            ),
            ServicePlanInfo(
                service_plan_id=SP_SHAREPOINT,
                service_plan_name="SHAREPOINTENTERPRISE",
                provisioning_status="Success",
                applies_to="User",
            ),
            ServicePlanInfo(
                service_plan_id=SP_TEAMS,
                service_plan_name="TEAMS1",
                provisioning_status="Success",
                applies_to="User",
            ),
        ],
    ),
    SubscribedSku(
        id="tenant-sku-ems",
        sku_id=SKU_ID_EMS,
        sku_part_number="EMS",
        capability_status="Enabled",
        applies_to="User",
        consumed_units=1,
        prepaid_units=LicenseUnitsDetail(
            enabled=10,
            suspended=0,
            warning=0,
        ),
        service_plans=[
            ServicePlanInfo(
                service_plan_id=SP_INTUNE,
                service_plan_name="INTUNE_A",
                provisioning_status="Success",
                applies_to="User",
            ),
            # SP_EXCHANGE is shared across licenses
            ServicePlanInfo(
                service_plan_id=SP_EXCHANGE,
                service_plan_name="EXCHANGE_S_ENTERPRISE",
                provisioning_status="Success",
                applies_to="User",
            ),
        ],
    ),
]

# Per-user assigned licenses

MOCK_USER_ASSIGNED_LICENSES: dict[str, list[AssignedLicense]] = {
    # User with E5 and EMS
    "ae4ac864-4433-4ba6-96a6-20f8cffdadcb": [
        AssignedLicense(
            sku_id=SKU_ID_E5,
        ),
        AssignedLicense(
            sku_id=SKU_ID_EMS,
        ),
    ],
    # User with E5 only
    "11dca63b-cb03-4e53-bb75-fa8060285550": [
        AssignedLicense(
            sku_id=SKU_ID_E5,
        ),
    ],
}
