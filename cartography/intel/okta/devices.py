from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.device_list import DeviceList

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_paginated
from cartography.models.okta.device import OktaDeviceSchema
from cartography.models.okta.device import OktaUserOwnsDeviceRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _timestamp(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


@timeit
async def _get_okta_devices(okta_client: OktaClient) -> list[DeviceList]:
    return await collect_paginated(
        okta_client.list_devices,
        expand="userSummary",
    )


def _transform_okta_devices(
    devices: list[DeviceList],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transformed_devices: list[dict[str, Any]] = []
    user_relationships: list[dict[str, Any]] = []

    for device in devices:
        profile = device.profile
        resource_display_name = device.resource_display_name
        transformed_devices.append(
            {
                "id": device.id,
                "status": _value(device.status),
                "created": _timestamp(device.created),
                "okta_last_updated": _timestamp(device.last_updated),
                "display_name": profile.display_name if profile else None,
                "platform": _value(profile.platform) if profile else None,
                "serial_number": profile.serial_number if profile else None,
                "sid": profile.sid if profile else None,
                "manufacturer": profile.manufacturer if profile else None,
                "model": profile.model if profile else None,
                "os_version": profile.os_version if profile else None,
                "registered": profile.registered if profile else None,
                "managed": profile.managed if profile else None,
                "secure_hardware_present": (
                    profile.secure_hardware_present if profile else None
                ),
                "disk_encryption_type": (
                    _value(profile.disk_encryption_type) if profile else None
                ),
                "integrity_jailbreak": (
                    profile.integrity_jailbreak if profile else None
                ),
                "imei": profile.imei if profile else None,
                "meid": profile.meid if profile else None,
                "udid": profile.udid if profile else None,
                "tpm_public_key_hash": (
                    profile.tpm_public_key_hash if profile else None
                ),
                "resource_type": device.resource_type,
                "resource_display_name": (
                    resource_display_name.value if resource_display_name else None
                ),
                "resource_display_name_sensitive": (
                    resource_display_name.sensitive if resource_display_name else None
                ),
                "resource_alternate_id": device.resource_alternate_id,
            },
        )

        embedded_users = device.embedded.users if device.embedded else None
        for enrollment in embedded_users or []:
            if enrollment.user and enrollment.user.id:
                user_relationships.append(
                    {
                        "device_id": device.id,
                        "user_id": enrollment.user.id,
                        "management_status": enrollment.management_status,
                        "screen_lock_type": enrollment.screen_lock_type,
                        "enrolled_at": enrollment.created,
                    },
                )

    return transformed_devices, user_relationships


def _load_okta_devices(
    neo4j_session: neo4j.Session,
    devices: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaDeviceSchema(),
        devices,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _load_okta_user_device_relationships(
    neo4j_session: neo4j.Session,
    relationships: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load_matchlinks(
        neo4j_session,
        OktaUserOwnsDeviceRel(),
        relationships,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        _sub_resource_label="OktaOrganization",
        _sub_resource_id=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_devices(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_matchlink(
        OktaUserOwnsDeviceRel(),
        "OktaOrganization",
        common_job_parameters["OKTA_ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        OktaDeviceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_okta_devices(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Okta devices")
    raw_devices = asyncio.run(_get_okta_devices(okta_client))
    devices, user_relationships = _transform_okta_devices(raw_devices)
    _load_okta_devices(neo4j_session, devices, common_job_parameters)
    _load_okta_user_device_relationships(
        neo4j_session,
        user_relationships,
        common_job_parameters,
    )
    _cleanup_okta_devices(neo4j_session, common_job_parameters)
    logger.info(
        "Loaded %s Okta devices and %s user ownership relationships",
        len(devices),
        len(user_relationships),
    )
