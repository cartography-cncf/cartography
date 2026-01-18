from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("hostname")
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


# (:Device)-[:OBSERVED_AS]->(:DuoEndpoint)
class DeviceToDuoEndpointRel(CartographyRelSchema):
    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:DuoPhone)
class DeviceToDuoPhoneRel(CartographyRelSchema):
    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:KandjiDevice)
class DeviceToKandjiDeviceRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:SnipeitAsset)
class DeviceToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:TailscaleDevice)
class DeviceToTailscaleDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:CrowdstrikeHost)
class DeviceToCrowdstrikeHostRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:BigfixComputer)
class DeviceToBigfixComputerRel(CartographyRelSchema):
    target_node_label: str = "BigfixComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computername": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:OBSERVED_AS]->(:GoogleWorkspaceDevice)
class DeviceToGoogleWorkspaceDeviceRel(CartographyRelSchema):
    target_node_label: str = "GoogleWorkspaceDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
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
            DeviceToDuoEndpointRel(),
            DeviceToDuoPhoneRel(),
            DeviceToKandjiDeviceRel(),
            DeviceToSnipeitAssetRel(),
            DeviceToTailscaleDeviceRel(),
            DeviceToCrowdstrikeHostRel(),
            DeviceToBigfixComputerRel(),
            DeviceToGoogleWorkspaceDeviceRel(),
        ],
    )
