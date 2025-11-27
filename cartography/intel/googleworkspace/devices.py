import datetime
import json
import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.device import GoogleWorkspaceDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_devices(
    cloudidentity: Resource,
) -> list[dict[str, Any]]:
    """
    Fetch all devices from Google Cloud Identity API.
    """
    # Only fetch user synced in the last 90 days
    from_date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=90
    )
    request = cloudidentity.devices().list(
        customer="customers/my_customer",
        pageSize=100,
        orderBy="last_sync_time desc",
        filter=f"sync:{from_date.strftime('%Y-%m-%dT%H:%M:%S')}..",
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.extend(resp.get("devices", []))
            request = cloudidentity.devices().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required Google Workspace scopes. If using the gcloud CLI, "
                    "run: gcloud auth application-default login --scopes="
                    "https://www.googleapis.com/auth/admin.directory.customer.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.security,"
                    "https://www.googleapis.com/auth/cloud-identity.devices.readonly,"
                    "https://www.googleapis.com/auth/cloud-identity.groups.readonly,"
                    "https://www.googleapis.com/auth/cloud-platform"
                )
            raise
    return response_objects


@timeit
def get_device_users(
    cloudidentity: Resource,
) -> list[dict[str, Any]]:
    """
    Fetch all device users from Google Cloud Identity API.
    """
    # Only fetch user synced in the last 90 days
    from_date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=90
    )
    request = (
        cloudidentity.devices()
        .deviceUsers()
        .list(
            customer="customers/my_customer",
            parent="devices/-",
            pageSize=100,
            orderBy="last_sync_time desc",
            filter=f"sync:{from_date.strftime('%Y-%m-%dT%H:%M:%S')}..",
        )
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.extend(resp.get("deviceUsers", []))
            request = cloudidentity.devices().deviceUsers().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required Google Workspace scopes. If using the gcloud CLI, "
                    "run: gcloud auth application-default login --scopes="
                    "https://www.googleapis.com/auth/admin.directory.customer.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.security,"
                    "https://www.googleapis.com/auth/cloud-identity.devices.readonly,"
                    "https://www.googleapis.com/auth/cloud-identity.groups.readonly,"
                    "https://www.googleapis.com/auth/cloud-platform"
                )
            raise

    return response_objects


def transform_devices(
    devices: list[dict[str, Any]], device_users: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Transform device data for Neo4j ingestion.
    """
    result = []

    # First we need to create a mapping of device ID to its users
    device_user_map: dict[str, str] = {}
    for device_user in device_users:
        # Ignore non approved device
        if device_user.get("managementState") != "APPROVED":
            continue
        if device_user.get("userEmail") is None:
            continue
        # Extract device name from device user name path
        device_name = device_user["name"].split("/deviceUsers/")[0]
        if device_name not in device_user_map:
            device_user_map[device_name] = device_user["userEmail"]
        else:
            logger.debug(
                "Multiple users found for device %s, the most recent was kept",
                device_name,
            )

    # Now transform each device, adding its users
    for device in devices:
        # Extract device ID from name path (devices/EiRlNzYzZjYyNC1...)
        device_name = device["name"]

        transformed = {
            # Required fields
            "deviceId": device.get("deviceId"),
            "hostname": device.get("hostname"),
            # Owner
            "owner_email": device_user_map.get(device_name),
            # Device information
            "model": device.get("model"),
            "manufacturer": device.get("manufacturer"),
            "releaseVersion": device.get("releaseVersion"),
            "brand": device.get("brand"),
            "buildNumber": device.get("buildNumber"),
            "kernelVersion": device.get("kernelVersion"),
            "basebandVersion": device.get("basebandVersion"),
            "deviceType": device.get("deviceType"),
            "osVersion": device.get("osVersion"),
            "ownerType": device.get("ownerType"),
            # Hardware identifiers
            "serialNumber": device.get("serialNumber"),
            "assetTag": device.get("assetTag"),
            "imei": device.get("imei"),
            "meid": device.get("meid"),
            "wifiMacAddresses": device.get("wifiMacAddresses"),
            "networkOperator": device.get("networkOperator"),
            # Security and state
            "encryptionState": device.get("encryptionState"),
            "compromisedState": device.get("compromisedState"),
            "managementState": device.get("managementState"),
            # Timestamps
            "createTime": device.get("createTime"),
            "lastSyncTime": device.get("lastSyncTime"),
            "securityPatchTime": device.get("securityPatchTime"),
            # Android specific attributes (stored as JSON string if present)
            "androidSpecificAttributes": (
                json.dumps(device.get("androidSpecificAttributes"))
                if device.get("androidSpecificAttributes")
                else None
            ),
            "enabledDeveloperOptions": device.get("enabledDeveloperOptions"),
            "enabledUsbDebugging": device.get("enabledUsbDebugging"),
            "bootloaderVersion": device.get("bootloaderVersion"),
            "otherAccounts": device.get("otherAccounts"),
            # Additional identifiers
            "unifiedDeviceId": device.get("unifiedDeviceId"),
            "endpointVerificationSpecificAttributes": (
                json.dumps(device.get("endpointVerificationSpecificAttributes"))
                if device.get("endpointVerificationSpecificAttributes")
                else None
            ),
        }
        result.append(transformed)

    return result


def load_devices(
    neo4j_session: neo4j.Session,
    devices: list[dict[str, Any]],
    customer_id: str,
    update_tag: int,
) -> None:
    """
    Load device data into Neo4j.
    """
    logger.info("Loading %d Google Workspace devices", len(devices))
    load(
        neo4j_session,
        GoogleWorkspaceDeviceSchema(),
        devices,
        lastupdated=update_tag,
        CUSTOMER_ID=customer_id,
    )


def cleanup_devices(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Remove devices that weren't updated in this sync run.
    """
    logger.debug("Running Google Workspace devices cleanup job")
    GraphJob.from_node_schema(GoogleWorkspaceDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_googleworkspace_devices(
    neo4j_session: neo4j.Session,
    cloudidentity: Resource,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Google Workspace devices and device users.
    """
    logger.info("Starting Google Workspace devices sync")

    customer_id = common_job_parameters["CUSTOMER_ID"]

    # 1. GET - Fetch devices data
    raw_devices = get_devices(cloudidentity)
    raw_device_users = get_device_users(cloudidentity)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_devices = transform_devices(raw_devices, raw_device_users)

    # 3. LOAD - Ingest to Neo4j
    load_devices(neo4j_session, transformed_devices, customer_id, update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup_devices(neo4j_session, common_job_parameters)

    logger.info("Completed Google Workspace devices sync")
