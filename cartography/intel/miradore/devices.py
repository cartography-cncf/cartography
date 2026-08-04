import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.miradore.tenant import load_tenant
from cartography.intel.miradore.util import as_list
from cartography.intel.miradore.util import get_nested
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import parse_bool
from cartography.intel.miradore.util import parse_datetime
from cartography.intel.miradore.util import parse_int
from cartography.intel.miradore.util import required_int_id
from cartography.intel.miradore.util import scoped_id
from cartography.models.miradore.config_profile_deployment import (
    MiradoreConfigProfileDeploymentSchema,
)
from cartography.models.miradore.device import MiradoreDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ITEM = "Device"
# `*` selects every attribute of the queried item, excluding its child items, and has to be
# repeated per child item we care about. Enumerating child items with `*` rather than leaf
# by leaf keeps this resilient to Miradore adding attributes.
_SELECT = ",".join(
    (
        "*",
        "InvDevice.*",
        "InvOS.*",
        "Client.*",
        "Security.*",
        "Security.iOS.*",
        "Security.Android.*",
        "Security.macOS.*",
        "Security.Windows.*",
        "User.ID",
        "Organization.ID",
        "Location.ID",
        "Category.ID",
        "Category.Name",
        "Tag.Name",
        "ConfigProfileDeployment.*",
        "ConfigProfileDeployment.ConfigProfile.ID",
    )
)


@timeit
def get(
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
) -> list[dict[str, Any]]:
    return get_paginated_miradore_items(
        api_session,
        base_uri,
        site_name,
        api_key,
        _ITEM,
        _SELECT,
    )


