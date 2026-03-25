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
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    model: PropertyRef = PropertyRef("model")
    platform: PropertyRef = PropertyRef("platform")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)


@dataclass(frozen=True)
class DeviceToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
class DeviceToCrowdstrikeHostBySerialRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:KandjiDevice) via serial_number
class DeviceToKandjiDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:SnipeitAsset) via serial
class DeviceToSnipeitAssetBySerialRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:TailscaleDevice) via serial_number
class DeviceToTailscaleDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"serial_number": PropertyRef("serial_number")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:GoogleWorkspaceDevice) via serial_number
class DeviceToGoogleWorkspaceDeviceBySerialRel(CartographyRelSchema):
    target_node_label: str = "GoogleWorkspaceDevice"
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
            DeviceToJumpCloudSystemRel(),
            # Serial number-based relationships
            DeviceToCrowdstrikeHostBySerialRel(),
            DeviceToKandjiDeviceBySerialRel(),
            DeviceToSnipeitAssetBySerialRel(),
            DeviceToTailscaleDeviceBySerialRel(),
            DeviceToGoogleWorkspaceDeviceBySerialRel(),
        ],
    )


# ---------------------------------------------------------------------------
# Hostname-based matchlinks
# These are fallback relationships that match devices by hostname.
# They are only executed when:
# - For modules with serial_number: serial_number links exist AND hostnames are unique
# - For modules without serial_number: hostnames are unique
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceHostnameMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("UPDATE_TAG", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id", set_in_kwargs=True,
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


# Configuration for hostname matchlinks used by the intel module.
# Each tuple: (target_label, target_hostname_field, matchlink_schema, has_serial_rel)
HOSTNAME_MATCHLINKS: list[tuple[str, str, CartographyRelSchema, bool]] = [
    ("CrowdstrikeHost", "hostname", DeviceToCrowdstrikeHostHostnameMatchLink(), True),
    ("KandjiDevice", "device_name", DeviceToKandjiDeviceHostnameMatchLink(), True),
    ("SnipeitAsset", "name", DeviceToSnipeitAssetHostnameMatchLink(), True),
    ("TailscaleDevice", "hostname", DeviceToTailscaleDeviceHostnameMatchLink(), True),
    ("GoogleWorkspaceDevice", "hostname", DeviceToGoogleWorkspaceDeviceHostnameMatchLink(), True),
    ("DuoEndpoint", "device_name", DeviceToDuoEndpointHostnameMatchLink(), False),
    ("DuoPhone", "name", DeviceToDuoPhoneHostnameMatchLink(), False),
    ("BigfixComputer", "computername", DeviceToBigfixComputerHostnameMatchLink(), False),
]
