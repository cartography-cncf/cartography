# Okta intel module - Devices
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError

from cartography.client.core.tx import run_write_query
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_okta_devices(api_client: ApiClient) -> List[Dict[str, Any]]:
    """
    Get devices from Okta server
    :param api_client: Okta api client
    :return: Array of device information
    """
    device_list: List[Dict[str, Any]] = []
    next_url: Optional[str] = None

    while True:
        # https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Device/#tag/Device/operation/listDevices
        try:
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    "limit": 200,  # Okta API max limit for devices
                    "expand": "user",  # Ensures user data is embedded in response
                }
                paged_response = api_client.get_path("/", params)

            # Parse JSON response
            response_data = json.loads(paged_response.text)
            device_list.extend(response_data)

            check_rate_limit(paged_response)

            if not is_last_page(paged_response):
                next_url = paged_response.links.get("next").get("url")
            else:
                break
        except OktaError as okta_error:
            logger.error(f"OktaError while listing devices: {okta_error}")
            raise

    return device_list


@timeit
def transform_okta_device_list(okta_device_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform okta device list to consumable format for graph
    :param okta_device_list: List of device dictionaries from API
    :return: List of transformed device dictionaries
    """
    devices: List[Dict[str, Any]] = []

    for device in okta_device_list:
        devices.append(transform_okta_device(device))

    return devices


def transform_okta_device(okta_device: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform okta device data
    :param okta_device: okta device dictionary from API
    :return: Dictionary containing device properties for ingestion
    """
    device_props: Dict[str, Any] = {}
    
    # Required fields
    device_props["id"] = okta_device["id"]
    
    # Status and basic info
    device_props["status"] = okta_device.get("status")
    device_props["created"] = okta_device.get("created")
    device_props["last_updated"] = okta_device.get("lastUpdated")
    
    # Profile information
    profile = okta_device.get("profile", {})
    device_props["display_name"] = profile.get("displayName")
    device_props["platform"] = profile.get("platform")
    device_props["manufacturer"] = profile.get("manufacturer")
    device_props["model"] = profile.get("model")
    device_props["serial_number"] = profile.get("serialNumber")
    device_props["os_version"] = profile.get("osVersion")
    device_props["user_agent"] = profile.get("userAgent")
    device_props["device_id"] = profile.get("deviceId")
    
    # User association - extract from _embedded or links
    # The device API may return user info in _embedded or we need to extract from relationships
    embedded = okta_device.get("_embedded", {})
    user_info = embedded.get("user", {})
    if user_info:
        user_id = user_info.get("id")
        device_props["user_id"] = user_id if user_id else None
    else:
        # Try to extract from _links if available
        links = okta_device.get("_links", {})
        user_link = links.get("user", {})
        if user_link:
            # Extract user ID from href if available
            href = user_link.get("href", "")
            # Parse user ID from href like /api/v1/users/00u1abc2def3ghi4jkl5
            if "/users/" in href:
                device_props["user_id"] = href.split("/users/")[-1].split("?")[0]
            else:
                device_props["user_id"] = None
        else:
            device_props["user_id"] = None

    return device_props


@timeit
def _load_okta_devices(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    device_list: List[Dict[str, Any]],
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
    MERGE (new_device:OktaDevice{id: device_data.id})
    ON CREATE SET new_device.firstseen = timestamp()
    SET new_device.status = device_data.status,
    new_device.created = device_data.created,
    new_device.last_updated = device_data.last_updated,
    new_device.display_name = device_data.display_name,
    new_device.platform = device_data.platform,
    new_device.manufacturer = device_data.manufacturer,
    new_device.model = device_data.model,
    new_device.serial_number = device_data.serial_number,
    new_device.os_version = device_data.os_version,
    new_device.user_agent = device_data.user_agent,
    new_device.device_id = device_data.device_id,
    new_device.lastupdated = $okta_update_tag
    WITH new_device, org, device_data
    MERGE (org)-[org_r:RESOURCE]->(new_device)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = $okta_update_tag
    WITH new_device, device_data
    WHERE device_data.user_id IS NOT NULL
    MATCH (user:OktaUser{id: device_data.user_id})
    MERGE (user)-[owns_r:OWNS]->(new_device)
    ON CREATE SET owns_r.firstseen = timestamp()
    SET owns_r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest_statement,
        ORG_ID=okta_org_id,
        DEVICE_LIST=device_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def sync_okta_devices(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
    sync_state: OktaSyncState,
) -> None:
    """
    Sync okta devices
    :param neo4j_session: Session with Neo4j server
    :param okta_org_id: Okta organization id to sync
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :param sync_state: Okta sync state
    :return: Nothing
    """
    logger.info("Syncing Okta devices")
    
    api_client = create_api_client(okta_org_id, "/api/v1/devices", okta_api_key)
    
    okta_device_data = _get_okta_devices(api_client)
    device_list = transform_okta_device_list(okta_device_data)
    
    _load_okta_devices(neo4j_session, okta_org_id, device_list, okta_update_tag)