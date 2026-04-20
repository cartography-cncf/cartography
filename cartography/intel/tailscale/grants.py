import ipaddress
import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.tailscale.grant import TailscaleDeviceToDeviceAccessMatchLink
from cartography.models.tailscale.grant import TailscaleGrantSchema
from cartography.models.tailscale.grant import TailscaleGroupToDeviceAccessMatchLink
from cartography.models.tailscale.grant import TailscaleGroupToServiceAccessMatchLink
from cartography.models.tailscale.grant import TailscaleUserToDeviceAccessMatchLink
from cartography.models.tailscale.grant import TailscaleUserToServiceAccessMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

MATCHLINK_SUB_RESOURCE_LABEL = "TailscaleTailnet"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
    grants: List[Dict[str, Any]],
    devices: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
    services: List[Dict[str, Any]] | None = None,
    posture_matches: List[Dict[str, str]] | None = None,
) -> None:
    """
    Sync Tailscale Grants and resolve effective access relationships.

    This module:
    1. Loads TailscaleGrant nodes with their source/destination relationships
    2. Resolves effective access by computing which users/groups/devices can access
       which devices and services based on grant rules, tag/group membership,
       and posture compliance
    """
    logger.info("Starting Tailscale Grants sync")

    transformed_grants = transform(grants)
    load_grants(neo4j_session, transformed_grants, org, update_tag)

    user_access, group_access, device_access, user_svc_access, group_svc_access = (
        resolve_access(
            grants,
            devices,
            groups,
            tags,
            users,
            services or [],
            posture_matches or [],
        )
    )
    load_access(
        neo4j_session,
        org,
        update_tag,
        user_access,
        group_access,
        device_access,
        user_svc_access,
        group_svc_access,
    )
    cleanup(neo4j_session, org, update_tag)

    logger.info(
        "Completed Tailscale Grants sync: %d grants, "
        "%d user→device, %d group→device, %d device→device, "
        "%d user→service, %d group→service",
        len(transformed_grants),
        len(user_access),
        len(group_access),
        len(device_access),
        len(user_svc_access),
        len(group_svc_access),
    )


