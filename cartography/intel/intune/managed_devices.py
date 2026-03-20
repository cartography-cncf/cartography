import logging
from typing import Any
from typing import AsyncGenerator

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.intune.managed_device import IntuneManagedDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Enum types from the SDK that we convert to strings for storage in the graph.
# The SDK returns these as enum members (e.g. ComplianceState.Compliant);
# calling .value on them gives us a stable lowercase string.
_ENUM_FIELDS = [
    "managed_device_owner_type",
    "compliance_state",
    "management_agent",
    "device_enrollment_type",
    "device_registration_state",
    "partner_reported_threat_state",
]


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

        try:
            page = await client.device_management.managed_devices.with_url(
                page.odata_next_link,
            ).get()
        except Exception as e:
            logger.error(
                "Failed to fetch next page of Intune managed devices "
                "– stopping pagination early: %s",
                e,
            )
            break


def _enum_to_str(val: Any) -> str | None:
    """Convert an SDK enum value to its string representation, or None."""
    if val is None:
        return None
    return val.value if hasattr(val, "value") else str(val)


@timeit
def transform_managed_devices(
    devices: list[ManagedDevice],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for device in devices:
        d: dict[str, Any] = {
            "id": device.id,
            "device_name": device.device_name,
            "user_id": device.user_id,
            "user_principal_name": device.user_principal_name,
            "operating_system": device.operating_system,
            "os_version": device.os_version,
            "is_encrypted": device.is_encrypted,
            "jail_broken": device.jail_broken,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "serial_number": device.serial_number,
            "imei": device.imei,
            "meid": device.meid,
            "wifi_mac_address": device.wi_fi_mac_address,
            "ethernet_mac_address": device.ethernet_mac_address,
            "azure_ad_device_id": device.azure_a_d_device_id,
            "azure_ad_registered": device.azure_a_d_registered,
            "is_supervised": device.is_supervised,
            "enrolled_date_time": device.enrolled_date_time,
            "last_sync_date_time": device.last_sync_date_time,
            "eas_activated": device.eas_activated,
            "eas_device_id": device.eas_device_id,
            "total_storage_space_in_bytes": device.total_storage_space_in_bytes,
            "free_storage_space_in_bytes": device.free_storage_space_in_bytes,
            "physical_memory_in_bytes": device.physical_memory_in_bytes,
        }
        # Convert enum fields to strings
        for field in _ENUM_FIELDS:
            d[field] = _enum_to_str(getattr(device, field, None))
        result.append(d)
    return result


@timeit
def load_managed_devices(
    neo4j_session: neo4j.Session,
    devices: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(devices)} Intune managed devices")
    load(
        neo4j_session,
        IntuneManagedDeviceSchema(),
        devices,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


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