def _get_serial_number(device: dict[str, Any], inv_device: dict[str, Any]) -> Any:
    """Resolve the device serial number from the several places Miradore reports it.

    `Device.SerialNo` only exists since API spec 1.20, and the hardware serial is only
    populated on some platforms, so fall back through every known source.
    """
    for candidate in (
        device.get("SerialNo"),
        inv_device.get("SerialNumber"),
        inv_device.get("HardwareSerialNumber"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def transform(api_result: list[dict[str, Any]], site_name: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for device in api_result:
        miradore_id = required_int_id(device, "Device")
        inv_device = device.get("InvDevice") or {}
        inv_os = device.get("InvOS") or {}
        client = device.get("Client") or {}
        security = device.get("Security") or {}
        ios = security.get("iOS") or {}
        android = security.get("Android") or {}
        macos = security.get("macOS") or {}
        windows = security.get("Windows") or {}

        result.append(
            {
                "id": scoped_id(site_name, miradore_id),
                "miradore_id": miradore_id,
                # Identity
                "serial_number": _get_serial_number(device, inv_device),
                "hostname": inv_device.get("DeviceName"),
                "udid": device.get("UDID") or inv_device.get("UDID"),
                "imei": device.get("IMEI") or inv_device.get("IMEI"),
                "android_id": device.get("AndroidID"),
                "mac_address": device.get("MACAddress"),
                "wifi_mac": inv_device.get("WiFiMAC"),
                "bluetooth_mac": inv_device.get("BluetoothMAC"),
                "ip_address": device.get("IPAddress"),
                "local_ip_address": device.get("LocalIpAddress"),
                # Hardware and operating system
                "manufacturer": inv_device.get("Manufacturer"),
                "model": inv_device.get("Model"),
                "marketing_name": inv_device.get("MarketingName"),
                "product_name": inv_device.get("ProductName"),
                "device_type": inv_device.get("DeviceType"),
                "platform": device.get("Platform"),
                "os_platform": inv_os.get("Platform"),
                "os_version": inv_os.get("Version"),
                "os_build": inv_os.get("Build"),
                "os_version_name": device.get("OSVersionName"),
                "os_language": inv_os.get("Language"),
                # Lifecycle
                "status": device.get("Status"),
                "online_status": device.get("OnlineStatus"),
                "source": device.get("Source"),
                "created": parse_datetime(device.get("Created")),
                "modified": parse_datetime(device.get("Modified")),
                "last_reported": parse_datetime(device.get("LastReported")),
                "purchase_date": parse_datetime(device.get("PurchaseDate")),
                "warranty_end_date": parse_datetime(device.get("WarrantyEndDate")),
                "lease_start_date": parse_datetime(device.get("LeaseStartDate")),
                "lease_end_date": parse_datetime(device.get("LeaseEndDate")),
                # Miradore client
                "client_id": parse_int(client.get("ID")),
                "client_version": client.get("Version"),
                "client_build_number": client.get("BuildNumber"),
                "management_type": client.get("ManagementType"),
                "device_owner_type": client.get("DeviceOwnerType"),
                "lost_mode_status": client.get("LostModeStatus"),
                "client_status": client.get("Status"),
                # Cross-platform security posture
                "passcode_set": security.get("PasscodeSet"),
                "encryption_status": security.get("EncryptionStatus"),
                # iOS security posture
                "ios_activation_lock": parse_bool(ios.get("ActivationLock")),
                "ios_device_locator_service": parse_bool(
                    ios.get("DeviceLocatorService")
                ),
                "ios_hardware_encryption": ios.get("HardwareEncryption"),
                "ios_passcode_compliant": parse_bool(ios.get("PasscodeCompliant")),
                "ios_passcode_compliant_with_profiles": parse_bool(
                    ios.get("PasscodeCompliantWithProfiles")
                ),
                "ios_passcode_present": ios.get("PasscodePresent"),
                "ios_profile_jailbroken": parse_bool(ios.get("ProfileJailBroken")),
                "ios_software_jailbroken": parse_bool(ios.get("SoftwareJailBroken")),
                "ios_supervised": parse_bool(ios.get("Supervised")),
                # Android security posture
                "android_rooted": android.get("Rooted"),
                "android_passcode_sufficient": android.get("PasscodeSufficient"),
                "android_storage_encryption_required": android.get(
                    "StorageEncryptionRequired"
                ),
                "android_storage_encryption_status": android.get(
                    "StorageEncryptionStatus"
                ),
                "android_security_patch_level": android.get("SecurityPatchLevel"),
                "android_device_administration_enabled": android.get(
                    "DeviceAdministrationEnabled"
                ),
                "android_safe_status": android.get("SAFEStatus"),
                "android_password_complexity_requirement": android.get(
                    "PasswordComplexityRequirement"
                ),
                "android_password_min_length": parse_int(
                    android.get("PasswordMinLength")
                ),
                "android_password_quality_requirement": android.get(
                    "PasswordQualityRequirement"
                ),
                "android_password_set": android.get("PasswordSet"),
                # macOS security posture
                "macos_activation_lock_enabled": parse_bool(
                    macos.get("ActivationLockEnabled")
                ),
                # Windows security posture
                "windows_secure_boot_state": windows.get("SecureBootState"),
                "windows_antivirus_status": windows.get("AntivirusStatus"),
                "windows_antivirus_signature_status": windows.get(
                    "AntivirusSignatureStatus"
                ),
                "windows_antispyware_status": windows.get("AntispywareStatus"),
                "windows_firewall_status": windows.get("FirewallStatus"),
                "windows_user_account_control_status": windows.get(
                    "UserAccountControlStatus"
                ),
                "windows_tpm_specification_version": windows.get(
                    "TrustedPlatformModuleSpecificationVersion"
                ),
                "windows_complies_with_enterprise_encryption_policy": parse_bool(
                    windows.get("CompliesWithEnterpriseEncryptionPolicy")
                ),
                # Grouping. These resolve relationships by the target's `id`, so they
                # carry the tenant-scoped identity rather than the raw Miradore ID.
                "user_id": scoped_id(
                    site_name, parse_int(get_nested(device, "User", "ID"))
                ),
                "organization_id": scoped_id(
                    site_name, parse_int(get_nested(device, "Organization", "ID"))
                ),
                "location_id": scoped_id(
                    site_name, parse_int(get_nested(device, "Location", "ID"))
                ),
                # Category has no node of its own, so it stays a raw property.
                "category_id": parse_int(get_nested(device, "Category", "ID")),
                "category_name": get_nested(device, "Category", "Name"),
                "tag_names": [
                    scoped_id(site_name, tag["Name"])
                    for tag in as_list(device.get("Tag"))
                    if isinstance(tag, dict) and tag.get("Name")
                ],
            }
        )
    return result


def transform_deployments(
    api_result: list[dict[str, Any]], site_name: str
) -> list[dict[str, Any]]:
    """Extract the configuration profile deployments carried by the device payload.

    Deployments are a `List` typed attribute of the `Device` item rather than a standalone
    queryable item, so they are derived from the same API response as the devices.
    """
    result: list[dict[str, Any]] = []
    for device in api_result:
        device_id = required_int_id(device, "Device")
        for deployment in as_list(device.get("ConfigProfileDeployment")):
            if not isinstance(deployment, dict):
                continue
            deployment_id = required_int_id(deployment, "ConfigProfileDeployment")
            result.append(
                {
                    "id": scoped_id(site_name, deployment_id),
                    "miradore_id": deployment_id,
                    "deployment_time": parse_datetime(deployment.get("DeploymentTime")),
                    "deployment_trigger": deployment.get("DeploymentTrigger"),
                    "status": deployment.get("Status"),
                    "device_id": scoped_id(site_name, device_id),
                    "config_profile_id": scoped_id(
                        site_name,
                        parse_int(get_nested(deployment, "ConfigProfile", "ID")),
                    ),
                }
            )
    return result


def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, tenant_id, update_tag)
    if not data:
        return
    load(
        neo4j_session,
        MiradoreDeviceSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def load_deployments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    if not data:
        return
    load(
        neo4j_session,
        MiradoreConfigProfileDeploymentSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        MiradoreConfigProfileDeploymentSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(MiradoreDeviceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri, site_name, api_key)
    devices = transform(raw_data, site_name)
    load_devices(neo4j_session, devices, site_name, update_tag)
    deployments = transform_deployments(raw_data, site_name)
    load_deployments(neo4j_session, deployments, site_name, update_tag)
    cleanup(neo4j_session, common_job_parameters)
