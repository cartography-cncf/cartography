import json
import logging
from typing import Dict
from typing import List

import neo4j
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError

from cartography.client.core.tx import run_write_query
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _create_device_client(okta_org: str, okta_api_key: str) -> ApiClient:
    """
    Create Okta Device API client
    :param okta_org: Okta organization name
    :param okta_api_key: Okta API key
    :return: Instance of ApiClient for /api/v1/devices endpoint
    """
    return create_api_client(
        okta_org,
        "/api/v1/devices",
        okta_api_key,
    )


@timeit
def _get_okta_devices(api_client: ApiClient) -> List[Dict]:
    """
    Get Okta devices from Okta server with pagination
    Uses expand=userSummary to get device-user associations in a single call
    :param api_client: Okta API client
    :return: Array of device data
    """
    device_list: List[Dict] = []
    next_url = None

    while True:
        try:
            if next_url:
                response = api_client.get(next_url)
            else:
                # Use expand=userSummary to get user associations
                params = {"limit": 200, "expand": "userSummary"}
                response = api_client.get_path("/", params)
        except OktaError:
            logger.error("OktaError while listing devices")
            raise

        device_list.extend(json.loads(response.text))

        check_rate_limit(response)

        if not is_last_page(response):
            next_url = response.links.get("next").get("url")
        else:
            break

    return device_list


@timeit
def transform_okta_device(device_data: Dict) -> Dict:
    """
    Transform okta device data
    :param device_data: raw device data from Okta API
    :return: Dictionary containing device properties for ingestion
    """
    device_props = {}

    # Required fields
    device_props["id"] = device_data["id"]
    device_props["status"] = device_data.get("status")
    device_props["created"] = device_data.get("created")
    device_props["last_updated"] = device_data.get("lastUpdated")

    # Profile fields (all optional depending on platform)
    profile = device_data.get("profile", {})
    device_props["display_name"] = profile.get("displayName")
    device_props["platform"] = profile.get("platform")
    device_props["serial_number"] = profile.get("serialNumber")
    device_props["sid"] = profile.get("sid")
    device_props["manufacturer"] = profile.get("manufacturer")
    device_props["model"] = profile.get("model")
    device_props["os_version"] = profile.get("osVersion")
    device_props["registered"] = profile.get("registered")
    device_props["secure_hardware_present"] = profile.get("secureHardwarePresent")
    device_props["disk_encryption_type"] = profile.get("diskEncryptionType")
    device_props["imei"] = profile.get("imei")
    device_props["meid"] = profile.get("meid")
    device_props["udid"] = profile.get("udid")

    # Resource metadata
    device_props["resource_type"] = device_data.get("resourceType")
    resource_display_name = device_data.get("resourceDisplayName", {})
    if resource_display_name:
        device_props["resource_display_name"] = resource_display_name.get("value")
        device_props["resource_display_name_sensitive"] = resource_display_name.get(
            "sensitive"
        )
    else:
        device_props["resource_display_name"] = None
        device_props["resource_display_name_sensitive"] = None

    device_props["resource_alternate_id"] = device_data.get("resourceAlternateId")

    return device_props


@timeit
def transform_okta_device_users(device_data: Dict) -> List[Dict]:
    """
    Extract user-device relationships from device data
    :param device_data: raw device data from Okta API (with expand=userSummary)
    :return: List of user-device relationship data
    """
    relationships = []
    device_id = device_data["id"]
    embedded_users = device_data.get("_embedded", {}).get("users", [])

    for user_data in embedded_users:
        user_info = user_data.get("user", {})
        user_id = user_info.get("id")

        if user_id:
            relationships.append(
                {
                    "device_id": device_id,
                    "user_id": user_id,
                    "management_status": user_data.get("managementStatus"),
                    "screen_lock_type": user_data.get("screenLockType"),
                    "enrolled_at": user_data.get("created"),
                }
            )

    return relationships


@timeit
def _load_okta_devices(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    device_list: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Load Okta device information into the graph
    :param neo4j_session: session with neo4j server
    :param okta_org_id: okta organization id
    :param device_list: list of devices
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (org:OktaOrganization{id: $ORG_ID})
    WITH org
    UNWIND $DEVICE_LIST as device_data
    MERGE (device:OktaDevice{id: device_data.id})
    ON CREATE SET device.firstseen = timestamp()
    SET device.status = device_data.status,
    device.created = device_data.created,
    device.last_updated = device_data.last_updated,
    device.display_name = device_data.display_name,
    device.platform = device_data.platform,
    device.serial_number = device_data.serial_number,
    device.sid = device_data.sid,
    device.manufacturer = device_data.manufacturer,
    device.model = device_data.model,
    device.os_version = device_data.os_version,
    device.registered = device_data.registered,
    device.secure_hardware_present = device_data.secure_hardware_present,
    device.disk_encryption_type = device_data.disk_encryption_type,
    device.imei = device_data.imei,
    device.meid = device_data.meid,
    device.udid = device_data.udid,
    device.resource_type = device_data.resource_type,
    device.resource_display_name = device_data.resource_display_name,
    device.resource_display_name_sensitive = device_data.resource_display_name_sensitive,
    device.resource_alternate_id = device_data.resource_alternate_id,
    device.lastupdated = $okta_update_tag
    WITH device, org
    MERGE (org)-[r:RESOURCE]->(device)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest_statement,
        ORG_ID=okta_org_id,
        DEVICE_LIST=device_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_okta_device_users(
    neo4j_session: neo4j.Session,
    device_user_relationships: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Load user-device relationships into the graph
    :param neo4j_session: session with neo4j server
    :param device_user_relationships: list of user-device relationship data
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    UNWIND $RELATIONSHIPS as rel_data
    MATCH (user:OktaUser{id: rel_data.user_id})
    MATCH (device:OktaDevice{id: rel_data.device_id})
    MERGE (user)-[r:HAS_DEVICE]->(device)
    ON CREATE SET r.firstseen = timestamp()
    SET r.management_status = rel_data.management_status,
    r.screen_lock_type = rel_data.screen_lock_type,
    r.enrolled_at = rel_data.enrolled_at,
    r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest_statement,
        RELATIONSHIPS=device_user_relationships,
        okta_update_tag=okta_update_tag,
    )


@timeit
def sync_okta_devices(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
) -> None:
    """
    Sync Okta devices and device-user relationships
    Requires okta.devices.read scope
    :param neo4j_session: Session with Neo4j server
    :param okta_org_id: Okta organization id to sync
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :return: Nothing
    """
    logger.info("Syncing Okta Devices")

    # Fetch devices with user associations (expand=userSummary)
    device_client = _create_device_client(okta_org_id, okta_api_key)
    raw_devices = _get_okta_devices(device_client)

    # Transform and load devices
    device_list = [transform_okta_device(d) for d in raw_devices]
    _load_okta_devices(neo4j_session, okta_org_id, device_list, okta_update_tag)

    # Extract and load user-device relationships
    all_relationships = []
    for device_data in raw_devices:
        relationships = transform_okta_device_users(device_data)
        all_relationships.extend(relationships)

    if all_relationships:
        _load_okta_device_users(neo4j_session, all_relationships, okta_update_tag)
        logger.info(f"Synced {len(all_relationships)} device-user relationships")

    logger.info(f"Synced {len(device_list)} Okta devices")
