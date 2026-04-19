import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.tailscale.grant import TailscaleGrantSchema
from cartography.models.tailscale.grant import TailscaleGroupToDeviceAccessMatchLink
from cartography.models.tailscale.grant import TailscaleUserToDeviceAccessMatchLink
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
) -> None:
    """
    Sync Tailscale Grants and resolve effective access relationships.

    This module:
    1. Loads TailscaleGrant nodes with their source/destination relationships
    2. Resolves effective access by computing which users/groups can access
       which devices based on grant rules and tag/group membership
    """
    logger.info("Starting Tailscale Grants sync")

    transformed_grants = transform(grants)
    load_grants(neo4j_session, transformed_grants, org, update_tag)

    user_access, group_access = resolve_access(
        grants,
        devices,
        groups,
        tags,
        users,
    )
    load_access(neo4j_session, org, update_tag, user_access, group_access)
    cleanup(neo4j_session, org, update_tag)

    logger.info(
        "Completed Tailscale Grants sync: %d grants, %d user access links, %d group access links",
        len(transformed_grants),
        len(user_access),
        len(group_access),
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


def resolve_access(
    grants: List[Dict[str, Any]],
    devices: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Resolve effective access from grants.

    For each grant, determine which users and groups can access which devices
    based on the grant's source/destination selectors and the current state
    of groups, tags, and devices.

    Returns:
        A tuple of (user_access, group_access) where each is a list of dicts
        suitable for load_matchlinks().
    """
    # Build lookup structures
    tag_to_devices = _build_tag_to_devices_map(devices)
    group_members = _build_group_members_map(groups)
    all_device_ids = {d["nodeId"] for d in devices}
    all_user_logins = {u["loginName"] for u in users}

    user_access: List[Dict[str, Any]] = []
    group_access: List[Dict[str, Any]] = []

    for grant in grants:
        grant_id = grant["id"]
        ip_rules = (
            json.dumps(grant["ip_rules"], sort_keys=True) if grant["ip_rules"] else None
        )

        # Resolve destination devices
        dest_device_ids = _resolve_destination_devices(
            grant,
            tag_to_devices,
            group_members,
            all_device_ids,
            devices,
        )

        if not dest_device_ids:
            continue

        # Resolve source users (direct user references in grant)
        for user_login in grant["source_users"]:
            if user_login not in all_user_logins:
                continue
            for device_id in dest_device_ids:
                user_access.append(
                    {
                        "user_login_name": user_login,
                        "device_id": device_id,
                        "grant_id": grant_id,
                        "ip_rules": ip_rules,
                    },
                )

        # Resolve source groups
        for group_id in grant["source_groups"]:
            # Create group-to-device access links
            for device_id in dest_device_ids:
                group_access.append(
                    {
                        "group_id": group_id,
                        "device_id": device_id,
                        "grant_id": grant_id,
                        "ip_rules": ip_rules,
                    },
                )

            # Also resolve individual user access through group membership
            members = group_members.get(group_id, set())
            for user_login in members:
                for device_id in dest_device_ids:
                    user_access.append(
                        {
                            "user_login_name": user_login,
                            "device_id": device_id,
                            "grant_id": grant_id,
                            "ip_rules": ip_rules,
                        },
                    )

    # Deduplicate: keep unique (user, device) pairs with the first grant seen
    user_access = _deduplicate_access(user_access, "user_login_name")
    group_access = _deduplicate_access(group_access, "group_id")

    logger.info(
        "Resolved %d user access links and %d group access links from %d grants",
        len(user_access),
        len(group_access),
        len(grants),
    )
    return user_access, group_access


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


def _resolve_destination_devices(
    grant: Dict[str, Any],
    tag_to_devices: Dict[str, List[str]],
    group_members: Dict[str, set[str]],
    all_device_ids: set[str],
    devices: List[Dict[str, Any]],
) -> set[str]:
    """Resolve which devices are targeted by a grant's destinations."""
    dest_device_ids: set[str] = set()

    for dst in grant["destinations"]:
        if dst == "*" or dst == "*:*":
            # Wildcard: all devices
            dest_device_ids.update(all_device_ids)
        elif dst.startswith("tag:"):
            # Tag selector: find devices with this tag
            tag_id = dst.split(":")[0] + ":" + dst.split(":")[1].rstrip(":*")
            devices_with_tag = tag_to_devices.get(tag_id, [])
            dest_device_ids.update(devices_with_tag)
        elif dst.startswith("group:") or dst.startswith("autogroup:"):
            # Group as destination: find devices owned by group members
            members = group_members.get(dst, set())
            for device in devices:
                if device.get("user") in members:
                    dest_device_ids.add(device["nodeId"])
        elif dst.startswith("autogroup:self"):
            # autogroup:self means the source's own devices - skip for now
            # as this requires per-user resolution
            pass

    return dest_device_ids


def _deduplicate_access(
    access_list: List[Dict[str, Any]],
    source_key: str,
) -> List[Dict[str, Any]]:
    """Deduplicate access entries, keeping the first occurrence per (source, device) pair."""
    seen: set[tuple[str, str]] = set()
    result: List[Dict[str, Any]] = []
    for entry in access_list:
        key = (entry[source_key], entry["device_id"])
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result
