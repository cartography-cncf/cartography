import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jamf.tenant import load_tenant
from cartography.intel.jamf.util import get_http_status_code
from cartography.intel.jamf.util import get_paginated_jamf_results
from cartography.intel.jamf.util import normalize_group_id
from cartography.models.jamf.mobiledevice import JamfMobileDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SECTION_PARAMS = {
    "section": [
        "GENERAL",
        "HARDWARE",
        "SECURITY",
        "GROUPS",
        "USER_AND_LOCATION",
    ],
}


def _normalize_mobile_os(device_type: str | None) -> str | None:
    """Normalize Jamf mobile device family values into OS-family values.

    Jamf's v2 mobile inventory uses ``deviceType`` for mobile family/platform
    values. In practice this may already be an OS-family value such as ``iOS``,
    but some tenants and fixtures return hardware-family values such as
    ``iPhone`` or ``iPad``. Normalize the known values here so the provider node
    can expose a consistent OS-family field to the ontology.
    """
    if not device_type:
        return None

    normalized = device_type.strip().lower()
    os_by_device_type = {
        "ios": "iOS",
        "iphone": "iOS",
        "ipod": "iOS",
        "ipados": "iPadOS",
        "ipad": "iPadOS",
        "tvos": "tvOS",
        "apple tv": "tvOS",
        "appletv": "tvOS",
        "android": "Android",
    }
    return os_by_device_type.get(normalized)


@timeit
def get(
    api_session: requests.Session,
    jamf_base_uri: str,
) -> list[dict[str, Any]]:
    try:
        return get_paginated_jamf_results(
            "/api/v2/mobile-devices/detail",
            jamf_base_uri,
            api_session,
            params=_SECTION_PARAMS,
        )
    except requests.HTTPError as err:
        if get_http_status_code(err) not in {404, 405}:
            raise
        logger.info(
            "Jamf: /api/v2/mobile-devices/detail unavailable; skipping mobile device sync.",
        )
        return []


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for device in api_result:
        general = device.get("general") or {}
        hardware = device.get("hardware") or {}
        security = device.get("security") or {}
        user_and_location = device.get("userAndLocation") or {}

        result.append(
            {
                "id": device["mobileDeviceId"],
                "display_name": general.get("displayName"),
                "managed": general.get("managed"),
                "supervised": general.get("supervised"),
                "last_inventory_update_date": general.get("lastInventoryUpdateDate"),
                "last_enrolled_date": general.get("lastEnrolledDate"),
                "platform": device.get("deviceType"),
                "os": _normalize_mobile_os(device.get("deviceType")),
                "os_version": general.get("osVersion"),
                "os_build": general.get("osBuild"),
                "serial_number": hardware.get("serialNumber"),
                "model": hardware.get("model"),
                "model_identifier": hardware.get("modelIdentifier"),
                "activation_lock_enabled": security.get("activationLockEnabled"),
                "bootstrap_token_escrowed": security.get("bootstrapTokenEscrowed"),
                "data_protected": security.get("dataProtected"),
                "hardware_encryption": security.get("hardwareEncryption"),
                "jailbreak_detected": security.get("jailBreakDetected"),
                "lost_mode_enabled": security.get("lostModeEnabled"),
                "passcode_compliant": security.get("passcodeCompliant"),
                "passcode_present": security.get("passcodePresent"),
                "username": user_and_location.get("username"),
                "user_real_name": user_and_location.get("realName"),
                "email": user_and_location.get("emailAddress"),
                "group_ids": [
                    group_id
                    for group_id in (
                        normalize_group_id(group.get("groupId"))
                        for group in (device.get("groups") or [])
                    )
                    if group_id is not None
                ],
            }
        )
    return result


def load_mobile_devices(
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
        JamfMobileDeviceSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JamfMobileDeviceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    jamf_base_uri: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, jamf_base_uri)
    mobile_devices = transform(raw_data)
    load_mobile_devices(neo4j_session, mobile_devices, jamf_base_uri, update_tag)
    cleanup(neo4j_session, common_job_parameters)
