from typing import Any
from typing import AsyncGenerator

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.compliance_state import ComplianceState
from msgraph.generated.models.device_enrollment_type import DeviceEnrollmentType
from msgraph.generated.models.device_registration_state import DeviceRegistrationState
from msgraph.generated.models.managed_device import ManagedDevice
from msgraph.generated.models.managed_device_owner_type import ManagedDeviceOwnerType
from msgraph.generated.models.managed_device_partner_reported_health_state import (
    ManagedDevicePartnerReportedHealthState,
)
from msgraph.generated.models.management_agent_type import ManagementAgentType

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.microsoft.intune.managed_device import IntuneManagedDeviceSchema
from cartography.util import timeit


@timeit
async def get_managed_devices(
    client: GraphServiceClient,
) -> AsyncGenerator[ManagedDevice, None]:
    """
    Get all Intune managed devices from Microsoft Graph API.
    https://learn.microsoft.com/en-us/graph/api/intune-devices-manageddevice-list
    Permissions: DeviceManagementManagedDevices.Read.All
    """
    page = await client.device_management.managed_devices.get()
    while page:
        if page.value:
            for device in page.value:
                yield device
        if not page.odata_next_link:
            break

        page = await client.device_management.managed_devices.with_url(
            page.odata_next_link,
        ).get()


@timeit
def transform_managed_devices(
    devices: list[ManagedDevice],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for device in devices:
        owner_type: ManagedDeviceOwnerType | None = device.managed_device_owner_type
        compliance: ComplianceState | None = device.compliance_state
        mgmt_agent: ManagementAgentType | None = device.management_agent
        enrollment_type: DeviceEnrollmentType | None = device.device_enrollment_type
        reg_state: DeviceRegistrationState | None = device.device_registration_state
        threat_state: ManagedDevicePartnerReportedHealthState | None = (
            device.partner_reported_threat_state
        )
        result.append(
            {
                "id": device.id,
                "device_name": device.device_name,
                "user_id": device.user_id,
                "user_principal_name": device.user_principal_name,
                "managed_device_owner_type": owner_type.value if owner_type else None,
                "operating_system": device.operating_system,
                "os_version": device.os_version,
                "compliance_state": compliance.value if compliance else None,
                "is_encrypted": device.is_encrypted,
                "jail_broken": device.jail_broken,
                "management_agent": mgmt_agent.value if mgmt_agent else None,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "serial_number": device.serial_number,
                "imei": device.imei,
                "meid": device.meid,
                "wifi_mac_address": device.wi_fi_mac_address,
                "ethernet_mac_address": device.ethernet_mac_address,
                "azure_ad_device_id": device.azure_a_d_device_id,
                "azure_ad_registered": device.azure_a_d_registered,
                "device_enrollment_type": (
                    enrollment_type.value if enrollment_type else None
                ),
                "device_registration_state": reg_state.value if reg_state else None,
                "is_supervised": device.is_supervised,
                "enrolled_date_time": device.enrolled_date_time,
                "last_sync_date_time": device.last_sync_date_time,
                "eas_activated": device.eas_activated,
                "eas_device_id": device.eas_device_id,
                "partner_reported_threat_state": (
                    threat_state.value if threat_state else None
                ),
                "total_storage_space_in_bytes": device.total_storage_space_in_bytes,
                "free_storage_space_in_bytes": device.free_storage_space_in_bytes,
                "physical_memory_in_bytes": device.physical_memory_in_bytes,
            }
        )
    return result


@timeit
def load_managed_devices(
    neo4j_session: neo4j.Session,
    devices: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        IntuneManagedDeviceSchema(),
        devices,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        IntuneManagedDeviceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
async def sync_managed_devices(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    devices_batch: list[ManagedDevice] = []
    batch_size = 500

    async for device in get_managed_devices(client):
        devices_batch.append(device)

        if len(devices_batch) >= batch_size:
            transformed = transform_managed_devices(devices_batch)
            load_managed_devices(neo4j_session, transformed, tenant_id, update_tag)
            devices_batch.clear()

    if devices_batch:
        transformed = transform_managed_devices(devices_batch)
        load_managed_devices(neo4j_session, transformed, tenant_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