def transform(grants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform grants for loading into Neo4j.

    Serializes list/dict fields to JSON strings for storage as node properties.
    """
    transformed: List[Dict[str, Any]] = []
    for grant in grants:
        transformed.append(
            {
                "id": grant["id"],
                "sources": json.dumps(grant["sources"], sort_keys=True),
                "destinations": json.dumps(grant["destinations"], sort_keys=True),
                "source_groups": grant["source_groups"],
                "source_users": grant["source_users"],
                "destination_tags": grant["destination_tags"],
                "destination_groups": grant["destination_groups"],
                "ip_rules": (
                    json.dumps(grant["ip_rules"], sort_keys=True)
                    if grant["ip_rules"]
                    else None
                ),
                "app_capabilities": (
                    json.dumps(
                        grant["app_capabilities"],
                        sort_keys=True,
                    )
                    if grant["app_capabilities"]
                    else None
                ),
                "src_posture": (
                    json.dumps(grant["src_posture"], sort_keys=True)
                    if grant["src_posture"]
                    else None
                ),
            },
        )
    return transformed


@timeit
def load_grants(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Tailscale Grants to the graph", len(data))
    load(
        neo4j_session,
        TailscaleGrantSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def load_access(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
    user_access: List[Dict[str, Any]],
    group_access: List[Dict[str, Any]],
    device_access: List[Dict[str, Any]],
    user_svc_access: List[Dict[str, Any]] | None = None,
    group_svc_access: List[Dict[str, Any]] | None = None,
) -> None:
    if user_access:
        load_matchlinks(
            neo4j_session,
            TailscaleUserToDeviceAccessMatchLink(),
            user_access,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )
    if group_access:
        load_matchlinks(
            neo4j_session,
            TailscaleGroupToDeviceAccessMatchLink(),
            group_access,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )
    if device_access:
        load_matchlinks(
            neo4j_session,
            TailscaleDeviceToDeviceAccessMatchLink(),
            device_access,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )
    if user_svc_access:
        load_matchlinks(
            neo4j_session,
            TailscaleUserToServiceAccessMatchLink(),
            user_svc_access,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )
    if group_svc_access:
        load_matchlinks(
            neo4j_session,
            TailscaleGroupToServiceAccessMatchLink(),
            group_svc_access,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "org": org,
    }
    GraphJob.from_node_schema(TailscaleGrantSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        TailscaleUserToDeviceAccessMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        TailscaleGroupToDeviceAccessMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        TailscaleDeviceToDeviceAccessMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        TailscaleUserToServiceAccessMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        TailscaleGroupToServiceAccessMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)


def resolve_access(
    grants: List[Dict[str, Any]],
    devices: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
    services: List[Dict[str, Any]] | None = None,
    posture_matches: List[Dict[str, str]] | None = None,
) -> tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    """Resolve effective access from grants.

    For each grant, determine which users, groups, and devices can access which
    devices and services based on the grant's source/destination selectors and
    the current state of groups, tags, devices, and services.

    Handles:
    - Direct user sources (email in src)
    - Group/autogroup sources (direct members only; transitive membership is
      resolved via INHERITED_MEMBER_OF in the graph by acls.py)
    - Tag sources (device-to-device access)
    - autogroup:self destinations (user's own devices)
    - svc:xxx destinations (Tailscale Services)
    - IP/CIDR destinations (matched against device addresses)
    - srcPosture filtering (only sources with compliant devices get access)

    Returns:
        A tuple of (user_access, group_access, device_access,
        user_svc_access, group_svc_access) where each is a list of dicts
        suitable for load_matchlinks().
    """
    # Build lookup structures
    tag_to_devices = _build_tag_to_devices_map(devices)
    group_members = _build_group_members_map(groups)
    all_device_ids = {d["nodeId"] for d in devices}
    all_user_logins = {u["loginName"] for u in users}
    user_to_devices = _build_user_to_devices_map(devices)
    ip_to_devices = _build_ip_to_devices_map(devices)
    service_ids = {f"svc:{s.get('name', '')}" for s in (services or [])}
    device_postures = _build_device_postures_map(posture_matches or [])
    user_postures = _build_user_postures_map(user_to_devices, device_postures)

    user_access: Dict[tuple[str, str], List[str]] = {}
    group_access: Dict[tuple[str, str], List[str]] = {}
    device_access: Dict[tuple[str, str], List[str]] = {}
    user_svc_access: Dict[tuple[str, str], List[str]] = {}
    group_svc_access: Dict[tuple[str, str], List[str]] = {}

    for grant in grants:
        grant_id = grant["id"]
        required_postures = set(grant.get("src_posture", []))

        has_self_destination = _has_autogroup_self(grant["destinations"])

        # Resolve destination devices (excluding autogroup:self and svc:)
        dest_device_ids = _resolve_destination_devices(
            grant,
            tag_to_devices,
            group_members,
            all_device_ids,
            devices,
            ip_to_devices,
        )

        # Resolve destination services
        dest_service_ids = _resolve_destination_services(
            grant["destinations"],
            service_ids,
        )

        # --- Source: direct users ---
        for user_login in grant["source_users"]:
            if user_login not in all_user_logins:
                continue
            if not _user_meets_posture(
                user_login,
                required_postures,
                user_postures,
            ):
                continue
            for device_id in dest_device_ids:
                _add_access(user_access, (user_login, device_id), grant_id)
            if has_self_destination:
                for device_id in user_to_devices.get(user_login, []):
                    _add_access(user_access, (user_login, device_id), grant_id)
            for svc_id in dest_service_ids:
                _add_access(user_svc_access, (user_login, svc_id), grant_id)

        # --- Source: groups/autogroups ---
        for group_id in grant["source_groups"]:
            for device_id in dest_device_ids:
                _add_access(group_access, (group_id, device_id), grant_id)
            for svc_id in dest_service_ids:
                _add_access(group_svc_access, (group_id, svc_id), grant_id)

            members = group_members.get(group_id, set())
            for user_login in members:
                if not _user_meets_posture(
                    user_login,
                    required_postures,
                    user_postures,
                ):
                    continue
                for device_id in dest_device_ids:
                    _add_access(user_access, (user_login, device_id), grant_id)
                if has_self_destination:
                    for device_id in user_to_devices.get(user_login, []):
                        _add_access(user_access, (user_login, device_id), grant_id)
                for svc_id in dest_service_ids:
                    _add_access(user_svc_access, (user_login, svc_id), grant_id)

        # --- Source: tags (device-to-device access) ---
        for source_tag in grant["source_tags"]:
            source_device_ids = tag_to_devices.get(source_tag, [])
            for source_device_id in source_device_ids:
                if not _device_meets_posture(
                    source_device_id,
                    required_postures,
                    device_postures,
                ):
                    continue
                for device_id in dest_device_ids:
                    if source_device_id == device_id:
                        continue
                    _add_access(
                        device_access,
                        (source_device_id, device_id),
                        grant_id,
                    )

    # Propagate user access to device-to-device access:
    # If a user CAN_ACCESS a device, then all the user's devices
    # CAN_ACCESS that device too (for exhaustive device→device queries).
    for (user_login, dest_device_id), grant_ids in user_access.items():
        for source_device_id in user_to_devices.get(user_login, []):
            if source_device_id == dest_device_id:
                continue
            for grant_id in grant_ids:
                _add_access(
                    device_access,
                    (source_device_id, dest_device_id),
                    grant_id,
                )

    # Convert aggregated dicts to lists for load_matchlinks
    user_access_list = [
        {"user_login_name": k[0], "device_id": k[1], "granted_by": v}
        for k, v in user_access.items()
    ]
    group_access_list = [
        {"group_id": k[0], "device_id": k[1], "granted_by": v}
        for k, v in group_access.items()
    ]
    device_access_list = [
        {"source_device_id": k[0], "device_id": k[1], "granted_by": v}
        for k, v in device_access.items()
    ]
    user_svc_access_list = [
        {"user_login_name": k[0], "service_id": k[1], "granted_by": v}
        for k, v in user_svc_access.items()
    ]
    group_svc_access_list = [
        {"group_id": k[0], "service_id": k[1], "granted_by": v}
        for k, v in group_svc_access.items()
    ]

    logger.info(
        "Resolved %d user→device, %d group→device, %d device→device, "
        "%d user→service, %d group→service from %d grants",
        len(user_access_list),
        len(group_access_list),
        len(device_access_list),
        len(user_svc_access_list),
        len(group_svc_access_list),
        len(grants),
    )
    return (
        user_access_list,
        group_access_list,
        device_access_list,
        user_svc_access_list,
        group_svc_access_list,
    )


def _build_tag_to_devices_map(
    devices: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Build a mapping from tag ID to list of device IDs."""
    tag_to_devices: Dict[str, List[str]] = {}
    for device in devices:
        for tag in device.get("tags", []):
            tag_to_devices.setdefault(tag, []).append(device["nodeId"])
    return tag_to_devices


def _build_group_members_map(
    groups: List[Dict[str, Any]],
) -> Dict[str, set[str]]:
    """Build a mapping from group ID to set of member login names."""
    group_members: Dict[str, set[str]] = {}
    for group in groups:
        group_members[group["id"]] = set(group.get("members", []))
    return group_members


def _build_user_to_devices_map(
    devices: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Build a mapping from user login name to list of their device IDs."""
    user_to_devices: Dict[str, List[str]] = {}
    for device in devices:
        user = device.get("user")
        if user:
            user_to_devices.setdefault(user, []).append(device["nodeId"])
    return user_to_devices


def _build_ip_to_devices_map(
    devices: List[Dict[str, Any]],
) -> Dict[str, str]:
    """Build a mapping from IP address string to device ID.

    Each device can have multiple addresses (IPv4 + IPv6).
    """
    ip_to_device: Dict[str, str] = {}
    for device in devices:
        for addr in device.get("addresses", []):
            ip_to_device[addr] = device["nodeId"]
    return ip_to_device


def _build_device_postures_map(
    posture_matches: List[Dict[str, str]],
) -> Dict[str, set[str]]:
    """Build a mapping from device ID to set of posture IDs it conforms to."""
    device_postures: Dict[str, set[str]] = {}
    for match in posture_matches:
        device_postures.setdefault(match["device_id"], set()).add(
            match["posture_id"],
        )
    return device_postures


def _build_user_postures_map(
    user_to_devices: Dict[str, List[str]],
    device_postures: Dict[str, set[str]],
) -> Dict[str, set[str]]:
    """Build a mapping from user login to the union of postures across all their devices.

    A user meets a posture requirement if at least one of their devices
    conforms to all required postures.
    """
    user_postures: Dict[str, set[str]] = {}
    for user_login, device_ids in user_to_devices.items():
        all_postures: set[str] = set()
        for device_id in device_ids:
            all_postures.update(device_postures.get(device_id, set()))
        user_postures[user_login] = all_postures
    return user_postures


def _user_meets_posture(
    user_login: str,
    required_postures: set[str],
    user_postures: Dict[str, set[str]],
) -> bool:
    """Check if a user meets posture requirements.

    Returns True if no posture is required, or if the user has at least
    one device conforming to all required postures.
    """
    if not required_postures:
        return True
    return required_postures.issubset(user_postures.get(user_login, set()))


def _device_meets_posture(
    device_id: str,
    required_postures: set[str],
    device_postures: Dict[str, set[str]],
) -> bool:
    """Check if a device meets posture requirements.

    Returns True if no posture is required, or if the device conforms
    to all required postures.
    """
    if not required_postures:
        return True
    return required_postures.issubset(device_postures.get(device_id, set()))


def _has_autogroup_self(destinations: List[str]) -> bool:
    """Check if any destination is autogroup:self."""
    for dst in destinations:
        if dst == "autogroup:self" or dst.startswith("autogroup:self:"):
            return True
    return False


def _resolve_destination_devices(
    grant: Dict[str, Any],
    tag_to_devices: Dict[str, List[str]],
    group_members: Dict[str, set[str]],
    all_device_ids: set[str],
    devices: List[Dict[str, Any]],
    ip_to_devices: Dict[str, str] | None = None,
) -> set[str]:
    """Resolve which devices are targeted by a grant's destinations.

    Note: autogroup:self is handled separately per-source in resolve_access().
    Note: svc:xxx is handled by _resolve_destination_services().
    """
    dest_device_ids: set[str] = set()

    for dst in grant["destinations"]:
        if dst == "*" or dst == "*:*":
            # Wildcard: all devices
            dest_device_ids.update(all_device_ids)
        elif dst == "autogroup:self" or dst.startswith("autogroup:self:"):
            # Handled per-source in resolve_access()
            pass
        elif dst.startswith("svc:"):
            # Handled by _resolve_destination_services()
            pass
        elif dst.startswith("tag:"):
            # Tag selector: find devices with this tag
            # Handle "tag:web:443" format by stripping port suffix
            parts = dst.split(":")
            tag_id = parts[0] + ":" + parts[1]
            devices_with_tag = tag_to_devices.get(tag_id, [])
            dest_device_ids.update(devices_with_tag)
        elif dst.startswith("group:") or dst.startswith("autogroup:"):
            # Group as destination: find devices owned by group members
            members = group_members.get(dst, set())
            for device in devices:
                if device.get("user") in members:
                    dest_device_ids.add(device["nodeId"])
        else:
            # Try to resolve as IP address or CIDR range
            matched = _resolve_ip_destination(dst, ip_to_devices or {})
            dest_device_ids.update(matched)

    return dest_device_ids


def _resolve_ip_destination(
    dst: str,
    ip_to_devices: Dict[str, str],
) -> set[str]:
    """Resolve an IP address or CIDR range to device IDs.

    Supports:
    - Exact IP: "100.64.0.1" -> device with that address
    - CIDR range: "100.64.0.0/24" -> all devices with addresses in that range
    """
    matched: set[str] = set()

    try:
        network = ipaddress.ip_network(dst, strict=False)
    except ValueError:
        # Not a valid IP or CIDR — ignore
        return matched

    if network.num_addresses == 1:
        # Single IP (e.g., "100.64.0.1" or "100.64.0.1/32")
        device_id = ip_to_devices.get(str(network.network_address))
        if device_id:
            matched.add(device_id)
    else:
        # CIDR range — check all device IPs against the network
        for ip_str, device_id in ip_to_devices.items():
            try:
                if ipaddress.ip_address(ip_str) in network:
                    matched.add(device_id)
            except ValueError:
                continue

    return matched


def _resolve_destination_services(
    destinations: List[str],
    service_ids: set[str],
) -> set[str]:
    """Resolve which services are targeted by a grant's destinations."""
    dest_services: set[str] = set()
    for dst in destinations:
        if dst.startswith("svc:") and dst in service_ids:
            dest_services.add(dst)
    return dest_services


def _add_access(
    access_map: Dict[tuple[str, str], List[str]],
    key: tuple[str, str],
    grant_id: str,
) -> None:
    """Add a grant_id to the access map, aggregating multiple grants per pair."""
    if key not in access_map:
        access_map[key] = [grant_id]
    elif grant_id not in access_map[key]:
        access_map[key].append(grant_id)
