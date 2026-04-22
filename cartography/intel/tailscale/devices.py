import logging
from ast import literal_eval
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.tailscale.device import TailscaleDeviceSchema
from cartography.models.tailscale.tag import TailscaleTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Device posture attribute projection allowlist.
# Sources:
# - https://tailscale.com/docs/integrations/crowdstrike-zta
# - https://tailscale.com/docs/integrations/sentinelone
# - https://tailscale.com/docs/integrations/kolide
# - https://tailscale.com/docs/integrations/fleet
# - https://tailscale.com/docs/integrations/huntress
# - https://tailscale.com/docs/integrations/iru
# - https://tailscale.com/docs/integrations/jamf-pro
# - https://tailscale.com/docs/integrations/mdm/intune
_POSTURE_ATTRIBUTE_FIELD_MAP = {
    "node:os": "posture_node_os",
    "node:osVersion": "posture_node_os_version",
    "node:tsAutoUpdate": "posture_node_ts_auto_update",
    "node:tsReleaseTrack": "posture_node_ts_release_track",
    "node:tsStateEncrypted": "posture_node_ts_state_encrypted",
    "node:tsVersion": "posture_node_ts_version",
    "ip:country": "posture_ip_country",
    "falcon:ztaScore": "posture_falcon_zta_score",
    "sentinelOne:operationalState": "posture_sentinelone_operational_state",
    "sentinelOne:activeThreats": "posture_sentinelone_active_threats",
    "sentinelOne:agentVersion": "posture_sentinelone_agent_version",
    "sentinelOne:encryptedApplications": "posture_sentinelone_encrypted_applications",
    "sentinelOne:firewallEnabled": "posture_sentinelone_firewall_enabled",
    "sentinelOne:infected": "posture_sentinelone_infected",
    "kolide:authState": "posture_kolide_auth_state",
    "fleet:present": "posture_fleet_present",
    "huntress:defenderStatus": "posture_huntress_defender_status",
    "huntress:defenderPolicyStatus": "posture_huntress_defender_policy_status",
    "huntress:firewallStatus": "posture_huntress_firewall_status",
    "kandji:mdmEnabled": "posture_kandji_mdm_enabled",
    "kandji:agentInstalled": "posture_kandji_agent_installed",
    "jamfPro:remoteManaged": "posture_jamfpro_remote_managed",
    "jamfPro:supervised": "posture_jamfpro_supervised",
    "jamfPro:firewallEnabled": "posture_jamfpro_firewall_enabled",
    "jamfPro:fileVaultStatus": "posture_jamfpro_file_vault_status",
    "jamfPro:SIPEnabled": "posture_jamfpro_sip_enabled",
    "intune:complianceState": "posture_intune_compliance_state",
    "intune:azureADRegistered": "posture_intune_azure_ad_registered",
    "intune:deviceRegistrationState": "posture_intune_device_registration_state",
    "intune:isSupervised": "posture_intune_is_supervised",
    "intune:isEncrypted": "posture_intune_is_encrypted",
    "intune:managedDeviceOwnerType": "posture_intune_managed_device_owner_type",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    org: str,
) -> tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    devices = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org,
    )
    tags = transform(devices)
    device_posture_attributes = get_device_posture_attributes(
        api_session,
        common_job_parameters["BASE_URL"],
        devices,
    )
    project_device_posture_attributes(
        devices,
        device_posture_attributes,
    )
    load_devices(
        neo4j_session,
        devices,
        org,
        common_job_parameters["UPDATE_TAG"],
    )
    load_tags(
        neo4j_session,
        tags,
        org,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return devices, device_posture_attributes


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    req = api_session.get(
        f"{base_url}/tailnet/{org}/devices",
        timeout=_TIMEOUT,
        params={"fields": "all"},
    )
    req.raise_for_status()
    results = req.json()["devices"]
    return results


def transform(
    raw_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extracts tags from the raw data and returns a list of dictionaries"""
    transformed_tags: dict[str, dict[str, Any]] = {}
    # Transform the raw data into the format expected by the load function
    for device in raw_data:
        # Extract the first serial number from postureIdentity if available
        serial_numbers = (device.get("postureIdentity") or {}).get("serialNumbers", [])
        device["serial_number"] = serial_numbers[0] if serial_numbers else None

        for raw_tag in device.get("tags", []):
            if raw_tag not in transformed_tags:
                transformed_tags[raw_tag] = {
                    "id": raw_tag,
                    "name": raw_tag.split(":")[-1],
                    "devices": [device["nodeId"]],
                }
            else:
                transformed_tags[raw_tag]["devices"].append(device["nodeId"])
    return list(transformed_tags.values())


@timeit
def get_device_posture_attributes(
    api_session: requests.Session,
    base_url: str,
    devices: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch device posture attributes from the per-device endpoint.

    The endpoint is N+1 by design, so we keep the result in-memory for the
    posture resolution stage instead of persisting each attribute as its own node.
    """
    results: dict[str, dict[str, Any]] = {}

    for device in devices:
        device_id = device.get("nodeId")
        if not device_id:
            logger.warning("Device missing nodeId, skipping posture attribute fetch")
            continue

        attributes = _build_builtin_device_attributes(device)

        try:
            req = api_session.get(
                f"{base_url}/device/{device_id}/attributes",
                timeout=_TIMEOUT,
            )
            req.raise_for_status()
            payload = req.json()
            for attribute_name, attribute_data in payload.get("attributes", {}).items():
                raw_value = attribute_data
                if isinstance(attribute_data, dict):
                    raw_value = attribute_data.get("value")
                normalized_value = _normalize_attribute_value(
                    raw_value,
                )
                attributes[attribute_name] = normalized_value
        except requests.exceptions.RequestException:
            logger.exception(
                "Failed to fetch posture attributes for Tailscale device %s",
                device_id,
            )
            raise

        results[device_id] = attributes

    return results


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TailscaleDeviceSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def load_tags(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TailscaleTagSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(TailscaleDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TailscaleTagSchema(), common_job_parameters).run(
        neo4j_session
    )


def project_device_posture_attributes(
    devices: List[Dict[str, Any]],
    device_posture_attributes: Dict[str, Dict[str, Any]],
) -> None:
    for device in devices:
        projected_attrs: dict[str, Any] = {
            field_name: None for field_name in _POSTURE_ATTRIBUTE_FIELD_MAP.values()
        }
        projected_attrs["posture_fleet_policies"] = []

        attributes = device_posture_attributes.get(device["nodeId"], {})
        for attribute_name, attribute_value in attributes.items():
            if attribute_name.startswith("fleetPolicy:"):
                projected_attrs["posture_fleet_policies"].append(attribute_name)
                continue

            field_name = _POSTURE_ATTRIBUTE_FIELD_MAP.get(attribute_name)
            if field_name:
                projected_attrs[field_name] = attribute_value

        if not projected_attrs["posture_fleet_policies"]:
            projected_attrs["posture_fleet_policies"] = None

        device.update(projected_attrs)


def _build_builtin_device_attributes(device: Dict[str, Any]) -> Dict[str, Any]:
    attributes: dict[str, Any] = {}

    if device.get("os") is not None:
        attributes["node:os"] = device["os"]

    if device.get("clientVersion") is not None:
        attributes["node:tsVersion"] = str(device["clientVersion"]).lstrip("v")

    return attributes


def _normalize_attribute_value(value: Any) -> Any:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.lower() == "true":
            return True
        if normalized.lower() == "false":
            return False
        if normalized.lower() == "null":
            return None
        try:
            return literal_eval(normalized)
        except (ValueError, SyntaxError):
            return normalized
    return value
