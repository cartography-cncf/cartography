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
from cartography.models.jamf.computer import JamfComputerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SECTION_PARAMS = {
    "section": [
        "GENERAL",
        "HARDWARE",
        "OPERATING_SYSTEM",
        "SECURITY",
        "DISK_ENCRYPTION",
        "GROUP_MEMBERSHIPS",
        "USER_AND_LOCATION",
    ],
}


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


@timeit
def get(
    api_session: requests.Session,
    jamf_base_uri: str,
) -> list[dict[str, Any]]:
    try:
        return get_paginated_jamf_results(
            "/api/v1/computers-inventory",
            jamf_base_uri,
            api_session,
            params=_SECTION_PARAMS,
        )
    except requests.HTTPError as err:
        if get_http_status_code(err) not in {404, 405}:
            raise
        logger.info(
            "Jamf: /api/v1/computers-inventory unavailable; skipping computer inventory sync.",
        )
        return []


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for device in api_result:
        general = device.get("general") or {}
        hardware = device.get("hardware") or {}
        operating_system = device.get("operatingSystem") or {}
        security = device.get("security") or {}
        disk_encryption = device.get("diskEncryption") or {}
        user_and_location = device.get("userAndLocation") or {}

        result.append(
            {
                "id": device["id"],
                "udid": device.get("udid"),
                "name": general.get("name"),
                "platform": general.get("platform"),
                "report_date": general.get("reportDate"),
                "last_contact_time": general.get("lastContactTime"),
                "site_name": _get_nested(general, "site", "name"),
                "supervised": general.get("supervised"),
                "user_approved_mdm": general.get("userApprovedMdm"),
                "declarative_device_management_enabled": general.get(
                    "declarativeDeviceManagementEnabled"
                ),
                "enrolled_via_automated_device_enrollment": general.get(
                    "enrolledViaAutomatedDeviceEnrollment"
                ),
                "remote_management_managed": _get_nested(
                    general,
                    "remoteManagement",
                    "managed",
                ),
                "serial_number": hardware.get("serialNumber"),
                "model": hardware.get("model"),
                "model_identifier": hardware.get("modelIdentifier"),
                "os_name": operating_system.get("name"),
                "os_version": operating_system.get("version"),
                "os_build": operating_system.get("build"),
                "filevault_enabled": disk_encryption.get("fileVault2Enabled"),
                "firewall_enabled": security.get("firewallEnabled"),
                "gatekeeper_status": security.get("gatekeeperStatus"),
                "sip_status": security.get("sipStatus"),
                "secure_boot_level": security.get("secureBootLevel"),
                "activation_lock_enabled": security.get("activationLockEnabled"),
                "recovery_lock_enabled": security.get("recoveryLockEnabled"),
                "bootstrap_token_escrowed_status": security.get(
                    "bootstrapTokenEscrowedStatus"
                ),
                "username": user_and_location.get("username"),
                "user_real_name": user_and_location.get("realname"),
                "email": user_and_location.get("email"),
                "group_ids": [
                    group_id
                    for group_id in (
                        normalize_group_id(group.get("groupId"))
                        for group in (device.get("groupMemberships") or [])
                    )
                    if group_id is not None
                ],
            }
        )
    return result


def load_computers(
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
        JamfComputerSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(JamfComputerSchema(), common_job_parameters).run(
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
    computers = transform(raw_data)
    load_computers(neo4j_session, computers, jamf_base_uri, update_tag)
    cleanup(neo4j_session, common_job_parameters)
