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


# (:Device)-[:HAS_OBSERVATION]->(:DuoEndpoint)
class DeviceToDuoEndpointRel(CartographyRelSchema):
    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:HAS_OBSERVATION]->(:DuoPhone)
class DeviceToDuoPhoneRel(CartographyRelSchema):
    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:HAS_OBSERVATION]->(:KandjiDevice)
class DeviceToKandjiDeviceRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:HAS_OBSERVATION]->(:SnipeitAsset)
class DeviceToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:HAS_OBSERVATION]->(:TailscaleDevice)
class DeviceToTailscaleDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:HAS_OBSERVATION]->(:CrowdstrikeHost)
class DeviceToCrowdstrikeHostRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: DeviceToNodeRelProperties = DeviceToNodeRelProperties()


# (:Device)-[:RESOURCE]->(:BigfixComputer)
class DeviceToBigfixComputerRel(CartographyRelSchema):
    target_node_label: str = "BigfixComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computername": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
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
        ],
    )
