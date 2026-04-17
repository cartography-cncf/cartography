from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("serial_number")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    instance_id: PropertyRef = PropertyRef("instance_id")
    manufacturer: PropertyRef = PropertyRef("manufacturer")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    model: PropertyRef = PropertyRef("model")
    platform: PropertyRef = PropertyRef("platform")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)


@dataclass(frozen=True)
class DeviceToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Cleanup-only relationship.
# This relation is created by custom ontology linking queries, not by load(DeviceSchema()).
# We keep it on the schema so GraphJob cleanup knows to remove stale edges.
# The PropertyRef intentionally points to a field that does not exist in device load payloads,
# so standard ingestion will never materialize this relationship.
# (:User)-[:OWNS]->(:Device)
@dataclass(frozen=True)
class DeviceOwnedByUserRel(CartographyRelSchema):
    target_node_label: str = "User"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_cleanup_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:JumpCloudSystem)
@dataclass(frozen=True)
class DeviceToJumpCloudSystemRel(CartographyRelSchema):
    target_node_label: str = "JumpCloudSystem"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# Serial number-based OBSERVED_AS relationships
# These match devices by serial_number, which is the primary matching strategy.


# (:Device)-[:OBSERVED_AS]->(:CrowdstrikeHost) via serial_number
@dataclass(frozen=True)
class DeviceToCrowdstrikeHostBySerialRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:KandjiDevice) via serial_number
@dataclass(frozen=True)
class DeviceToKandjiDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:SnipeitAsset) via serial
@dataclass(frozen=True)
class DeviceToSnipeitAssetBySerialRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:TailscaleDevice) via serial_number
@dataclass(frozen=True)
class DeviceToTailscaleDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:GoogleWorkspaceDevice) via serial_number
@dataclass(frozen=True)
class DeviceToGoogleWorkspaceDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "GoogleWorkspaceDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:S1Agent) via serial_number
@dataclass(frozen=True)
class DeviceToS1AgentBySerialRel(CartographyRelSchema):
    target_node_label: str = "S1Agent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:IntuneManagedDevice) via serial_number
@dataclass(frozen=True)
class DeviceToIntuneManagedDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


@dataclass(frozen=True)
class DeviceToJamfComputerBySerialRel(CartographyRelSchema):
    target_node_label: str = "JamfComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


@dataclass(frozen=True)
class DeviceToJamfMobileDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "JamfMobileDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


@dataclass(frozen=True)
class DeviceSchema(CartographyNodeSchema):
    label: str = "Device"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: DeviceNodeProperties = DeviceNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DeviceOwnedByUserRel(),
            DeviceToJumpCloudSystemRel(),
            # Serial number-based relationships
            DeviceToCrowdstrikeHostBySerialRel(),
            DeviceToKandjiDeviceBySerialRel(),
            DeviceToSnipeitAssetBySerialRel(),
            DeviceToTailscaleDeviceBySerialRel(),
            DeviceToGoogleWorkspaceDeviceBySerialRel(),
            DeviceToS1AgentBySerialRel(),
            DeviceToIntuneManagedDeviceBySerialRel(),
            DeviceToJamfComputerBySerialRel(),
            DeviceToJamfMobileDeviceBySerialRel(),
        ],
    )


# ---------------------------------------------------------------------------
# Hostname-based matchlinks
# These are fallback relationships that match devices by hostname when both
# sides have unique hostnames. They can also supplement serial-number matches
# for providers that support both strategies.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceHostnameMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("UPDATE_TAG", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


# (:Device)-[:OBSERVED_AS]->(:DuoEndpoint) via hostname
@dataclass(frozen=True)
class DeviceToDuoEndpointHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:DuoPhone) via hostname
@dataclass(frozen=True)
class DeviceToDuoPhoneHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:KandjiDevice) via hostname
@dataclass(frozen=True)
class DeviceToKandjiDeviceHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:SnipeitAsset) via hostname
@dataclass(frozen=True)
class DeviceToSnipeitAssetHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:TailscaleDevice) via hostname
@dataclass(frozen=True)
class DeviceToTailscaleDeviceHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:CrowdstrikeHost) via hostname
@dataclass(frozen=True)
class DeviceToCrowdstrikeHostHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:BigfixComputer) via hostname
@dataclass(frozen=True)
class DeviceToBigfixComputerHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "BigfixComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computername": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:GoogleWorkspaceDevice) via hostname
@dataclass(frozen=True)
class DeviceToGoogleWorkspaceDeviceHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "GoogleWorkspaceDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:S1Agent) via hostname
@dataclass(frozen=True)
class DeviceToS1AgentHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "S1Agent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computer_name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# (:Device)-[:OBSERVED_AS]->(:IntuneManagedDevice) via hostname
@dataclass(frozen=True)
class DeviceToIntuneManagedDeviceHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


@dataclass(frozen=True)
class DeviceToJamfComputerHostnameMatchLink(CartographyRelSchema):
    target_node_label: str = "JamfComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    source_node_label: str = "Device"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceHostnameMatchLinkProperties = DeviceHostnameMatchLinkProperties()


# Configuration for hostname matchlinks used by the intel module.
# Each tuple: (target_label, target_hostname_field, matchlink_schema)
HOSTNAME_MATCHLINKS: list[tuple[str, str, CartographyRelSchema]] = [
    ("CrowdstrikeHost", "hostname", DeviceToCrowdstrikeHostHostnameMatchLink()),
    ("KandjiDevice", "device_name", DeviceToKandjiDeviceHostnameMatchLink()),
    ("SnipeitAsset", "name", DeviceToSnipeitAssetHostnameMatchLink()),
    ("TailscaleDevice", "hostname", DeviceToTailscaleDeviceHostnameMatchLink()),
    (
        "GoogleWorkspaceDevice",
        "hostname",
        DeviceToGoogleWorkspaceDeviceHostnameMatchLink(),
    ),
    ("S1Agent", "computer_name", DeviceToS1AgentHostnameMatchLink()),
    ("DuoEndpoint", "device_name", DeviceToDuoEndpointHostnameMatchLink()),
    ("DuoPhone", "name", DeviceToDuoPhoneHostnameMatchLink()),
    (
        "BigfixComputer",
        "computername",
        DeviceToBigfixComputerHostnameMatchLink(),
    ),
    (
        "IntuneManagedDevice",
        "device_name",
        DeviceToIntuneManagedDeviceHostnameMatchLink(),
    ),
    ("JamfComputer", "name", DeviceToJamfComputerHostnameMatchLink()),
]
